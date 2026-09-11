import pytest
from unittest.mock import AsyncMock, patch
from app.agents.conflict_detector import conflict_detector_agent
from app.agents.state import ResearchState

@pytest.mark.asyncio
async def test_conflict_detector_finds_conflicts():
    mock_result = {
        "conflicts": [
            {
                "topic": "Productivity improvement",
                "claim_a": {"text": "+30%", "source": "A", "value": "30%"},
                "claim_b": {"text": "+10%", "source": "B", "value": "10%"},
                "possible_explanation": "Different methodologies",
                "severity": "medium",
            }
        ]
    }

    with patch("app.agents.conflict_detector.llm_service") as mock_llm:
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
            verified_claims=[
                {"claim": "+30% productivity", "source_url": "https://a.com"},
                {"claim": "+10% productivity", "source_url": "https://b.com"},
            ],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=1,
            status="analyzing",
            errors=[],
        )

        result = await conflict_detector_agent(state)
        assert len(result["conflicts"]) == 1
        assert result["conflicts"][0]["topic"] == "Productivity improvement"


@pytest.mark.asyncio
async def test_conflict_detector_no_conflicts():
    mock_result = {"conflicts": []}

    with patch("app.agents.conflict_detector.llm_service") as mock_llm:
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
            verified_claims=[
                {"claim": "AI helps", "source_url": "https://a.com"},
                {"claim": "AI helps", "source_url": "https://b.com"},
            ],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=1,
            status="analyzing",
            errors=[],
        )

        result = await conflict_detector_agent(state)
        assert result["conflicts"] == []


@pytest.mark.asyncio
async def test_conflict_detector_insufficient_claims():
    state = ResearchState(
        research_id="test-id",
        user_query="Impact of AI",
        research_plan=[],
        current_task="",
        completed_tasks=[],
        search_queries=[],
        sources=[],
        evidence=[],
        verified_claims=[{"claim": "AI helps", "source_url": "https://a.com"}],
        conflicts=[],
        analysis="",
        citations=[],
        confidence_scores={},
        report={},
        iteration=1,
        status="analyzing",
        errors=[],
    )

    result = await conflict_detector_agent(state)
    assert result["conflicts"] == []
