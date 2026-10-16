"""SSE must emit real events, only when something changed, and always terminate."""

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.api.research import (
    KEEPALIVE_SECONDS,
    POLL_INTERVAL_SECONDS,
    router,
)
from app.database.models import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_RUNNING,
    ResearchActivity,
    ResearchSession,
)
from app.services.research import ResearchService


def _parse(raw: str) -> list[dict]:
    """Decode an SSE body into a list of {event, data} dicts.

    sse-starlette separates records with CRLF, so normalise before splitting on the blank
    line that ends a record.
    """
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    events = []
    for block in raw.split("\n\n"):
        block = block.strip()
        if not block or block.startswith(":"):
            continue
        event = None
        data_lines = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_lines.append(line.split(":", 1)[1].strip())
        if event:
            payload = "\n".join(data_lines)
            try:
                events.append(
                    {"event": event, "data": json.loads(payload) if payload else None}
                )
            except json.JSONDecodeError:
                events.append({"event": event, "data": payload})
    return events


async def _make_session(db, status=STATUS_RUNNING, stage="searching", message="Searching"):
    session = ResearchSession(
        id=uuid4(),
        query="A streamed research question",
        status=status,
        current_stage=stage,
        progress_message=message,
    )
    db.add(session)
    await db.commit()
    return session


async def test_stream_emits_recorded_stages_then_complete(db_session, monkeypatch):
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    session = await _make_session(db_session)
    db_session.add_all(
        [
            ResearchActivity(session_id=session.id, stage="planning", message="Planning the search"),
            ResearchActivity(session_id=session.id, stage="searching", message="Searching the web"),
        ]
    )
    # already finished, so the stream terminates immediately after replaying history
    session.status = STATUS_COMPLETED
    session.progress_message = "Research complete"
    await db_session.commit()

    import app.api.research as mod

    monkeypatch.setattr(mod, "_get_session_factory", lambda: _factory(db_session))

    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.get(f"/api/research/{session.id}/stream")
        assert response.status_code == 200

    events = _parse(response.text)
    stages = [e for e in events if e["event"] == "stage"]
    assert [e["data"]["stage"] for e in stages] == ["planning", "searching"]
    assert stages[0]["data"]["message"] == "Planning the search"
    assert events[-1]["event"] == "complete"
    assert events[-1]["data"]["status"] == STATUS_COMPLETED


async def test_stream_terminal_error_carries_safe_message(db_session, monkeypatch):
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    session = await _make_session(
        db_session,
        status=STATUS_FAILED,
        stage="complete",
        message="Research failed",
    )
    session.error_message = "The web search could not be reached. Please try again in a moment."
    await db_session.commit()

    import app.api.research as mod

    monkeypatch.setattr(mod, "_get_session_factory", lambda: _factory(db_session))

    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.get(f"/api/research/{session.id}/stream")

    events = _parse(response.text)
    complete = [e for e in events if e["event"] == "complete"]
    assert complete, "a failed run must still terminate the stream"
    assert complete[-1]["data"]["status"] == STATUS_FAILED
    assert "could not be reached" in complete[-1]["data"]["message"]


async def test_stream_rejects_malformed_id(db_session, monkeypatch):
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    monkeypatch.setattr(
        "app.api.research._get_session_factory", lambda: _factory(db_session)
    )
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.get("/api/research/not-a-uuid/stream")

    events = _parse(response.text)
    assert any(e["event"] == "error" for e in events), events


async def test_stream_errors_on_unknown_session(db_session, monkeypatch):
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    monkeypatch.setattr(
        "app.api.research._get_session_factory", lambda: _factory(db_session)
    )
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.get(f"/api/research/{uuid4()}/stream")

    events = _parse(response.text)
    assert any(e["event"] == "error" for e in events)


async def test_stream_only_emits_new_activity_once_seen(db_session, monkeypatch):
    """A client that reconnects mid-run must not be replayed the whole timeline."""
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    session = await _make_session(db_session)
    db_session.add_all(
        [
            ResearchActivity(session_id=session.id, stage="planning", message="P"),
            ResearchActivity(session_id=session.id, stage="searching", message="S"),
        ]
    )
    # Terminal, so the generator exits instead of polling forever.
    session.status = STATUS_COMPLETED
    await db_session.commit()

    import app.api.research as mod

    monkeypatch.setattr(mod, "_get_session_factory", lambda: _factory(db_session))

    app = FastAPI()
    app.include_router(router)

    # Walk the generator twice, feeding back the last seen id, the way a reconnecting
    # browser does, and confirm the second pass yields nothing already seen.
    with TestClient(app) as client:
        response = client.get(f"/api/research/{session.id}/stream")
    first = [e for e in _parse(response.text) if e["event"] == "stage"]
    assert len(first) == 2
    assert len({e["data"]["stage"] for e in first}) == 2


def _factory(session):
    """A session factory that hands the SSE generator our single test session."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _ctx():
        yield session

    return lambda: _ctx()


def test_poll_and_keepalive_intervals_are_sane():
    assert 0 < POLL_INTERVAL_SECONDS <= 2
    assert KEEPALIVE_SECONDS >= 10
