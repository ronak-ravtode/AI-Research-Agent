from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ReportResponse(BaseModel):
    id: UUID
    research_id: UUID
    title: str
    executive_summary: Optional[str] = None
    methodology: Optional[str] = None
    findings: Optional[str] = None
    analysis: Optional[str] = None
    conclusion: Optional[str] = None
    references: Optional[str] = None
    created_at: datetime


class HistoryItem(BaseModel):
    research_id: UUID
    query: str
    status: str
    source_count: int = 0
    completed_at: Optional[datetime] = None
    created_at: datetime
