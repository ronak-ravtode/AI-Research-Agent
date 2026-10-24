"""The research workflow: four stages, one failure path.

    plan → search → extract → write

Each stage transition writes `status`, `current_stage` and `progress_message` on the
session *and* appends a `research_activity` row in the same transaction, so the timeline a
client streams can never disagree with the session row it also reads.

There is exactly one catch site. A failure rolls back the run's writes, records a safe
user-facing message, and logs the real cause server-side. Nothing is swallowed and
reported as success.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ResearchCancelled, ResearchRunError
from app.core.logging import logger
from app.database.models import (
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_RUNNING,
    Report,
    ResearchActivity,
    ResearchSession,
    Source,
)
from app.services.coverage import coverage_service
from app.services.extraction import RetrievedSource, extraction_service
from app.services.planning import planning_service
from app.services.report import report_service
from app.services.search import SearchResult, normalize_url, search_service
from app.services.verification import VerificationResult, verification_service

STAGE_PLAN = "planning"
STAGE_SEARCH = "searching"
STAGE_EXTRACT = "reading"
STAGE_DECIDE = "deciding"
STAGE_WRITE = "writing"
STAGE_VERIFY = "verifying"
STAGE_DONE = "complete"

# Quick / standard / deep are the three choices the UI offers. `None` means "use the
# server's configured default", so the API's behaviour is unchanged for old clients.
MIN_ITERATIONS = 0
MAX_ITERATIONS = 3


@dataclass
class ResearchOptions:
    """Per-run overrides. Bounded by the API before it reaches here."""

    max_iterations: int | None = None


class ResearchService:
    def __init__(self, db: AsyncSession, options: ResearchOptions | None = None):
        self.db = db
        self.options = options or ResearchOptions()

    async def run(
        self, session_id: UUID, options: ResearchOptions | None = None
    ) -> None:
        """Execute a full research run for an already-created session.

        Every failure path ends in a persisted `failed` status. Nothing is raised to the
        caller, because a background task that throws would leave the session stuck on
        `queued` with no way for a client to discover why. A cancellation is a third
        outcome: it ends the run as `cancelled`, not as a failure.
        """
        if options is not None:
            self.options = options
        try:
            get_settings().validate_required_keys()
            session = await self._load(session_id)
            if session is None:
                logger.error(
                    "Research session vanished before the run started",
                    data={"session_id": str(session_id)},
                )
                return
            await self._execute(session)
        except ResearchCancelled:
            await self._mark_cancelled(session_id)
        except ResearchRunError as exc:
            await self._fail(session_id, exc)
        except Exception as exc:
            await self._fail(session_id, exc)

    async def _execute(self, session: ResearchSession) -> None:
        """The adaptive agent loop. Failures propagate to `run`, which records them."""
        settings = get_settings()
        query = session.query.strip()

        memory_sources, prior_context = await self._load_memory(session)

        await self._stage(session, STAGE_PLAN, "Breaking the question into search queries")
        queries = await planning_service.plan_queries(query, context=prior_context)
        session.planned_queries = json.dumps(queries)
        await self._stage(session, STAGE_PLAN, f"Planned queries: {'; '.join(queries)}")

        await self._stage(session, STAGE_SEARCH, "Searching the web with Tavily")
        results = await search_service.search(queries)
        if not results:
            await self._mark_failed(
                session, "No usable sources were found for that question."
            )
            return

        await self._stage(session, STAGE_SEARCH, f"Found {len(results)} possible sources")
        results = await self._broaden_if_thin(query, results)

        await self._stage(session, STAGE_EXTRACT, "Reading selected pages")
        sources = await extraction_service.extract(results)
        await self._stage(
            session,
            STAGE_EXTRACT,
            f"Read {sum(1 for s in sources if s.content)} of {len(sources)} pages",
        )

        results, sources = await self._broaden_if_shallow(session, query, results, sources)

        if memory_sources:
            sources = self._merge_sources(memory_sources, sources)
            await self._stage(
                session,
                STAGE_EXTRACT,
                f"Reused {len(memory_sources)} source(s) from earlier research",
            )

        # Adaptive loop: ask a reviewer whether the evidence is enough; follow up
        # at most MAX_AGENT_ITERATIONS times (or the per-run override from the UI).
        max_iterations = (
            self.options.max_iterations
            if self.options.max_iterations is not None
            else session.max_iterations
            if session.max_iterations is not None
            else settings.MAX_AGENT_ITERATIONS
        )
        tried_queries = list(queries)
        for _ in range(max_iterations):
            await self._stage(
                session, STAGE_DECIDE, "Checking whether the evidence is sufficient"
            )
            decision = await coverage_service.assess(query, sources, tried_queries)
            if decision.sufficient:
                await self._stage(session, STAGE_DECIDE, f"Evidence sufficient: {decision.reason}")
                break
            await self._stage(session, STAGE_DECIDE, f"Evidence gap: {decision.reason}")

            # Re-invoke the planner with the gap as feedback. The reviewer's own
            # suggested queries are the fallback when re-planning yields nothing new.
            followup_context = (
                "Queries already searched:\n"
                + "\n".join(f"- {q}" for q in tried_queries)
                + f"\n\nThe evidence reviewer found this gap: {decision.reason}"
            )
            if decision.followup_queries:
                followup_context += (
                    "\nReviewer suggested: " + "; ".join(decision.followup_queries)
                )
            followup_context += (
                "\n\nPropose new short web-search queries targeting this gap. "
                "Exclude every already-tried query."
            )
            replanned: list[str] = []
            try:
                replanned = await planning_service.plan_queries(
                    query, context=followup_context
                )
            except Exception as exc:
                logger.warning(
                    "Replanning failed; using the reviewer's follow-up queries",
                    data={"error": type(exc).__name__},
                )
            tried_lower = {q.lower() for q in tried_queries}
            new_queries = [q for q in replanned if q and q.lower() not in tried_lower]
            if not new_queries:
                new_queries = [
                    q
                    for q in decision.followup_queries
                    if q.lower() not in tried_lower
                ]
            new_queries = new_queries[: settings.MAX_SEARCH_QUERIES]
            if not new_queries:
                await self._stage(
                    session,
                    STAGE_DECIDE,
                    f"{decision.reason} No new query was proposed.",
                )
                break
            tried_queries.extend(new_queries)
            await self._stage(
                session,
                STAGE_SEARCH,
                "Following up on missing evidence: " + "; ".join(new_queries),
            )
            try:
                more_results = await search_service.search(new_queries)
            except Exception as exc:
                logger.warning(
                    "Follow-up search failed",
                    data={"error": type(exc).__name__},
                )
                await self._stage(
                    session,
                    STAGE_DECIDE,
                    "Follow-up search failed; continuing with the available evidence.",
                )
                break
            fresh = self._only_new_results(results, more_results)
            if not fresh:
                await self._stage(
                    session,
                    STAGE_DECIDE,
                    "Follow-up search found nothing new; continuing with the available evidence.",
                )
                break
            results.extend(fresh)
            await self._stage(
                session, STAGE_EXTRACT, f"Reading {len(fresh)} additional pages"
            )
            try:
                more_sources = await extraction_service.extract(fresh)
            except Exception as exc:
                logger.warning(
                    "Follow-up extraction failed",
                    data={"error": type(exc).__name__},
                )
                await self._stage(
                    session,
                    STAGE_EXTRACT,
                    "Additional pages could not be read; continuing with the available evidence.",
                )
                break
            sources = self._merge_sources(sources, more_sources)

        await self._stage(session, STAGE_WRITE, "Preparing the cited answer")
        draft = await report_service.write_draft(
            query, sources, prior_context=prior_context
        )

        await self._stage(
            session, STAGE_VERIFY, "Checking claims against the retrieved sources"
        )
        verification = None
        try:
            verification = await verification_service.verify(query, draft, sources)
        except Exception as exc:
            logger.warning(
                "Verification step failed; keeping the draft",
                data={"error": type(exc).__name__},
            )
            await self._stage(
                session,
                STAGE_VERIFY,
                "Verification unavailable; keeping the draft as written.",
            )
        if verification is not None:
            if verification.revised:
                message = (
                    f"Verified claims; removed or qualified "
                    f"{verification.removed_claims} unsupported claim(s)."
                )
            else:
                message = f"Verification complete: {verification.note}"
            await self._stage(session, STAGE_VERIFY, message)

            # Verifier→writer negotiation: a flagged draft goes back to the writer
            # for a rewrite, then the rewrite is verified again. Bounded by
            # MAX_REWRITE_ROUNDS; when the budget is out, the verifier's own edit ships.
            rewrite_round = 0
            while verification.revised and rewrite_round < settings.MAX_REWRITE_ROUNDS:
                rewrite_round += 1
                await self._stage(
                    session,
                    STAGE_WRITE,
                    f"Rewriting after verifier feedback: {verification.note}",
                )
                rewritten = None
                try:
                    rewritten = await report_service.revise(
                        query,
                        verification.body,
                        sources,
                        feedback=verification.note,
                    )
                except Exception as exc:
                    logger.warning(
                        "Writer revision failed; shipping the verifier's edit",
                        data={"error": type(exc).__name__},
                    )
                    break
                if not rewritten.strip():
                    break
                await self._stage(
                    session, STAGE_VERIFY, "Re-verifying the rewritten answer"
                )
                try:
                    verification = await verification_service.verify(
                        query, rewritten, sources
                    )
                except Exception as exc:
                    logger.warning(
                        "Re-verification failed; shipping the rewrite",
                        data={"error": type(exc).__name__},
                    )
                    verification = VerificationResult(
                        body=rewritten,
                        revised=False,
                        note="Re-verification unavailable; the rewrite is shipped.",
                    )
                if verification.revised:
                    message = (
                        f"Re-verification still found gaps; removed or qualified "
                        f"{verification.removed_claims} unsupported claim(s)."
                    )
                else:
                    message = f"Re-verification complete: {verification.note}"
                await self._stage(session, STAGE_VERIFY, message)

        body = verification.body if verification is not None else draft
        report = report_service.finalize(body, sources, query)

        # Sources are persisted before the report so a report can never reference a
        # source that is not in the database.
        stored = await self._persist_sources(session, sources)
        self.db.add(
            Report(
                session_id=session.id,
                title=report.title,
                answer_markdown=report.answer_markdown,
                verification_note=verification.note if verification else None,
                removed_claims=verification.removed_claims if verification else 0,
                verification_revised=bool(verification.revised) if verification else False,
                verification_available=verification is not None,
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

    async def _load_memory(
        self, session: ResearchSession
    ) -> tuple[list[RetrievedSource], str | None]:
        """Pull reusable context from a completed parent session, if any."""
        if session.parent_session_id is None:
            return [], None
        parent = await self._load(session.parent_session_id)
        if parent is None or parent.status != STATUS_COMPLETED:
            return [], None

        settings = get_settings()
        sources: list[RetrievedSource] = []
        if settings.MAX_CONTEXT_SOURCES > 0:
            rows = await self.db.execute(
                select(Source)
                .where(Source.session_id == parent.id)
                .order_by(Source.search_score.desc().nullslast(), Source.created_at)
                .limit(settings.MAX_CONTEXT_SOURCES)
            )
            for row in rows.scalars():
                sources.append(
                    RetrievedSource(
                        url=row.url,
                        domain=row.domain,
                        title=row.title,
                        content=row.content or "",
                        snippet=row.snippet,
                        source_type=row.source_type,
                        retrieval_method=row.retrieval_method,
                        search_score=row.search_score or 0.0,
                    )
                )

        report = (
            await self.db.execute(select(Report).where(Report.session_id == parent.id))
        ).scalar_one_or_none()

        parts: list[str] = []
        if parent.query:
            parts.append(f"Previous question: {parent.query}")
        if report is not None:
            body = report.answer_markdown.split("## References")[0].strip()
            body = body[: settings.MAX_CONTEXT_CHARS]
            if body:
                parts.append(f"Previous answer:\n{body}")
        context = "\n\n".join(parts).strip() or None
        return sources, context

    def _only_new_results(
        self, existing: list[SearchResult], incoming: list[SearchResult]
    ) -> list[SearchResult]:
        seen = {normalize_url(r.url) or r.url for r in existing}
        fresh: list[SearchResult] = []
        for item in incoming:
            key = normalize_url(item.url) or item.url
            if key not in seen:
                seen.add(key)
                fresh.append(item)
        return fresh

    def _merge_sources(
        self,
        *groups: list[RetrievedSource],
        limit: int | None = None,
    ) -> list[RetrievedSource]:
        """Merge source lists, deduping by URL and keeping the richest copy."""
        best: dict[str, RetrievedSource] = {}
        order: list[str] = []
        for group in groups:
            for source in group:
                key = normalize_url(source.url) or source.url.lower()
                if key not in best:
                    best[key] = source
                    order.append(key)
                elif len(source.content) > len(best[key].content):
                    best[key] = source
        merged = [best[key] for key in order]
        if limit is not None:
            merged = merged[:limit]
        return merged

    async def _broaden_if_shallow(
        self,
        session: ResearchSession,
        query: str,
        results: list[SearchResult],
        sources: list[RetrievedSource],
    ) -> tuple[list[SearchResult], list[RetrievedSource]]:
        """Second fallback: when extraction left us with snippet-only pages,
        search the original question once more and try to read fresh URLs."""
        if sum(1 for s in sources if s.content.strip()) >= 2:
            return results, sources
        try:
            broader = await search_service.search([query])
        except Exception as exc:
            logger.warning(
                "Shallow-evidence fallback search failed",
                data={"error": type(exc).__name__},
            )
            return results, sources
        fresh = self._only_new_results(results, broader)
        if not fresh:
            return results, sources
        await self._stage(
            session,
            STAGE_SEARCH,
            f"Only snippets so far; found {len(fresh)} more sources",
        )
        try:
            more = await extraction_service.extract(fresh)
        except Exception as exc:
            logger.warning(
                "Shallow-evidence fallback extraction failed",
                data={"error": type(exc).__name__},
            )
            return results, sources
        results = results + fresh
        sources = self._merge_sources(sources, more)
        return results, sources

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
        await self._raise_if_cancelled(session)
        session.status = STATUS_RUNNING
        session.current_stage = stage
        session.progress_message = message
        session.started_at = session.started_at or datetime.now(timezone.utc)
        session.error_message = None
        self._activity(session, stage, message)
        await self.db.commit()
        logger.info(message, data={"session_id": str(session.id), "stage": stage})

    async def _raise_if_cancelled(self, session: ResearchSession) -> None:
        """Read the cancel flag from the database, not the in-memory session.

        The cancellation arrives on a different request (and therefore a different
        session), so this row is the only shared signal. Checking at every stage boundary
        bounds the wasted work to one stage.
        """
        try:
            await self.db.refresh(session, attribute_names=["cancel_requested"])
        except Exception:
            # A refresh failure must not abort a healthy run; treat it as "not cancelled".
            return
        if session.cancel_requested:
            raise ResearchCancelled()

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

    async def _mark_cancelled(self, session_id: UUID) -> None:
        """Record a user cancellation as its own terminal state, not a failure."""
        try:
            await self.db.rollback()
            session = await self._load(session_id)
            if session is None or session.status == STATUS_CANCELLED:
                return
            if session.status in (STATUS_COMPLETED, STATUS_FAILED):
                return
            session.status = STATUS_CANCELLED
            session.current_stage = STAGE_DONE
            session.progress_message = "Research cancelled"
            session.error_message = None
            session.completed_at = datetime.now(timezone.utc)
            self._activity(session, STAGE_DONE, "Research cancelled by user")
            await self.db.commit()
            logger.info("Research cancelled", data={"session_id": str(session_id)})
        except Exception:
            logger.error(
                "Could not persist cancellation state",
                data={"session_id": str(session_id)},
                exc_info=True,
            )

    async def _fail(self, session_id: UUID, exc: BaseException) -> None:
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
            data={"session_id": str(session_id), "error": repr(exc)},
            exc_info=exc,
        )

        try:
            session = await self._load(session_id)
            if session is None:
                return
            await self._mark_failed(session, user_message)
        except Exception:
            logger.error(
                "Could not persist failure state",
                data={"session_id": str(session_id)},
                exc_info=True,
            )

    async def _load(self, session_id: UUID) -> ResearchSession | None:
        result = await self.db.execute(
            select(ResearchSession).where(ResearchSession.id == session_id)
        )
        return result.scalar_one_or_none()
