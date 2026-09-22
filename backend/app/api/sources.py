from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db_readonly
from app.database.models import Source
from app.schemas.source import SourceListResponse, SourceResponse

router = APIRouter()


@router.get("/api/research/{research_id}/sources")
async def get_sources(research_id: str, db: AsyncSession = Depends(get_db_readonly)):
    try:
        research_uuid = UUID(research_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid research ID format")

    result = await db.execute(
        select(Source).where(Source.session_id == research_uuid)
    )
    sources = result.scalars().all()
    return SourceListResponse(
        sources=[
            SourceResponse(
                id=str(s.id),
                title=s.title,
                url=s.url,
                domain=s.domain,
                author=s.author,
                published_date=s.published_date,
                source_type=s.source_type,
                search_query=s.search_query,
                relevance_score=s.relevance_score,
                reliability_score=s.reliability_score,
                retrieved_at=s.retrieved_at,
            )
            for s in sources
        ],
        total=len(sources),
    )
