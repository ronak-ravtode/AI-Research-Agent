"""The research workflow: four stages, one failure path.

    plan → search → extract → write

Each stage transition writes `status`, `current_stage` and `progress_message` on the
session *and* appends a `research_activity` row in the same transaction, so the timeline a
client streams can never disagree with the session row it also reads.

There is exactly one catch site. A failure rolls back the run's writes, records a safe
user-facing message, and logs the real cause server-side. Nothing is swallowed and
reported as success.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ResearchRunError
from app.core.logging import logger
from app.database.models import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_RUNNING,
    Report,
    ResearchActivity,
    ResearchSession,
    Source,
)
from app.services.extraction import RetrievedSource, extraction_service
from app.services.planning import planning_service
from app.services.report import report_service
from app.services.search import SearchResult, search_service

STAGE_PLAN = "planning"
STAGE_SEARCH = "searching"
STAGE_EXTRACT = "reading"
STAGE_WRITE = "writing"
STAGE_DONE = "complete"


class ResearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self, session_id: UUID) -> None:
        """Execute a full research run for an already-created session."""
        settings = get_settings()
        settings.validate_required_keys()

        session = await self._load(session_id)
        if session is None:
            raise ResearchRunError(detail=f"session {session_id} disappeared")

        query = session.query.strip()

        try:
            await self._stage(session, STAGE_PLAN, "Breaking the question into search queries")

            queries = await planning_service.plan_queries(query)
            logger.info("Planned search queries", data={"count": len(queries)})

            await self._stage(session, STAGE_SEARCH, "Searching the web with Tavily")
            results = await search_service.search(queries)
            if not results:
                await self._mark_failed(
                    session, "No usable sources were found for that question."
                )
                return

            await self._stage(
                session, STAGE_SEARCH, f"Found {len(results)} possible sources"
            )
            results = await self._broaden_if_thin(query, results)

            await self._stage(session, STAGE_EXTRACT, "Reading selected pages")
            sources = await extraction_service.extract(results)
            await self._stage(
                session,
                STAGE_EXTRACT,
                f"Read {sum(1 for s in sources if s.content)} of {len(sources)} pages",
            )

            await self._stage(session, STAGE_WRITE, "Preparing the cited answer")
            report = await report_service.write_report(query, sources)

            # Sources are persisted before the report so a report can never reference a
            # source that is not in the database.
            stored = await self._persist_sources(session, sources)
            self.db.add(
                Report(
                    session_id=session.id,
                    title=report.title,
                    answer_markdown=report.answer_markdown,
                )
            )
            session.status = STATUS_COMPLETED
            session.current_stage = STAGE_DONE
            session.progress_message = "Research complete"
            session.completed_at = datetime.now(timezone.utc)
            session.error_message = None
            self._activity(session, STAGE_DONE, "Research complete")
            await self.db.commit()

            logger.info(
                "Research completed",
                data={"session_id": str(session.id), "sources": len(stored)},
            )

        except ResearchRunError as exc:
            await self._fail(session, exc)
        except Exception as exc:
            await self._fail(session, exc)

    async def _broaden_if_thin(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """The one allowed fallback: a single broader search on the original question."""
        if len(results) >= 2:
            return results
        try:
            broader = await search_service.search([query])
        except Exception as exc:
            logger.warning(
                "Broader fallback search failed",
                data={"error": type(exc).__name__},
            )
            return results

        seen = {r.normalized_url or r.url for r in results}
        merged = list(results)
        for item in broader:
            key = item.normalized_url or item.url
            if key not in seen:
                seen.add(key)
                merged.append(item)
        merged.sort(key=lambda r: r.score, reverse=True)
        return merged[: get_settings().MAX_SEARCH_RESULTS]

    async def _persist_sources(
        self, session: ResearchSession, sources: list[RetrievedSource]
    ) -> list[Source]:
        stored: list[Source] = []
        for source in sources:
            row = Source(
                session_id=session.id,
                title=source.title,
                url=source.url,
                domain=source.domain,
                source_type=source.source_type,
                snippet=source.snippet,
                content=source.content,
                retrieval_method=source.retrieval_method,
                search_score=source.search_score,
                retrieved_at=datetime.now(timezone.utc),
            )
            self.db.add(row)
            stored.append(row)
        await self.db.flush()
        return stored

    async def _stage(
        self, session: ResearchSession, stage: str, message: str
    ) -> None:
        session.status = STATUS_RUNNING
        session.current_stage = stage
        session.progress_message = message
        session.started_at = session.started_at or datetime.now(timezone.utc)
        session.error_message = None
        self._activity(session, stage, message)
        await self.db.commit()
        logger.info(message, data={"session_id": str(session.id), "stage": stage})

    def _activity(
        self, session: ResearchSession, stage: str, message: str
    ) -> None:
        self.db.add(
            ResearchActivity(
                session_id=session.id, stage=stage, message=message
            )
        )

    async def _mark_failed(self, session: ResearchSession, message: str) -> None:
        session.status = STATUS_FAILED
        session.current_stage = STAGE_DONE
        session.progress_message = "Research failed"
        session.error_message = message
        session.completed_at = datetime.now(timezone.utc)
        self._activity(session, STAGE_DONE, message)
        await self.db.commit()
        logger.warning(
            "Research failed", data={"session_id": str(session.id), "reason": message}
        )

    async def _fail(self, session: ResearchSession, exc: BaseException) -> None:
        """Roll back partial work, then record a safe failure.

        The exception itself goes to the log with a traceback; the client only ever sees the
        class's fixed user_message.
        """
        try:
            await self.db.rollback()
        except Exception:
            logger.error("Rollback failed", data={"exc": repr(exc)})

        user_message = (
            exc.user_message
            if isinstance(exc, ResearchRunError)
            else "Research could not be completed. Please try again."
        )
        logger.error(
            "Research run failed",
            data={"session_id": str(session.id), "error": repr(exc)},
            exc_info=exc,
        )

        try:
            session = await self._load(session.id) or session
            await self._mark_failed(session, user_message)
        except Exception:
            logger.error(
                "Could not persist failure state",
                data={"session_id": str(session.id)},
                exc_info=True,
            )

    async def _load(self, session_id: UUID) -> ResearchSession | None:
        result = await self.db.execute(
            select(ResearchSession).where(ResearchSession.id == session_id)
        )
        return result.scalar_one_or_none()
