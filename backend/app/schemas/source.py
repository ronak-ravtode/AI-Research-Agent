from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SourceResponse(BaseModel):
    id: str
    title: str
    url: str
    domain: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    source_type: str = "unknown"
    search_query: Optional[str] = None
    relevance_score: float = 0.0
    reliability_score: float = 0.0
    retrieved_at: Optional[datetime] = None


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
    total: int
