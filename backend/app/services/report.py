"""Stage 4 — write the cited answer, and make its citations impossible to fake.

The division of labour is the important part:

* The model writes the **body only**. It is never asked for URLs, titles, or a reference
  list, so there is nothing in its output a reader could mistake for a verified source.
* The **reference list is assembled by this module from the stored `Source` rows.** Every
  link a user can click therefore comes from a URL that Tavily actually returned and that
  was persisted for this session.
* Any `[n]` the model invents outside `1..len(sources)` is removed. Surviving numbers are
  never renumbered, so a citation keeps pointing at the source it was written for.
"""

import re
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.exceptions import ReportGenerationError
from app.core.logging import logger
from app.services.extraction import RetrievedSource
from app.services.llm import llm_service

SYSTEM_PROMPT = (
    "You are a careful research assistant. You answer using ONLY the numbered source "
    "material provided to you.\n"
    "Rules:\n"
    "- Cite every factual claim with the matching source number in ASCII square "
    "brackets, for example [2]. Use no other bracket style.\n"
    "- Never invent a source number that is not in the provided list.\n"
    "- Never write URLs, links, or a reference list; those are added separately.\n"
    "- If the material does not establish something, say so plainly instead of guessing.\n"
    "- Where sources disagree, say so and give both sides.\n"
    "- Write in Markdown. Do not use raw HTML.\n"
    "Structure the answer as:\n"
    "## Answer\n"
    "A direct response to the question in a short paragraph.\n"
    "## Key findings\n"
    "Grouped short sections with headings where it helps.\n"
    "## Uncertainties\n"
    "Limitations and disagreements visible in the material, or 'None identified'.\n"
    "## Conclusion\n"
    "Two or three sentences."
)

# Citation brackets. Models do not all emit ASCII: `openai/gpt-oss-120b` writes 【3】 and
# often the Firecrawl-style 【3†L1-L4】. Only the source number is meaningful here, so every
# recognised form is normalised to ASCII [3] and the frontend has one form to linkify.
# The lookahead keeps Markdown links such as [1](https://...) intact.
CITATION_RE = re.compile(
    r"[\[【［〔]\s*(\d{1,3})\s*(?:†[^\]】］〕]*)?\s*[\]】］〕](?!\()"
)


@dataclass
class ReportResult:
    title: str
    answer_markdown: str


def build_source_material(sources: list[RetrievedSource]) -> str:
    """Render sources as a numbered block, each capped, with a total budget."""
    settings = get_settings()
    per_source = settings.MAX_SOURCE_CHARS
    budget = settings.MAX_TOTAL_SOURCE_CHARS
    blocks: list[str] = []
    used = 0

    for index, source in enumerate(sources, start=1):
        text = (source.text or "").strip()
        if not text:
            continue
        remaining = budget - used
        if remaining <= 0:
            logger.info("Source material budget reached", data={"included": index - 1})
            break
        excerpt = text[: min(per_source, remaining)]
        used += len(excerpt)
        blocks.append(
            f"[{index}] {source.title}\n"
            f"URL: {source.url}\n"
            f"{'Full page text' if source.content else 'Search snippet only'}\n\n"
            f"{excerpt}"
        )

    return "\n\n---\n\n".join(blocks)


def validate_citations(body: str, source_count: int) -> str:
    """Normalise citation brackets and remove any that point at no real source.

    Surviving numbers are deliberately **not** renumbered. The reference list is built from
    the stored sources in their own order, so `[7]` must keep meaning the 7th stored
    source; compacting the numbering would silently re-point a claim at the wrong page,
    which is the exact failure this module exists to prevent. Gaps in the sequence are
    honest and correct.
    """
    if source_count <= 0:
        return CITATION_RE.sub("", body)

    dropped: set[int] = set()
    normalised = 0

    def replace(match: re.Match) -> str:
        nonlocal normalised
        number = int(match.group(1))
        if not 1 <= number <= source_count:
            dropped.add(number)
            return ""
        if match.group(0) != f"[{number}]":
            normalised += 1
        return f"[{number}]"

    cleaned = CITATION_RE.sub(replace, body)

    if normalised:
        logger.info(
            "Normalised citation bracket style",
            data={"converted": normalised},
        )
    if dropped:
        logger.warning(
            "Removed citations that pointed at no retrieved source",
            data={"dropped": sorted(dropped), "source_count": source_count},
        )

    return cleaned


