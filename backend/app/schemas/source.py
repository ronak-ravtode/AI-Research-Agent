from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SourceResponse(BaseModel):
    id: str
    title: str
    url: str
    domain: Optional[str] = None
    source_type: str = "Web article"
    snippet: Optional[str] = None
    retrieval_method: str = "tavily_snippet"
    search_score: float = 0.0
    retrieved_at: Optional[datetime] = None


class SourceListResponse(BaseModel):
    sources: list[SourceResponse]
    total: int
