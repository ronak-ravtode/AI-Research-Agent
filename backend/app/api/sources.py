from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db_readonly
from app.database.models import Report, ResearchSession, Source
from app.schemas.report import HistoryItem
from app.schemas.source import SourceListResponse, SourceResponse

router = APIRouter()

HISTORY_LIMIT = 50


def _parse_uuid(research_id: str) -> UUID:
    try:
        return UUID(research_id)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid research ID format")


@router.get("/api/research/{research_id}/sources")
async def get_sources(
    research_id: str,
    db: AsyncSession = Depends(get_db_readonly),
):
    research_uuid = _parse_uuid(research_id)
    rows = (
        await db.execute(
            select(Source)
            .where(Source.session_id == research_uuid)
            .order_by(Source.created_at.asc())
        )
    ).scalars().all()

    return SourceListResponse(
        sources=[
            SourceResponse(
                id=str(s.id),
                title=s.title,
                url=s.url,
                domain=s.domain,
                source_type=s.source_type,
                snippet=s.snippet,
                retrieval_method=s.retrieval_method,
                search_score=s.search_score,
                retrieved_at=s.retrieved_at,
            )
            for s in rows
        ],
        total=len(rows),
    )


@router.get("/api/history")
async def get_history(db: AsyncSession = Depends(get_db_readonly)):
    """Recent sessions, newest first, with source and report counts resolved in one query.

    The previous implementation ran a COUNT per session inside a loop; both counts here
    come from a single grouped join instead.
    """
    source_counts = (
        select(
            Source.session_id.label("sid"),
            func.count(Source.id).label("source_count"),
        )
        .group_by(Source.session_id)
        .subquery()
    )
    report_counts = (
        select(
            Report.session_id.label("rid"),
            func.count(Report.id).label("report_count"),
        )
        .group_by(Report.session_id)
        .subquery()
    )

    rows = (
        await db.execute(
            select(
                ResearchSession,
                func.coalesce(source_counts.c.source_count, 0),
                func.coalesce(report_counts.c.report_count, 0),
            )
            .select_from(ResearchSession)
            .outerjoin(source_counts, source_counts.c.sid == ResearchSession.id)
            .outerjoin(report_counts, report_counts.c.rid == ResearchSession.id)
            .order_by(ResearchSession.created_at.desc())
            .limit(HISTORY_LIMIT)
        )
    ).all()

    return {
        "history": [
            HistoryItem(
                research_id=str(session.id),
                query=session.query,
                status=session.status,
                parent_research_id=(
                    str(session.parent_session_id)
                    if session.parent_session_id
                    else None
                ),
                source_count=int(source_count),
                has_report=bool(report_count),
                created_at=session.created_at,
                completed_at=session.completed_at,
            ).model_dump()
            for session, source_count, report_count in rows
        ]
    }
