import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.tools.tavily_search import TavilySearch, SearchResult


@pytest.fixture
def tavily():
    with patch("app.tools.tavily_search.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(TAVILY_API_KEY="test-key")
        with patch("app.tools.tavily_search.AsyncTavilyClient"):
            search = TavilySearch()
            search.client = AsyncMock()
            return search


@pytest.mark.asyncio
async def test_search_returns_results(tavily):
    tavily.client.search = AsyncMock(return_value={
        "results": [
            {"title": "Test", "url": "https://example.com", "content": "Content", "score": 0.9}
        ]
    })

    results = await tavily.search_web("test query")
    assert len(results) == 1
    assert results[0].title == "Test"
    assert results[0].domain == "example.com"


@pytest.mark.asyncio
async def test_search_empty_results(tavily):
    tavily.client.search = AsyncMock(return_value={"results": []})
    results = await tavily.search_web("no results")
    assert len(results) == 0
