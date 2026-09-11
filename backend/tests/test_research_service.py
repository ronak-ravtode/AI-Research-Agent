import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.research import ResearchService


@pytest.mark.asyncio
async def test_research_service_initializes():
    mock_db = AsyncMock()
    service = ResearchService(mock_db)
    assert service.db == mock_db


@pytest.mark.asyncio
async def test_start_research_creates_session():
    mock_db = AsyncMock()
    service = ResearchService(mock_db)

    mock_planner = AsyncMock(return_value={
        "research_plan": [{"id": 1, "task": "Test task", "priority": "high"}],
        "status": "planning",
    })
    mock_researcher = AsyncMock(return_value={
        "sources": [{"title": "Src", "url": "http://example.com", "content": "content", "relevance_score": 0.8}],
        "search_queries": ["test query"],
        "status": "researching",
    })
    mock_extractor = AsyncMock(return_value={
        "evidence": [{"source_id": None, "source_url": "http://example.com", "claim": "claim", "evidence_text": "text", "evidence_type": "factual", "confidence_score": 0.7}],
        "status": "extracting",
    })
    mock_verifier = AsyncMock(return_value={
        "verified_claims": [{"claim": "claim", "source_url": "http://example.com", "verification_status": "supported", "confidence": 0.9}],
        "status": "verifying",
    })
    mock_sufficiency = AsyncMock(return_value={"status": "verifying"})
    mock_analyst = AsyncMock(return_value={"analysis": "Conclusion", "status": "analyzing"})
    mock_conflict = AsyncMock(return_value={"conflicts": [], "status": "analyzing"})
    mock_writer = AsyncMock(return_value={
        "report": {"title": "Test Report", "content": "Report content"},
        "status": "writing",
    })

    with patch("app.services.research.planner_agent", mock_planner), \
         patch("app.services.research.researcher_agent", mock_researcher), \
         patch("app.services.research.extractor_agent", mock_extractor), \
         patch("app.services.research.verifier_agent", mock_verifier), \
         patch("app.services.research.sufficiency_agent", mock_sufficiency), \
         patch("app.services.research.analyst_agent", mock_analyst), \
         patch("app.services.research.conflict_detector_agent", mock_conflict), \
         patch("app.services.research.writer_agent", mock_writer):

        result = await service.start_research("What is AI?")

    assert result is not None
    assert isinstance(result, str)
    mock_db.add.assert_called()
    mock_db.flush.assert_called()
