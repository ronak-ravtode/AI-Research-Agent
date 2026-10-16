import asyncio
import json
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.logging import logger
from app.database.database import get_db, get_db_readonly, _get_session_factory
from app.database.models import (
    STATUS_FAILED,
    STATUS_QUEUED,
    TERMINAL_STATUSES,
    Report,
    ResearchActivity,
    ResearchSession,
)
from app.schemas.research import (
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


async def _run_in_background(research_id: str) -> None:
    """Run the workflow on its own DB session so the request can return immediately."""
    session_factory = _get_session_factory()
    async with session_factory() as db:
        try:
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
    session = ResearchSession(
        id=uuid4(),
        query=request.query.strip(),
        status=STATUS_QUEUED,
        current_stage="queued",
        progress_message="Queued",
    )
    db.add(session)
    await db.commit()
    research_id = str(session.id)

    background_tasks.add_task(_run_in_background, research_id)
    return ResearchResponse(research_id=research_id, status="started")


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
        status=session.status,
        current_stage=session.current_stage,
        progress_message=session.progress_message,
        error_message=session.error_message,
        report_id=str(report.id) if report else None,
        report_title=report.title if report else None,
        report_markdown=report.answer_markdown if report else None,
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

        async with session_factory() as db:
            while True:
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
                    yield {
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

                if session.status in TERMINAL_STATUSES:
                    payload = {
                        "research_id": research_id,
                        "status": session.status,
                        "current_stage": session.current_stage,
                        "progress_message": session.progress_message,
                    }
                    if session.status == STATUS_FAILED:
                        payload["message"] = session.error_message or "Research failed"
                    yield {"event": "complete", "data": json.dumps(payload)}
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
