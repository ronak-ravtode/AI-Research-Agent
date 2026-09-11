import pytest
from unittest.mock import AsyncMock, patch
from app.agents.planner import planner_agent
from app.agents.state import ResearchState

@pytest.mark.asyncio
async def test_planner_returns_plan():
    mock_plan = {
        "research_objective": "Test objective",
        "subtasks": [
            {"id": 1, "task": "Find studies", "priority": "high"},
            {"id": 2, "task": "Find surveys", "priority": "medium"},
        ],
    }

    with patch("app.agents.planner.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_plan)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI on development",
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
            status="planning",
            errors=[],
        )

        result = await planner_agent(state)
        assert len(result["research_plan"]) == 2
        assert result["status"] == "planning"
