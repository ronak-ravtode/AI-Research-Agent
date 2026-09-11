import pytest
from unittest.mock import AsyncMock, patch
from app.agents.writer import writer_agent
from app.agents.state import ResearchState

@pytest.mark.asyncio
async def test_writer_generates_report():
    with patch("app.agents.writer.llm_service") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="# Research Report\n\n## Executive Summary\n...")

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[{"claim": "AI improves productivity", "verification_status": "supported"}],
            conflicts=[],
            analysis="AI generally improves productivity",
            citations=[{"citation_number": 1, "source_url": "https://a.com"}],
            confidence_scores={},
            report={},
            iteration=1,
            status="analyzing",
            errors=[],
        )

        result = await writer_agent(state)
        assert result["status"] == "writing"
        assert "title" in result["report"]
        assert "content" in result["report"]

@pytest.mark.asyncio
async def test_writer_includes_citations_in_report():
    with patch("app.agents.writer.llm_service") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="# Report\n\nContent here.")

        state = ResearchState(
            research_id="test-id",
            user_query="Climate change effects",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[{"claim": "Temperatures rising", "verification_status": "supported"}],
            conflicts=[{"topic": "Rate of change", "possible_explanation": "Different models used"}],
            analysis="Climate change is real",
            citations=[
                {"citation_number": 1, "source_url": "https://source1.com"},
                {"citation_number": 2, "source_url": "https://source2.com"},
            ],
            confidence_scores={},
            report={},
            iteration=1,
            status="analyzing",
            errors=[],
        )

        result = await writer_agent(state)
        assert result["status"] == "writing"
        assert result["report"]["citations"] == [
            {"citation_number": 1, "source_url": "https://source1.com"},
            {"citation_number": 2, "source_url": "https://source2.com"},
        ]
        mock_llm.generate.assert_called_once()

@pytest.mark.asyncio
async def test_writer_handles_empty_state():
    with patch("app.agents.writer.llm_service") as mock_llm:
        mock_llm.generate = AsyncMock(return_value="# Empty Report\n")

        state = ResearchState(
            research_id="test-id",
            user_query="Test query",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=0,
            status="analyzing",
            errors=[],
        )

        result = await writer_agent(state)
        assert result["status"] == "writing"
        assert "title" in result["report"]
        assert "content" in result["report"]
