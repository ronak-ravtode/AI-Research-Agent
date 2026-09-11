from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db
from app.database.models import Source

router = APIRouter()


@router.get("/api/research/{research_id}/sources")
async def get_sources(research_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Source).where(Source.session_id == research_id)
    )
    sources = result.scalars().all()
    return {
        "sources": [
            {
                "id": str(s.id),
                "title": s.title,
                "url": s.url,
                "relevance_score": s.relevance_score,
            }
            for s in sources
        ],
        "total": len(sources),
    }
