from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

REQUIRED_KEYS = ("GROQ_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY", "DATABASE_URL")


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    APP_NAME: str = "ai-research-assistant"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    TAVILY_API_KEY: str = ""
    FIRECRAWL_API_KEY: str = ""

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DATABASE_URL: str = ""

    FRONTEND_URL: str = "http://localhost:3000"

    # Request timeouts, in seconds.
    SEARCH_TIMEOUT: float = 30.0
    SCRAPE_TIMEOUT: float = 45.0
    LLM_TIMEOUT: float = 90.0

    # Hard bounds so a single run cannot grow without limit.
    MAX_SEARCH_QUERIES: int = 4
    MAX_SEARCH_RESULTS: int = 8
    MAX_EXTRACT_SOURCES: int = 5
    MAX_SOURCE_CHARS: int = 6000
    MAX_TOTAL_SOURCE_CHARS: int = 20000

    def missing_required_keys(self) -> list[str]:
        """Names of required keys that are still blank. Logged, never returned to a client."""
        return [name for name in REQUIRED_KEYS if not getattr(self, name, "").strip()]

    def validate_required_keys(self) -> None:
        from app.core.exceptions import ConfigurationError

        missing = self.missing_required_keys()
        if missing:
            raise ConfigurationError(detail=f"missing settings: {', '.join(missing)}")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
