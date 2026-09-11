from typing import TypedDict, Annotated, Optional
from uuid import UUID
import operator


class ResearchState(TypedDict):
    """State definition for the research agent workflow."""
    research_id: str
    user_query: str
    research_plan: list
    current_task: str
    completed_tasks: Annotated[list, operator.add]
    search_queries: Annotated[list, operator.add]
    sources: Annotated[list, operator.add]
    evidence: Annotated[list, operator.add]
    verified_claims: Annotated[list, operator.add]
    conflicts: Annotated[list, operator.add]
    analysis: str
    citations: Annotated[list, operator.add]
    confidence_scores: dict
    report: dict
    iteration: int
    status: str
    errors: Annotated[list, operator.add]