def build_reference_list(sources: list[RetrievedSource]) -> str:
    """Build the reference list from stored source rows. Never from model output."""
    lines = []
    for index, source in enumerate(sources, start=1):
        method = (
            "full page"
            if source.retrieval_method == "firecrawl"
            else "search snippet only"
        )
        lines.append(f"{index}. [{source.title}]({source.url}) — {source.domain} ({method})")
    return "\n".join(lines)


MAX_PRIOR_CONTEXT_CHARS = 6000


def _prepare_prior_context(text: str | None) -> str:
    """Keep prior research as background only, with its old citation numbers removed.

    A previous answer can legitimately contain `[2]` pointing at a source list that no
    longer exists in this run. Carrying that marker into the new prompt invites the model
    to reuse a number that now points somewhere else, so the brackets are stripped.
    """
    if not text:
        return ""
    cleaned = CITATION_RE.sub("", text)
    cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines()).strip()
    return cleaned[:MAX_PRIOR_CONTEXT_CHARS]


class ReportService:
    async def write_draft(
        self,
        question: str,
        sources: list[RetrievedSource],
        prior_context: str | None = None,
    ) -> str:
        """Write the body only. References are never part of the model's output."""
        if not sources:
            raise ReportGenerationError(detail="no sources to write from")

        material = build_source_material(sources)
        if not material.strip():
            raise ReportGenerationError(detail="source material was empty")

        context = _prepare_prior_context(prior_context)
        context_block = (
            "Prior research context (background only; do not cite it and do not reuse "
            "its citation numbers):\n"
            f"{context}\n\n"
            if context
            else ""
        )

        try:
            body = await llm_service.generate(
                prompt=(
                    f"{context_block}"
                    f"Research question:\n{question}\n\n"
                    f"Source material:\n\n{material}\n\n"
                    "Write the answer now. Cite with [n] square brackets."
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=4096,
            )
        except Exception as exc:
            raise ReportGenerationError(detail=f"llm generation failed: {exc}") from exc

        body = (body or "").strip()
        if not body:
            raise ReportGenerationError(detail="model returned an empty answer")

        return validate_citations(body, len(sources))

    async def revise(
        self,
        question: str,
        body: str,
        sources: list[RetrievedSource],
        feedback: str = "",
    ) -> str:
        """Rewrite a draft the verifier flagged, keeping only supported claims.

        This is the writer's move in the verifier→writer negotiation: the critic's
        verdict (its edited body + note) is fed back as guidance, and the writer
        rewrites rather than the orchestrator shipping a critic-authored text.
        Mirrors write_draft's error contract: empty output is an error.
        """
        if not sources:
            raise ReportGenerationError(detail="no sources to write from")

        material = build_source_material(sources)
        if not material.strip():
            raise ReportGenerationError(detail="source material was empty")

        note = " ".join((feedback or "").split()).strip()
        try:
            rewritten = await llm_service.generate(
                prompt=(
                    f"Research question:\n{question}\n\n"
                    f"Current draft:\n\n{body}\n\n"
                    f"Numbered source material:\n\n{material}\n\n"
                    f"Reviewer verdict: {note or ('some claims were unsupported and were '
                    'removed or qualified in this draft.')}\n\n"
                    "Rewrite the answer: keep every claim the sources support with its "
                    "[n] citation, remove or explicitly qualify anything the sources do "
                    "not establish, and keep the same Markdown structure. Never add new "
                    "facts, sources, URLs, or a reference list."
                ),
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=4096,
            )
        except Exception as exc:
            raise ReportGenerationError(detail=f"llm revision failed: {exc}") from exc

        rewritten = (rewritten or "").strip()
        if not rewritten:
            raise ReportGenerationError(detail="model returned an empty revision")

        return validate_citations(rewritten, len(sources))

    def finalize(
        self,
        body: str,
        sources: list[RetrievedSource],
        question: str = "",
    ) -> ReportResult:
        """Attach a reference list built from stored sources, never from model output."""
        body = validate_citations(body, len(sources))
        references = build_reference_list(sources)
        answer = f"{body}\n\n## References\n\n{references}\n"
        return ReportResult(title=_derive_title(question), answer_markdown=answer)

    async def write_report(
        self, question: str, sources: list[RetrievedSource]
    ) -> ReportResult:
        body = await self.write_draft(question, sources)
        return self.finalize(body, sources, question)


def _derive_title(question: str) -> str:
    """A readable title from the question, without another model call."""
    cleaned = " ".join(question.split()).strip().rstrip("?")
    if len(cleaned) <= 90:
        return cleaned or "Research Report"
    return cleaned[:87].rsplit(" ", 1)[0] + "..."


report_service = ReportService()
