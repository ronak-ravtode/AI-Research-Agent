import pytest
from unittest.mock import patch, MagicMock
from app.tools.firecrawl_extract import FirecrawlExtract, ExtractedContent


@pytest.fixture
def firecrawl():
    with patch("app.tools.firecrawl_extract.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(FIRECRAWL_API_KEY="test-key")
        with patch("app.tools.firecrawl_extract.FirecrawlApp"):
            extract = FirecrawlExtract()
            extract._app = MagicMock()
            return extract


@pytest.mark.asyncio
async def test_extract_returns_content(firecrawl):
    firecrawl.app.scrape_url.return_value = {
        "metadata": {"title": "Test Page"},
        "markdown": "# Test content",
    }

    result = await firecrawl.extract_url("https://example.com")
    assert result.title == "Test Page"
    assert result.markdown == "# Test content"


@pytest.mark.asyncio
async def test_extract_handles_error(firecrawl):
    firecrawl.app.scrape_url.side_effect = Exception("API error")

    result = await firecrawl.extract_url("https://bad-url.com")
    assert "failed" in result.content.lower()
