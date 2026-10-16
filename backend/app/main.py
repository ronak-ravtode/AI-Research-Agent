import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

# Imported from starlette rather than `fastapi.middleware.cors`: that path is a
# one-line re-export shim in FastAPI 0.141, and under this app's import order it fails
# with `cannot import name 'CORSMiddleware'`. starlette is where the class is defined,
# so importing it directly is both correct and immune to the shim.
from starlette.middleware.cors import CORSMiddleware

from app.api import health, research, sources
from app.core.config import get_settings
from app.core.logging import logger
from app.database.database import Base, _get_engine
from app.database.migrations import sync_schema

settings = get_settings()

STARTUP_HELP = """
Could not reach the database.

  host in DATABASE_URL : {host}

Check, in order:
  1. backend/.env has a DATABASE_URL for a database that actually exists.
  2. The password is URL-encoded ('#' becomes '%23').
  3. You are connected to the internet (cloud databases need it).
  4. If you are on IPv4-only, use the Supabase *pooler* host
     (aws-0-<region>.pooler.supabase.com) instead of db.<ref>.supabase.co.

For a quick local run, point it at a local PostgreSQL:
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    missing = settings.missing_required_keys()
    logger.info(
        "Starting ai-research-assistant",
        data={
            "env": settings.APP_ENV,
            "missing_config": missing,
            "database_host": settings.DATABASE_URL.split("@")[-1].split("/")[0]
            if settings.DATABASE_URL
            else "(unset)",
        },
    )
    if missing:
        logger.warning(
            "Missing configuration; research runs will fail until this is fixed",
            data={"missing": missing},
        )

    engine = _get_engine()
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            # create_all only creates missing tables; sync_schema also adds columns an
            # older deployment is missing and fixes naive timestamp types.
            applied = await sync_schema(conn)
    except Exception as exc:
        # An unreachable database is a configuration mistake, not a crash to debug
        # through a stack trace. Say what to check, then stop.
        host = settings.DATABASE_URL.split("@")[-1].split("/")[0] or "(unset)"
        print(STARTUP_HELP.format(host=host), file=sys.stderr)
        logger.error(
            "Database unreachable at startup",
            data={"host": host, "error": type(exc).__name__},
        )
        await engine.dispose()
        # `from None` suppresses the chained traceback: the actionable message above is
        # the useful output, and the raw driver stack trace only buries it.
        raise SystemExit(1) from None

    if applied:
        logger.info("Applied schema changes", data={"changes": applied})
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
