from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

class StartResearchRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    query: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="The research question. Must be at least 10 characters.",
    )


class ResearchResponse(BaseModel):
    research_id: str
    status: str


class ResearchStatusResponse(BaseModel):
    research_id: str
    query: str
    status: Literal["queued", "running", "completed", "failed"]
    current_stage: Optional[str] = None
    progress_message: Optional[str] = None
    error_message: Optional[str] = None
    report_id: Optional[str] = None
    report_title: Optional[str] = None
    report_markdown: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
