from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db
from app.database.models import Report

router = APIRouter()


@router.get("/api/research/{research_id}/report")
async def get_report(research_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Report).where(Report.session_id == research_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        return {"error": "Report not found"}
    return {
        "id": str(report.id),
        "title": report.title,
        "content": report.content,
        "created_at": report.created_at.isoformat(),
    }
