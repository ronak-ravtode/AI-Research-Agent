"""Bring an existing database up to the models' schema, without destroying data.

`Base.metadata.create_all` only creates tables that do not exist. It never adds a column
to a table that is already there, so an older deployment keeps its old shape and the
application fails at the first INSERT with `column ... does not exist`.

This module performs that missing step. It is deliberately narrow and idempotent:

* missing tables are created,
* missing columns are added, carrying a server-side default when the model has one,
* timestamp columns are converted to `timestamptz` when the model expects an aware
  datetime and the database has a naive one,
* obsolete tables are only dropped when `drop_obsolete=True` is passed explicitly.

Nothing here deletes rows.
"""

import logging
from dataclasses import dataclass

from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncConnection

from app.database.database import Base

log = logging.getLogger("agentic-research-assistant.schema")

# PostgreSQL is the only supported target, and rendering with an explicit dialect is what
# makes `Uuid` and `DateTime(timezone=True)` emit UUID and TIMESTAMPTZ.
PG = postgresql.dialect()


def _collect_schema(sync_conn) -> tuple[set[str], dict[str, dict]]:
    """Read the live table and column names.

    Introspection must happen inside `run_sync`: the inspector returned by `inspect()` is a
    synchronous object, so awaiting one of its methods outside the greenlet raises
    MissingGreenlet.
    """
    inspector = inspect(sync_conn)
    tables = set(inspector.get_table_names())
    columns = {
        name: {c["name"]: c for c in inspector.get_columns(name)} for name in tables
    }
    return tables, columns


@dataclass
class Change:
    table: str
    statement: str


def _render_type(column) -> str:
    """PostgreSQL type for a mapped column, e.g. `VARCHAR(500)` or `TIMESTAMPTZ`."""
    return column.type.compile(dialect=PG)


def _render_default(column) -> str | None:
    """Server-side default for a column, if the model declares one."""
    default = column.default
    if default is None or getattr(default, "is_callable", False):
        # A Python-side callable (e.g. uuid4, lambda: utcnow) cannot be rendered as a
        # server default; the application always supplies the value instead.
        return None
    value = getattr(default, "arg", None)
    if callable(value):
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return None


async def plan_changes(conn: AsyncConnection) -> list[Change]:
    """Work out every statement needed, without executing anything."""
    changes: list[Change] = []
    existing_tables, columns_by_table = await conn.run_sync(_collect_schema)

    wanted_tables = set(Base.metadata.tables)

    for name in sorted(wanted_tables - existing_tables):
        # create_all handles these; recorded so the summary is complete.
        changes.append(Change(name, f"CREATE TABLE {name}"))

    for table_name in sorted(wanted_tables & existing_tables):
        table = Base.metadata.tables[table_name]
        present = columns_by_table.get(table_name, {})

        for column in table.columns:
            if column.name not in present:
                statement = (
                    f'ALTER TABLE {table_name} ADD COLUMN "{column.name}" '
                    f"{_render_type(column)}"
                )
                server_default = _render_default(column)
                if server_default is not None:
                    statement += f" DEFAULT {server_default}"
                changes.append(Change(table_name, statement))
                continue

            # A naive timestamp column rejects the aware datetimes the app writes.
            existing = present[column.name]
            wants_tz = bool(getattr(column.type, "timezone", False))
            existing_type = existing.get("type")
            existing_has_tz = bool(getattr(existing_type, "timezone", False)) or (
                "WITH TIME ZONE" in str(existing_type).upper()
            )
            is_timestamp = str(existing_type).upper().startswith("TIMESTAMP")
            if wants_tz and is_timestamp and not existing_has_tz:
                changes.append(
                    Change(
                        table_name,
                        f'ALTER TABLE {table_name} ALTER COLUMN "{column.name}" '
                        f"TYPE TIMESTAMP WITH TIME ZONE",
                    )
                )

        # Legacy columns not in the current model that have NOT NULL will cause INSERTs
        # to fail because the application no longer supplies values for them.
        # Dropping the NOT NULL constraint makes them nullable so writes succeed.
        model_column_names = set(table.columns.keys())
        for col_name, col_info in present.items():
            if col_name not in model_column_names and not col_info.get("nullable", True):
                changes.append(
                    Change(
                        table_name,
                        f'ALTER TABLE {table_name} ALTER COLUMN "{col_name}" DROP NOT NULL',
                    )
                )

    return changes


async def apply_changes(conn: AsyncConnection, changes: list[Change]) -> None:
    for change in changes:
        if change.statement.startswith("CREATE TABLE"):
            continue  # create_all already did this
        if conn.dialect.name == "sqlite" and "ALTER COLUMN" in change.statement:
            continue
        await conn.execute(text(change.statement))


async def sync_schema(conn: AsyncConnection, drop_obsolete: bool = False) -> list[str]:
    """Create tables, add missing columns and fix timestamp types.

    Returns a short list of the changes applied, for the startup log.
    """
    changes = await plan_changes(conn)

    created = [c.table for c in changes if c.statement.startswith("CREATE TABLE")]
    if created:
        await conn.run_sync(Base.metadata.create_all)

    await apply_changes(conn, changes)

    dropped: list[str] = []
    if drop_obsolete:
        existing_tables, _ = await conn.run_sync(_collect_schema)
        for name in sorted(existing_tables - set(Base.metadata.tables)):
            await conn.execute(text(f'DROP TABLE IF EXISTS "{name}" CASCADE'))
            dropped.append(name)

    applied = [f"{c.table}: {c.statement}" for c in changes if not c.statement.startswith("CREATE TABLE")]
    applied += [f"created table {t}" for t in created]
    applied += [f"dropped obsolete table {t}" for t in dropped]
    return applied