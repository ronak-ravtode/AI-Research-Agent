import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.researcher import researcher_agent
from app.agents.state import ResearchState
from app.tools.tavily_search import SearchResult

@pytest.mark.asyncio
async def test_researcher_searches_and_returns_sources():
    mock_results = [
        SearchResult(title="Study 1", url="https://arxiv.org/paper", content="Content", score=0.9),
        SearchResult(title="Blog 1", url="https://blog.example.com/post", content="Content", score=0.6),
    ]

    with patch("app.agents.researcher.llm_service") as mock_llm, \
         patch("app.agents.researcher.tavily_search") as mock_tavily:
        mock_llm.generate = AsyncMock(return_value="AI productivity study 2026")
        mock_tavily.search_web = AsyncMock(return_value=mock_results)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[{"id": 1, "task": "Find studies", "priority": "high"}],
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

        result = await researcher_agent(state)
        assert len(result["sources"]) == 2
        assert result["status"] == "researching"