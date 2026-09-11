import pytest
from app.core.config import Settings


@pytest.fixture
def test_settings():
    return Settings(
        GROQ_API_KEY="test-key",
        TAVILY_API_KEY="test-key",
        FIRECRAWL_API_KEY="test-key",
        DATABASE_URL="sqlite+aiosqlite:///test.db",
    )
