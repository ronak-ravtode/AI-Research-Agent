from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db_readonly
from app.database.models import (
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_QUEUED,
    STATUS_RUNNING,
    Report,
    ResearchSession,
    Source,
    normalize_status,
)
from app.schemas.report import HistoryItem
from app.schemas.source import (
    SourceDetailResponse,
    SourceListResponse,
    SourceResponse,
)

router = APIRouter()

DEFAULT_HISTORY_LIMIT = 20
MAX_HISTORY_LIMIT = 100
VALID_STATUSES = {
    STATUS_QUEUED,
    STATUS_RUNNING,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_CANCELLED,
}


def _parse_uuid(research_id: str) -> UUID:
    try:
        return UUID(research_id)
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid research ID format")


def _source_response(source: Source) -> SourceResponse:
    return SourceResponse(
        id=str(source.id),
        title=source.title,
        url=source.url,
        domain=source.domain,
        source_type=source.source_type,
        snippet=source.snippet,
        retrieval_method=source.retrieval_method,
        search_score=source.search_score,
        retrieved_at=source.retrieved_at,
    )


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
            .order_by(Source.created_at.asc(), Source.id.asc())
        )
    ).scalars().all()

    return SourceListResponse(
        sources=[_source_response(s) for s in rows],
        total=len(rows),
    )


@router.get(
    "/api/research/{research_id}/sources/{source_id}",
    response_model=SourceDetailResponse,
)
async def get_source(
    research_id: str,
    source_id: str,
    db: AsyncSession = Depends(get_db_readonly),
):
    """One source with its full extracted text, plus its citation number.

    The list endpoint deliberately omits `content` (it can be a whole page per row);
    the reader view is the only place that needs it.
    """
    research_uuid = _parse_uuid(research_id)
    source_uuid = _parse_uuid(source_id)

    source = (
        await db.execute(
            select(Source).where(
                Source.id == source_uuid, Source.session_id == research_uuid
            )
        )
    ).scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    ordered_ids = (
        await db.execute(
            select(Source.id)
            .where(Source.session_id == research_uuid)
            .order_by(Source.created_at.asc(), Source.id.asc())
        )
    ).scalars().all()

    try:
        index = ordered_ids.index(source_uuid) + 1
    except ValueError:
        index = 1

    return SourceDetailResponse(
        **_source_response(source).model_dump(),
        content=source.content,
        index=index,
        total=len(ordered_ids),
    )


@router.get("/api/history")
async def get_history(
    db: AsyncSession = Depends(get_db_readonly),
    limit: int = Query(DEFAULT_HISTORY_LIMIT, ge=1, le=MAX_HISTORY_LIMIT),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, max_length=200),
):
    """Recent sessions, newest first, with source and report counts resolved in one query.

    Supports the sidebar (first page) and the library (paging, status filter, search).
    Both counts come from a single grouped join rather than a query per session.
    """
    filters = []
    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="Unknown status filter")
        filters.append(ResearchSession.status == status)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                ResearchSession.query.ilike(pattern),
                ResearchSession.display_title.ilike(pattern),
            )
        )

    total = int(
        (
            await db.execute(
                select(func.count())
                .select_from(ResearchSession)
                .where(*filters)
            )
        ).scalar_one()
    )

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
            .where(*filters)
            .order_by(ResearchSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).all()

    return {
        "history": [
            HistoryItem(
                research_id=str(session.id),
                query=session.query,
                title=session.display_title or session.query,
                status=normalize_status(session.status),
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
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(rows) < total,
    }
