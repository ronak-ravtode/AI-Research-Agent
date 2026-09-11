from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db
from app.database.models import ResearchSession

router = APIRouter()


@router.get("/api/history")
async def get_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResearchSession).order_by(ResearchSession.created_at.desc()).limit(50)
    )
    sessions = result.scalars().all()
    return {
        "history": [
            {
                "research_id": str(s.id),
                "query": s.query,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in sessions
        ]
    }
