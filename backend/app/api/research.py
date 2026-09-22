import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db, get_db_readonly
from app.database.models import ResearchSession
from app.schemas.research import StartResearchRequest, ResearchResponse, ResearchStatusResponse
from app.services.research import ResearchService

router = APIRouter()


async def _run_research_background(research_id: str, query: str, depth: str):
    """Run the full research pipeline in the background."""
    from app.database.database import _get_session_factory
    session_factory = _get_session_factory()
    async with session_factory() as db:
        try:
            service = ResearchService(db)
            await service.start_research(query=query, depth=depth, research_id=research_id)
            await db.commit()
        except Exception:
            await db.rollback()
            raise


@router.post("/api/research", response_model=ResearchResponse)
async def start_research(
    request: StartResearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    from uuid import uuid4
    from datetime import datetime, timezone
    from app.database.models import ResearchSession

    research_id = uuid4()
    session = ResearchSession(
        id=research_id,
        query=request.query,
        research_depth=request.depth,
        status="planning",
        started_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()

    background_tasks.add_task(
        _run_research_background,
        research_id=str(research_id),
        query=request.query,
        depth=request.depth,
    )

    return ResearchResponse(research_id=str(research_id), status="started")


@router.get("/api/research/{research_id}")
async def get_research_status(
    research_id: str,
    db: AsyncSession = Depends(get_db_readonly),
):
    try:
        research_uuid = UUID(research_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid research ID format")

    result = await db.execute(
        select(ResearchSession).where(ResearchSession.id == research_uuid)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return ResearchStatusResponse(
        research_id=str(session.id),
        query=session.query,
        status=session.status.value if hasattr(session.status, "value") else session.status,
        research_depth=session.research_depth,
        started_at=session.started_at,
        completed_at=session.completed_at,
        created_at=session.created_at,
    )


@router.get("/api/research/{research_id}/stream")
async def stream_research(research_id: str):
    async def event_generator():
        from app.database.database import _get_session_factory
        session_factory = _get_session_factory()
        async with session_factory() as db:
            while True:
                try:
                    research_uuid = UUID(research_id)
                except ValueError:
                    yield {"event": "error", "data": json.dumps({"message": "Invalid research ID"})}
                    break

                result = await db.execute(
                    select(ResearchSession).where(ResearchSession.id == research_uuid)
                )
                session = result.scalar_one_or_none()

                if not session:
                    yield {"event": "error", "data": json.dumps({"message": "Session not found"})}
                    break

                status_val = session.status.value if hasattr(session.status, "value") else session.status
                yield {
                    "event": "status",
                    "data": json.dumps({
                        "research_id": str(research_id),
                        "status": status_val,
                    }),
                }

                if status_val in ["completed", "failed"]:
                    yield {
                        "event": "complete",
                        "data": json.dumps({
                            "research_id": str(research_id),
                            "status": status_val,
                        }),
                    }
                    break

                await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
