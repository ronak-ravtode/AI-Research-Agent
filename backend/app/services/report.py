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
    "- Cite every factual claim with the matching source number in square brackets, "
    "for example [2].\n"
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

CITATION_RE = re.compile(r"\[(\d{1,3})\]")


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
    """Remove citation numbers that point at no real source.

    Surviving numbers are deliberately **not** renumbered. The reference list is built from
    the stored sources in their own order, so `[7]` must keep meaning the 7th stored
    source; compacting the numbering would silently re-point a claim at the wrong page,
    which is the exact failure this module exists to prevent. Gaps in the sequence are
    honest and correct.
    """
    if source_count <= 0:
        return CITATION_RE.sub("", body)

    dropped: set[int] = set()

    def replace(match: re.Match) -> str:
        number = int(match.group(1))
        if 1 <= number <= source_count:
            return match.group(0)
        dropped.add(number)
        return ""

    cleaned = CITATION_RE.sub(replace, body)

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


class ReportService:
    async def write_report(
        self, question: str, sources: list[RetrievedSource]
    ) -> ReportResult:
        if not sources:
            raise ReportGenerationError(detail="no sources to write from")

        material = build_source_material(sources)
        if not material.strip():
            raise ReportGenerationError(detail="source material was empty")

        try:
            body = await llm_service.generate(
                prompt=(
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

        body = validate_citations(body, len(sources))

        references = build_reference_list(sources)
        answer = f"{body}\n\n## References\n\n{references}\n"

        return ReportResult(title=_derive_title(question), answer_markdown=answer)


def _derive_title(question: str) -> str:
    """A readable title from the question, without another model call."""
    cleaned = " ".join(question.split()).strip().rstrip("?")
    if len(cleaned) <= 90:
        return cleaned or "Research Report"
    return cleaned[:87].rsplit(" ", 1)[0] + "..."


report_service = ReportService()
