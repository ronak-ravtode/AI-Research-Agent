from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/api/health")
async def health_check():
    missing = settings.missing_required_keys()
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        # Non-secret identity of what actually runs this deployment, so the UI never has
        # to hardcode provider names that drift from the configuration.
        "providers": {
            "llm": settings.GROQ_MODEL,
            "search": "tavily",
            "extraction": "firecrawl",
        },
        "limits": {
            "max_agent_iterations": settings.MAX_AGENT_ITERATIONS,
            "max_search_results": settings.MAX_SEARCH_RESULTS,
            "max_extract_sources": settings.MAX_EXTRACT_SOURCES,
        },
        "configured": not missing,
    }
