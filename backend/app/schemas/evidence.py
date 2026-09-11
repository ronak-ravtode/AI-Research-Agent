from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class EvidenceResponse(BaseModel):
    id: UUID
    source_id: UUID
    claim: str
    evidence_text: str
    evidence_type: str
    confidence_score: float
    verification_status: Optional[str] = None
    created_at: datetime


class EvidenceListResponse(BaseModel):
    evidence: list[EvidenceResponse]
    total: int
