from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EvidenceResponse(BaseModel):
    id: str
    session_id: str
    task_id: str
    source_id: str
    claim: str
    evidence_text: str
    evidence_type: str = "factual"
    verification_status: Optional[str] = None
    confidence_score: float = 0.0
    created_at: Optional[datetime] = None


class EvidenceListResponse(BaseModel):
    evidence: list[EvidenceResponse]
    total: int
