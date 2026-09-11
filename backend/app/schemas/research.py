from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from typing import Literal


class StartResearchRequest(BaseModel):
    query: str = Field(..., min_length=10, max_length=2000)
    depth: Literal["quick", "standard", "deep"] = "standard"


class ResearchResponse(BaseModel):
    research_id: UUID
    status: str


class ResearchStatusResponse(BaseModel):
    research_id: UUID
    query: str
    status: str
    research_depth: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
