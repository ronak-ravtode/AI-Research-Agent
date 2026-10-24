"""Coverage agent — decide whether the retrieved evidence is enough to write from.

This is the first genuinely adaptive step in the workflow. The planner produces a first
set of queries; after those sources are read, this agent judges the evidence and can send
the researcher back for one or two targeted follow-up searches. It is deliberately
best-effort: if the model is unavailable or answers with something unusable, the run
proceeds to the writer with the evidence it already has rather than failing.
"""

from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.logging import logger
from app.services.extraction import RetrievedSource
from app.services.llm import llm_service
from app.services.report import build_source_material

SYSTEM_PROMPT = (
    "You audit research evidence. You are given a research question, the sources already "
    "retrieved, and the queries already searched.\n"
    "Decide whether the evidence is sufficient to answer the question with citations.\n"
    "Reply with JSON only:\n"
    '{"sufficient": true|false, "followup_queries": ["..."], "reason": "..."}\n'
    "Rules:\n"
    "- Mark sufficient=true when the sources cover the main angles of the question.\n"
    "- Mark sufficient=false only when a specific, answerable gap remains.\n"
    "- Follow-up queries must be short, distinct from the tried queries, and target the "
    "gap. Return at most two.\n"
    "- If followup_queries is empty, sufficient must be true.\n"
    "- Keep reason to one sentence. No commentary outside the JSON."
)

MAX_FOLLOWUP_QUERIES = 2


@dataclass
class CoverageDecision:
    sufficient: bool
    followup_queries: list[str] = field(default_factory=list)
    reason: str = ""


def _clean_queries(raw) -> list[str]:
    if not isinstance(raw, list):
        return []
    cleaned: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        query = " ".join(item.split()).strip().strip('"')
        if query and query.lower() not in {q.lower() for q in cleaned}:
            cleaned.append(query)
    return cleaned


class CoverageService:
    def __init__(self):
        self.max_queries = get_settings().MAX_SEARCH_QUERIES

    async def assess(
        self,
        question: str,
        sources: list[RetrievedSource],
        tried_queries: list[str],
    ) -> CoverageDecision:
        """Judge coverage, defaulting to "write now" on every failure path."""
        tried = [q for q in tried_queries if q and q.strip()]
        material = build_source_material(sources) or "(no readable source text)"
        prompt = (
            f"Research question:\n{question}\n\n"
            f"Queries already searched:\n"
            + ("\n".join(f"- {q}" for q in tried) or "- (none)")
            + f"\n\nEvidence retrieved:\n\n{material}"
        )

        try:
            payload = await llm_service.structured_generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=400,
            )
        except Exception as exc:
            logger.warning(
                "Coverage check failed, writing from available evidence",
                data={"error": type(exc).__name__},
            )
            return CoverageDecision(
                sufficient=True,
                reason="Coverage check unavailable; writing from the evidence retrieved.",
            )

        if not isinstance(payload, dict) or not isinstance(payload.get("sufficient"), bool):
            logger.warning("Coverage check returned an unusable payload")
            return CoverageDecision(
                sufficient=True,
                reason="Coverage check returned no usable decision.",
            )

        sufficient = bool(payload["sufficient"])
        reason = " ".join(str(payload.get("reason") or "").split()).strip()
        if not reason:
            reason = (
                "The evidence covers the question."
                if sufficient
                else "Some aspects of the question are not covered yet."
            )

        if sufficient:
            return CoverageDecision(sufficient=True, reason=reason)

        tried_lower = {q.lower() for q in tried}
        followups = [
            q
            for q in _clean_queries(payload.get("followup_queries"))
            if q.lower() not in tried_lower
        ][: min(MAX_FOLLOWUP_QUERIES, self.max_queries)]

        if not followups:
            return CoverageDecision(
                sufficient=True,
                reason=f"{reason} No new query was proposed, so writing now.",
            )

        return CoverageDecision(
            sufficient=False, followup_queries=followups, reason=reason
        )


coverage_service = CoverageService()
