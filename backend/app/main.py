from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, research, sources
from app.core.config import get_settings
from app.core.logging import logger
from app.database.database import Base, _get_engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting ai-research-assistant",
        data={
            "env": settings.APP_ENV,
            "missing_config": settings.missing_required_keys(),
        },
    )

    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ready")

    yield

    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title="AI Research Assistant",
    description="Web research with cited sources.",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [settings.FRONTEND_URL]
if settings.APP_ENV == "development":
    origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(research.router)
app.include_router(sources.router)
