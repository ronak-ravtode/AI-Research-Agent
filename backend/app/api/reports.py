from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.database import get_db_readonly
from app.database.models import Report
from app.schemas.report import ReportResponse

router = APIRouter()


@router.get("/api/research/{research_id}/report")
async def get_report(research_id: str, db: AsyncSession = Depends(get_db_readonly)):
    try:
        research_uuid = UUID(research_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid research ID format")

    result = await db.execute(
        select(Report).where(Report.session_id == research_uuid)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportResponse(
        id=str(report.id),
        research_id=str(report.session_id),
        title=report.title,
        content=report.content,
        executive_summary=report.executive_summary,
        methodology=report.methodology,
        findings=report.findings,
        analysis=report.analysis,
        conclusion=report.conclusion,
        references=report.references,
        created_at=report.created_at,
    )
