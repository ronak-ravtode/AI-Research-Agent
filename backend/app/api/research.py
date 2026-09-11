import asyncio
import json

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.database.models import ResearchSession
from app.schemas.research import StartResearchRequest, ResearchResponse
from app.services.research import ResearchService

router = APIRouter()


@router.post("/api/research", response_model=ResearchResponse)
async def start_research(
    request: StartResearchRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ResearchService(db)
    research_id = await service.start_research(
        query=request.query,
        depth=request.depth,
    )
    return ResearchResponse(research_id=research_id, status="started")


@router.get("/api/research/{research_id}/stream")
async def stream_research(research_id: str, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        while True:
            result = await db.execute(
                select(ResearchSession).where(ResearchSession.id == research_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                yield {"event": "error", "data": json.dumps({"message": "Session not found"})}
                break

            yield {
                "event": "status",
                "data": json.dumps({
                    "research_id": str(research_id),
                    "status": session.status,
                }),
            }

            if session.status in ["completed", "failed"]:
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "research_id": str(research_id),
                        "status": session.status,
                    }),
                }
                break

            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
