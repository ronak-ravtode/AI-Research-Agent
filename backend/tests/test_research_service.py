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

    mock_final_state = {
        "research_id": "test-id",
        "user_query": "What is AI?",
        "research_plan": [{"id": 1, "task": "Test task", "priority": "high"}],
        "sources": [{"title": "Src", "url": "http://example.com", "content": "content", "relevance_score": 0.8, "source_type": "unknown", "domain": "example.com"}],
        "evidence": [{"source_url": "http://example.com", "claim": "claim", "evidence_text": "text", "evidence_type": "factual", "confidence_score": 0.7}],
        "verified_claims": [{"claim": "claim", "source_url": "http://example.com", "verification_status": "supported", "confidence": 0.9}],
        "conflicts": [],
        "analysis": "Conclusion",
        "citations": [],
        "confidence_scores": {"overall": 0.85, "summary": {"total": 1, "supported": 1}},
        "report": {"title": "Test Report", "content": "Report content"},
        "completed_tasks": [1],
        "search_queries": ["test query"],
        "iteration": 1,
        "status": "completed",
        "errors": [],
        "current_task": "",
        "research_depth": "standard",
    }

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(return_value=mock_final_state)

    # Mock db.execute to return None for the session lookup (so it creates a new one)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.services.research.create_research_graph", return_value=mock_graph):
        result = await service.start_research("What is AI?")

    assert result is not None
    assert isinstance(result, str)
    mock_db.add.assert_called()
    mock_db.flush.assert_called()
