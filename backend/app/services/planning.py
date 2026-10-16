"""Stage 1 — turn the user's question into 2–4 search queries.

Planning is best-effort by design: if the model is unavailable or answers with something
unusable, the original question is used as the single query. A research run must not die
because a planning call did.
"""

from app.core.config import get_settings
from app.core.logging import logger
from app.services.llm import llm_service

SYSTEM_PROMPT = (
    "You turn a research question into web search queries. "
    "Reply with JSON only: {\"queries\": [\"...\", \"...\"]}. "
    "Produce between 2 and 4 short queries. "
    "Cover distinct angles of the question rather than repeating it. "
    "Do not include quotes, citations, or commentary."
)


def _clean_query(raw: str) -> str:
    return " ".join(str(raw).split()).strip().strip('"').strip()


def _coerce_queries(payload) -> list[str]:
    if isinstance(payload, dict):
        raw = payload.get("queries") or payload.get("search_queries") or []
    elif isinstance(payload, list):
        raw = payload
    else:
        raw = []
    if not isinstance(raw, list):
        return []
    cleaned = [_clean_query(item) for item in raw]
    return [q for q in cleaned if q]


class PlanningService:
    def __init__(self):
        settings = get_settings()
        self.max_queries = settings.MAX_SEARCH_QUERIES

    async def plan_queries(self, question: str) -> list[str]:
        """Return 2–4 queries, degrading to the original question on any problem."""
        question = question.strip()
        try:
            payload = await llm_service.structured_generate(
                prompt=f"Research question: {question}",
                system_prompt=SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=300,
            )
        except Exception as exc:
            logger.warning(
                "Query planning failed, using the original question",
                data={"error": type(exc).__name__},
            )
            return [question]

        queries = _coerce_queries(payload)
        if not queries:
            logger.warning("Query planning returned nothing usable")
            return [question]

        deduped: list[str] = []
        for query in queries:
            if query not in deduped:
                deduped.append(query)
        return deduped[: self.max_queries]


planning_service = PlanningService()
