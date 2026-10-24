from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HistoryItem(BaseModel):
    research_id: str
    query: str
    title: Optional[str] = None
    status: str
    parent_research_id: Optional[str] = None
    source_count: int = 0
    has_report: bool = False
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
