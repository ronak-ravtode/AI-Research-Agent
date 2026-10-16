"""Tests for the automatic database schema synchronization."""

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.database.database import Base
from app.database.migrations import (
    _render_default,
    _render_type,
    plan_changes,
    sync_schema,
)
import app.database.models  # noqa: F401


def test_render_default_variants():
    col_no_default = Column("a", Integer)
    assert _render_default(col_no_default) is None

    col_callable = Column("b", Integer, default=lambda: 42)
    assert _render_default(col_callable) is None

    col_bool = Column("c", Integer, default=True)
    assert _render_default(col_bool) == "true"

    col_int = Column("d", Integer, default=100)
    assert _render_default(col_int) == "100"

    col_str = Column("e", String, default="test'value")
    assert _render_default(col_str) == "'test''value'"


def test_render_type_emits_postgres_dialect():
    col = Column("s", String(120))
    rendered = _render_type(col)
    assert rendered == "VARCHAR(120)"


@pytest.mark.asyncio
async def test_sync_schema_on_empty_database_creates_tables():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    try:
        async with engine.begin() as conn:
            applied = await sync_schema(conn)

        assert any("created table research_sessions" in a for a in applied)
        assert any("created table sources" in a for a in applied)
        assert any("created table reports" in a for a in applied)
        assert any("created table research_activity" in a for a in applied)

        # Idempotency check: second run should make no changes
        async with engine.begin() as conn:
            applied_second = await sync_schema(conn)
        assert applied_second == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_plan_changes_detects_missing_column():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    try:
        async with engine.begin() as conn:
            # Create research_sessions table with only id and query
            await conn.execute(
                text("CREATE TABLE research_sessions (id VARCHAR(36) PRIMARY KEY, query TEXT)")
            )
            changes = await plan_changes(conn)

        # Should plan to add the missing columns
        added_statements = [c.statement for c in changes if c.table == "research_sessions"]
        assert any('ADD COLUMN "current_stage"' in s for s in added_statements)
        assert any('ADD COLUMN "status"' in s for s in added_statements)
    finally:
        await engine.dispose()
