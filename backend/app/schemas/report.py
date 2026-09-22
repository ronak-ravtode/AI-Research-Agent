from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportResponse(BaseModel):
    id: str
    research_id: str
    title: str
    content: str
    executive_summary: Optional[str] = None
    methodology: Optional[str] = None
    findings: Optional[str] = None
    analysis: Optional[str] = None
    conclusion: Optional[str] = None
    references: Optional[str] = None
    created_at: Optional[datetime] = None


class HistoryItem(BaseModel):
    research_id: str
    query: str
    status: str
    research_depth: str = "standard"
    source_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
