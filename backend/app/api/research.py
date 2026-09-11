from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
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
