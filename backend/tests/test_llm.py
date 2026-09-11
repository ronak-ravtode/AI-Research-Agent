import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm import LLMService

@pytest.fixture
def llm_service():
    with patch("app.services.llm.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(GROQ_API_KEY="test", GROQ_MODEL="test-model")
        with patch("app.services.llm.AsyncGroq"):
            service = LLMService()
            service.client = AsyncMock()
            return service

@pytest.mark.asyncio
async def test_generate_returns_text(llm_service):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Hello world"))]
    llm_service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await llm_service.generate("Test prompt")
    assert result == "Hello world"

@pytest.mark.asyncio
async def test_structured_generate_returns_dict(llm_service):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content='{"key": "value"}'))]
    llm_service.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await llm_service.structured_generate("Test prompt")
    assert result == {"key": "value"}