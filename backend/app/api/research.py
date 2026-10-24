import asyncio
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.logging import logger
from app.database.database import get_db, get_db_readonly, _get_session_factory
from app.database.models import (
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_QUEUED,
    TERMINAL_STATUSES,
    Report,
    ResearchActivity,
    ResearchSession,
    normalize_status,
)
from app.schemas.research import (
    RenameResearchRequest,
    ResearchResponse,
    ResearchStatusResponse,
    StartResearchRequest,
)
from app.services.research import ResearchService

router = APIRouter()

POLL_INTERVAL_SECONDS = 1.0
KEEPALIVE_SECONDS = 15.0
MAX_STREAM_SECONDS = 900.0


def _parse_uuid(research_id: str) -> UUID:
    try:
        return UUID(research_id)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid research ID format")


def _parse_plan(raw: str | None) -> list[str]:
    """Read the stored plan without letting a bad row break the status endpoint."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, str)]


async def _run_in_background(research_id: str) -> None:
    """Run the workflow on its own DB session so the request can return immediately."""
    session_factory = _get_session_factory()
    async with session_factory() as db:
        try:
            # The per-run depth override is stored on the session row, so the worker does
            # not need it passed through the background task signature.
            await ResearchService(db).run(UUID(research_id))
        except Exception:
            # `run` owns its own failure handling; anything reaching here is a bug in the
            # handler itself and is logged rather than crashing the worker.
            logger.error(
                "Background research handler failed",
                data={"research_id": research_id},
                exc_info=True,
            )


@router.post("/api/research", response_model=ResearchResponse)
async def start_research(
    request: StartResearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    parent: ResearchSession | None = None
    if request.parent_research_id:
        parent_id = _parse_uuid(request.parent_research_id)
        parent = await db.get(ResearchSession, parent_id)
        if parent is None:
            raise HTTPException(status_code=404, detail="Parent research not found")
        if parent.status != STATUS_COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="The parent research must be completed before a follow-up.",
            )

    session = ResearchSession(
        id=uuid4(),
        query=request.query.strip(),
        status=STATUS_QUEUED,
        parent_session_id=parent.id if parent else None,
        current_stage="queued",
        max_iterations=request.max_iterations,
        progress_message=(
            f"Follow-up queued for {parent.id}" if parent else "Queued"
        ),
    )
    db.add(session)
    await db.commit()
    research_id = str(session.id)

    background_tasks.add_task(_run_in_background, research_id)
    return ResearchResponse(research_id=research_id, status="started")


@router.post("/api/research/{research_id}/cancel")
async def cancel_research(
    research_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Ask a live run to stop. Idempotent: a finished run is returned unchanged.

    The workflow notices the flag at its next stage boundary and records `cancelled`,
    so money is not spent on the remaining stages but nothing is left half-written.
    """
    research_uuid = _parse_uuid(research_id)
    session = await db.get(ResearchSession, research_uuid)
    if session is None:
        raise HTTPException(status_code=404, detail="Research session not found")

    if session.status in TERMINAL_STATUSES:
        return {"research_id": research_id, "status": normalize_status(session.status)}

    session.cancel_requested = True
    if session.status == STATUS_QUEUED:
        # Nothing has started yet, so there is no stage boundary to wait for.
        session.status = STATUS_CANCELLED
        session.current_stage = "complete"
        session.progress_message = "Research cancelled"
        session.completed_at = datetime.now(timezone.utc)
        db.add(
            ResearchActivity(
                session_id=session.id, stage="complete", message="Research cancelled by user"
            )
        )
    await db.commit()
    return {"research_id": research_id, "status": normalize_status(session.status)}


