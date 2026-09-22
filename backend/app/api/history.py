from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.database import get_db_readonly
from app.database.models import ResearchSession, Source
from app.schemas.report import HistoryItem

router = APIRouter()


@router.get("/api/history")
async def get_history(db: AsyncSession = Depends(get_db_readonly)):
    result = await db.execute(
        select(ResearchSession).order_by(ResearchSession.created_at.desc()).limit(50)
    )
    sessions = result.scalars().all()

    history = []
    for s in sessions:
        source_count_result = await db.execute(
            select(func.count(Source.id)).where(Source.session_id == s.id)
        )
        source_count = source_count_result.scalar() or 0

        history.append(HistoryItem(
            research_id=str(s.id),
            query=s.query,
            status=s.status.value if hasattr(s.status, "value") else s.status,
            research_depth=s.research_depth,
            source_count=source_count,
            started_at=s.started_at,
            completed_at=s.completed_at,
            created_at=s.created_at,
        ))
    return {"history": [h.model_dump() for h in history]}
