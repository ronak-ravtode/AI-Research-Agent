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
    parent_research_id: Optional[str] = Field(
        default=None,
        description="A completed research session this question follows up on.",
    )
    max_iterations: Optional[int] = Field(
        default=None,
        ge=0,
        le=3,
        description=(
            "How many evidence-gap follow-up rounds the agent may run. "
            "0 = quick, 2 = standard (server default), 3 = deep."
        ),
    )


class ResearchResponse(BaseModel):
    research_id: str
    status: str


class ResearchStatusResponse(BaseModel):
    research_id: str
    query: str
    display_title: Optional[str] = None
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    current_stage: Optional[str] = None
    progress_message: Optional[str] = None
    error_message: Optional[str] = None
    parent_research_id: Optional[str] = None
    planned_queries: list[str] = Field(default_factory=list)
    report_id: Optional[str] = None
    report_title: Optional[str] = None
    report_markdown: Optional[str] = None
    verification_note: Optional[str] = None
    verification_revised: bool = False
    verification_available: bool = True
    removed_claims: int = 0
    max_iterations: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class RenameResearchRequest(BaseModel):
    model_config = {"str_strip_whitespace": True}

    title: Optional[str] = Field(
        default=None,
        max_length=300,
        description="A display name for the run. Null or empty restores the question.",
    )
