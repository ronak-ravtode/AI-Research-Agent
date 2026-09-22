from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.database.database import _get_engine, Base
from app.api import health, research, reports, sources, history
from app.core.logging import logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting agentic-research-assistant", data={"env": settings.APP_ENV})

    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified")

    yield

    logger.info("Shutting down agentic-research-assistant")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

origins = [settings.FRONTEND_URL]
if settings.APP_ENV == "development":
    origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(research.router)
app.include_router(reports.router)
app.include_router(sources.router)
app.include_router(history.router)
