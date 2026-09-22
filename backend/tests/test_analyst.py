import pytest
from unittest.mock import AsyncMock, patch
from app.agents.analyst import sufficiency_agent, analyst_agent
from app.agents.state import ResearchState

@pytest.mark.asyncio
async def test_sufficiency_returns_when_max_iterations():
    state = ResearchState(
        research_id="test-id",
        user_query="test",
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
        iteration=5,
        status="verifying",
        errors=[],
        research_depth="quick",
    )

    result = await sufficiency_agent(state)
    assert result["status"] == "analyzing"

@pytest.mark.asyncio
async def test_sufficiency_calls_llm_when_under_max():
    mock_result = {
        "sufficient": False,
        "reason": "Need more sources",
        "next_searches": ["AI productivity 2024"],
    }

    with patch("app.agents.analyst.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
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
            status="researching",
            errors=[],
            research_depth="standard",
        )

        result = await sufficiency_agent(state)
        assert result["status"] == "researching"
        assert "AI productivity 2024" in result["search_queries"]
        assert result["iteration"] == 1

@pytest.mark.asyncio
async def test_sufficiency_returns_verifying_when_sufficient():
    mock_result = {
        "sufficient": True,
        "reason": "Enough evidence collected",
        "next_searches": [],
    }

    with patch("app.agents.analyst.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
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
            status="researching",
            errors=[],
            research_depth="standard",
        )

        result = await sufficiency_agent(state)
        assert result["status"] == "analyzing"

@pytest.mark.asyncio
async def test_analyst_returns_analysis():
    mock_result = {
        "key_findings": ["Finding 1"],
        "conclusion": "AI generally improves productivity",
    }

    with patch("app.agents.analyst.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

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
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=1,
            status="verifying",
            errors=[],
        )

        result = await analyst_agent(state)
        assert result["status"] == "analyzing"
        assert len(result["analysis"]) > 0
