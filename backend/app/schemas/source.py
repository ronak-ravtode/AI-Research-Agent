from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SourceResponse(BaseModel):
    id: UUID
    title: str
    url: str
    domain: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    source_type: str
    relevance_score: float
    reliability_score: float
    retrieved_at: datetime


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
    total: int
