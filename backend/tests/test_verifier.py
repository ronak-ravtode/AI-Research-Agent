import pytest
from unittest.mock import AsyncMock, patch
from app.agents.verifier import verifier_agent
from app.agents.state import ResearchState

@pytest.mark.asyncio
async def test_verifier_verifies_claims():
    mock_result = {
        "verified_claims": [
            {
                "claim": "AI improves productivity",
                "verification_status": "supported",
                "confidence": 0.9,
                "reason": "Study directly supports",
            }
        ]
    }

    with patch("app.agents.verifier.llm_service") as mock_llm:
        mock_llm.structured_generate = AsyncMock(return_value=mock_result)

        state = ResearchState(
            research_id="test-id",
            user_query="Impact of AI",
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[{"claim": "AI improves productivity", "evidence_text": "30% improvement", "source_url": "https://example.com"}],
            verified_claims=[],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=0,
            status="extracting",
            errors=[],
        )

        result = await verifier_agent(state)
        assert len(result["verified_claims"]) == 1
        assert result["verified_claims"][0]["verification_status"] == "supported"