@router.patch("/api/research/{research_id}")
async def rename_research(
    research_id: str,
    request: RenameResearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Set (or clear) the display name used by history and the library."""
    research_uuid = _parse_uuid(research_id)
    session = await db.get(ResearchSession, research_uuid)
    if session is None:
        raise HTTPException(status_code=404, detail="Research session not found")

    title = (request.title or "").strip()
    session.display_title = title or None
    await db.commit()
    return {
        "research_id": str(session.id),
        "display_title": session.display_title,
    }


@router.delete("/api/research/{research_id}", status_code=204)
async def delete_research(
    research_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a run and everything that belongs to it."""
    research_uuid = _parse_uuid(research_id)
    session = await db.get(ResearchSession, research_uuid)
    if session is None:
        raise HTTPException(status_code=404, detail="Research session not found")
    await db.delete(session)
    await db.commit()
    return None


@router.get("/api/research/{research_id}")
async def get_research_status(
    research_id: str,
    db: AsyncSession = Depends(get_db_readonly),
):
    research_uuid = _parse_uuid(research_id)
    session = await db.get(ResearchSession, research_uuid)
    if session is None:
        raise HTTPException(status_code=404, detail="Research session not found")

    report: Report | None = None
    result = await db.execute(
        select(Report).where(Report.session_id == research_uuid)
    )
    report = result.scalar_one_or_none()

    return ResearchStatusResponse(
        research_id=str(session.id),
        query=session.query,
        display_title=session.display_title,
        status=normalize_status(session.status),
        current_stage=session.current_stage,
        progress_message=session.progress_message,
        error_message=session.error_message,
        parent_research_id=(
            str(session.parent_session_id) if session.parent_session_id else None
        ),
        planned_queries=_parse_plan(session.planned_queries),
        report_id=str(report.id) if report else None,
        report_title=report.title if report else None,
        report_markdown=report.answer_markdown if report else None,
        verification_note=report.verification_note if report else None,
        verification_revised=report.verification_revised if report else False,
        verification_available=report.verification_available if report else True,
        removed_claims=report.removed_claims if report else 0,
        max_iterations=session.max_iterations,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at,
    )

@router.get("/api/research/{research_id}/stream")
async def stream_research(research_id: str):
    """Stream real workflow events.

    Activity rows are append-only and monotonically numbered, so tracking the highest id
    already seen gives an exact change signal: an event is emitted when, and only when, a
    stage actually produced one.
    """
    try:
        research_uuid = UUID(research_id)
    except (ValueError, AttributeError, TypeError):
        async def reject():
            yield {"event": "error", "data": json.dumps({"message": "Invalid research ID"})}
        return EventSourceResponse(reject())

    async def event_generator():
        session_factory = _get_session_factory()
        last_id = 0
        seconds_since_keepalive = 0.0
        elapsed = 0.0

        while True:
            stage_events = []
            is_terminal = False
            complete_payload = None

            async with session_factory() as db:
                session = await db.get(ResearchSession, research_uuid)
                if session is None:
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": "Research session not found"}),
                    }
                    return

                rows = (
                    await db.execute(
                        select(ResearchActivity)
                        .where(
                            ResearchActivity.session_id == research_uuid,
                            ResearchActivity.id > last_id,
                        )
                        .order_by(ResearchActivity.id.asc())
                    )
                ).scalars().all()

                for row in rows:
                    last_id = max(last_id, row.id)
                    stage_events.append(
                        {
                            "event": "stage",
                            "data": json.dumps(
                                {
                                    "research_id": research_id,
                                    "stage": row.stage,
                                    "message": row.message,
                                    "at": row.created_at.isoformat() if row.created_at else None,
                                }
                            ),
                        }
                    )

                if session.status in TERMINAL_STATUSES:
                    is_terminal = True
                    complete_payload = {
                        "research_id": research_id,
                        "status": normalize_status(session.status),
                        "current_stage": session.current_stage,
                        "progress_message": session.progress_message,
                    }
                    if normalize_status(session.status) == STATUS_FAILED:
                        complete_payload["message"] = session.error_message or "Research failed"

            for event in stage_events:
                yield event

            if is_terminal:
                yield {"event": "complete", "data": json.dumps(complete_payload)}
                return

            if seconds_since_keepalive >= KEEPALIVE_SECONDS:
                yield {"event": "keepalive", "data": ""}
                seconds_since_keepalive = 0.0

            # Backstop: a run that dies without reaching a terminal status would
            # otherwise hold the connection open indefinitely. Close it and let the
            # client fall back to polling the status endpoint.
            if elapsed >= MAX_STREAM_SECONDS:
                yield {
                    "event": "timeout",
                    "data": json.dumps(
                        {"message": "Progress stream closed. Poll for status."}
                    ),
                }
                return

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            seconds_since_keepalive += POLL_INTERVAL_SECONDS
            elapsed += POLL_INTERVAL_SECONDS

    return EventSourceResponse(event_generator())


@router.get("/api/research/{research_id}/activity")
async def get_activity(
    research_id: str,
    db: AsyncSession = Depends(get_db_readonly),
):
    """The recorded timeline, for a session reopened from history."""
    research_uuid = _parse_uuid(research_id)
    rows = (
        await db.execute(
            select(ResearchActivity)
            .where(ResearchActivity.session_id == research_uuid)
            .order_by(ResearchActivity.id.asc())
        )
    ).scalars().all()
    return {
        "activity": [
            {
                "stage": row.stage,
                "message": row.message,
                "at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }
