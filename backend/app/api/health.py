from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "agentic-research-assistant",
        "version": "0.1.0",
        "environment": settings.APP_ENV,
    }
