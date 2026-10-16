import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.database import Base
from app.database.models import ResearchSession


@pytest_asyncio.fixture
async def db_session():
    """An isolated in-memory database carrying the real schema.

    The models use the cross-dialect `Uuid` type, so this SQLite connection compiles the
    same columns PostgreSQL will create. That keeps the tests honest about the production
    schema without needing a live database.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()


@pytest.fixture
def sample_session():
    return ResearchSession(query="What are the main risks of generative AI?")
