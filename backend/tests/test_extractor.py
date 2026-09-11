import pytest
from unittest.mock import AsyncMock, patch
from app.agents.extractor import extractor_agent
from app.agents.state import ResearchState


@pytest.mark.asyncio
async def test_extractor_extracts_claims():
    mock_result = {
        "claims": [
            {
                "claim": "AI improves productivity",
                "evidence": "Study shows 30% improvement",
                "evidence_type": "statistical",
                "importance": 0.9,
            }
        ]
    }

    with patch("app.agents.extractor.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[{"id": "src-1", "title": "Study", "url": "https://example.com", "content": "x" * 200}],
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
        )

        result = await extractor_agent(state)
        assert len(result["evidence"]) == 1
        assert result["status"] == "extracting"


@pytest.mark.asyncio
async def test_extractor_skips_short_content():
    with patch("app.agents.extractor.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock()

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[{"id": "src-1", "title": "Short", "url": "https://example.com", "content": "short"}],
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
        )

        result = await extractor_agent(state)
        assert len(result["evidence"]) == 0
        mock_llm.structured_generate.assert_not_called()


@pytest.mark.asyncio
async def test_extractor_handles_llm_error():
    with patch("app.agents.extractor.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(side_effect=Exception("API error"))

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[{"id": "src-1", "title": "Study", "url": "https://example.com", "content": "x" * 200}],
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
        )

        result = await extractor_agent(state)
        assert len(result["evidence"]) == 0
        assert result["status"] == "extracting"


@pytest.mark.asyncio
async def test_extractor_multiple_sources():
    mock_result = {
        "claims": [
            {
                "claim": "AI improves productivity",
                "evidence": "Study shows 30% improvement",
                "evidence_type": "statistical",
                "importance": 0.9,
            }
        ]
    }

    with patch("app.agents.extractor.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[
                {"id": "src-1", "title": "Study 1", "url": "https://example.com", "content": "x" * 200},
                {"id": "src-2", "title": "Study 2", "url": "https://example2.com", "content": "y" * 200},
            ],
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
        )

        result = await extractor_agent(state)
        assert len(result["evidence"]) == 2
        assert result["status"] == "extracting"
