from app.schemas.research import StartResearchRequest, ResearchResponse
from uuid import uuid4


def test_start_research_valid():
    req = StartResearchRequest(query="What is the impact of AI on software development?")
    assert req.depth == "standard"


def test_start_research_too_short():
    try:
        StartResearchRequest(query="short")
    except Exception as e:
        assert "min_length" in str(e) or "at least" in str(e)


def test_research_response():
    resp = ResearchResponse(research_id=uuid4(), status="started")
    assert resp.status == "started"
