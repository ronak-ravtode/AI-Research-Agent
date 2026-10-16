from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

_engine = None
_async_session_factory = None


def _normalize_db_url(url: str) -> str:
    """Convert sync PostgreSQL URLs to async (asyncpg)."""
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


def _connect_args(db_url: str) -> dict:
    """SSL settings for asyncpg.

    asyncpg does not read `?sslmode=` from the URL the way psycopg2 does, so a hosted
    database that requires TLS (Supabase does) would otherwise negotiate without it.
    An explicit `?sslmode=require` is honoured, and any Supabase host gets SSL anyway.
    """
    host = db_url.split("@")[-1].split("/")[0].split(":")[0].lower()
    query = db_url.partition("?")[2].lower()
    if "sslmode=disable" in query:
        return {}
    if "supabase" in host or "sslmode=require" in query:
        return {"ssl": "require"}
    return {}


def _get_engine():
    global _engine
    if _engine is None:
        db_url = _normalize_db_url(settings.DATABASE_URL)
        _engine = create_async_engine(
            db_url,
            echo=settings.APP_ENV == "development",
            # Fail fast instead of hanging a request on an unreachable cloud database.
            connect_args={**_connect_args(db_url), "timeout": 10, "command_timeout": 30},
        )
    return _engine


def _get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_factory


class Base(DeclarativeBase):
    pass


async def get_db():
    """Read-write session — auto-commits on success, rolls back on error."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_readonly():
    """Read-only session — never commits."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        yield session
