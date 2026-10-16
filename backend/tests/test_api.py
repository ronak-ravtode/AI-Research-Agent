from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.research import router
from app.database.database import Base, get_db, get_db_readonly


@pytest.fixture
def client(db_session):
    """A TestClient whose DB dependency resolves to the in-memory session."""
    from fastapi import FastAPI

    from app.api.sources import router as sources_router

    app = FastAPI()
    app.include_router(router)
    app.include_router(sources_router)

    async def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_db_readonly] = _get_db

    with TestClient(app) as test_client:
        yield test_client


def test_health_is_ok():
    from fastapi import FastAPI
    from app.api.health import router as health_router

    app = FastAPI()
    app.include_router(health_router)
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_post_research_returns_id_immediately(client):
    response = client.post(
        "/api/research", json={"query": "What are the main risks of generative AI?"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "started"
    assert len(body["research_id"]) == 36


def test_post_rejects_short_query(client):
    response = client.post("/api/research", json={"query": "hi"})
    assert response.status_code == 422


def test_post_rejects_empty_query(client):
    response = client.post("/api/research", json={"query": ""})
    assert response.status_code == 422


def test_post_rejects_overlong_query(client):
    response = client.post("/api/research", json={"query": "x" * 2001})
    assert response.status_code == 422


def test_post_strips_whitespace(client):
    response = client.post(
        "/api/research",
        json={"query": "    What are the main risks of generative AI?    "},
    )
    assert response.status_code == 200


async def test_status_reports_stage_and_message(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(
        id=uuid4(),
        query="A question about AI safety",
        status="running",
        current_stage="searching",
        progress_message="Searching the web with Tavily",
    )
    db_session.add(session)
    await db_session.commit()

    response = client.get(f"/api/research/{session.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["current_stage"] == "searching"
    assert body["progress_message"] == "Searching the web with Tavily"
    assert body["error_message"] is None
    assert body["report_markdown"] is None


async def test_status_includes_report_when_present(client, db_session):
    from app.database.models import Report, ResearchSession

    session = ResearchSession(
        id=uuid4(), query="A completed question", status="completed"
    )
    db_session.add(session)
    db_session.add(
        Report(session_id=session.id, title="T", answer_markdown="## Answer\nBody [1]")
    )
    await db_session.commit()

    body = client.get(f"/api/research/{session.id}").json()
    assert body["report_markdown"].startswith("## Answer")
    assert body["report_title"] == "T"


async def test_status_includes_error_message_on_failure(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(
        id=uuid4(),
        query="A failing question",
        status="failed",
        error_message="The web search could not be reached. Please try again in a moment.",
    )
    db_session.add(session)
    await db_session.commit()

    body = client.get(f"/api/research/{session.id}").json()
    assert body["status"] == "failed"
    assert "could not be reached" in body["error_message"]


def test_status_rejects_malformed_id(client):
    response = client.get("/api/research/not-a-uuid")
    assert response.status_code == 400


def test_status_returns_404_for_unknown_id(client):
    response = client.get(f"/api/research/{uuid4()}")
    assert response.status_code == 404


async def test_activity_returns_recorded_timeline(client, db_session):
    from app.database.models import ResearchActivity, ResearchSession

    session = ResearchSession(id=uuid4(), query="Timeline question here", status="running")
    db_session.add(session)
    db_session.add_all(
        [
            ResearchActivity(session_id=session.id, stage="planning", message="Breaking it down"),
            ResearchActivity(session_id=session.id, stage="searching", message="Searching"),
        ]
    )
    await db_session.commit()

    body = client.get(f"/api/research/{session.id}/activity").json()
    assert [a["stage"] for a in body["activity"]] == ["planning", "searching"]
    assert body["activity"][0]["message"] == "Breaking it down"


async def test_sources_endpoint_lists_retrieval_method(client, db_session):
    from app.database.models import ResearchSession, Source

    session = ResearchSession(id=uuid4(), query="Sources question here", status="completed")
    db_session.add(session)
    db_session.add_all(
        [
            Source(
                session_id=session.id,
                title="One",
                url="https://one.com/a",
                domain="one.com",
                retrieval_method="firecrawl",
                source_type="Web article",
            ),
            Source(
                session_id=session.id,
                title="Two",
                url="https://two.com/b",
                domain="two.com",
                retrieval_method="tavily_snippet",
                source_type="News",
            ),
        ]
    )
    await db_session.commit()

    body = client.get(f"/api/research/{session.id}/sources").json()
    assert body["total"] == 2
    assert {s["retrieval_method"] for s in body["sources"]} == {
        "firecrawl",
        "tavily_snippet",
    }


async def test_history_lists_sessions_with_counts(client, db_session):
    from app.database.models import Report, ResearchSession, Source

    session = ResearchSession(
        id=uuid4(), query="History question here", status="completed"
    )
    db_session.add(session)
    db_session.add(Source(session_id=session.id, title="s", url="https://s.com"))
    db_session.add(Report(session_id=session.id, title="t", answer_markdown="a"))
    await db_session.commit()

    body = client.get("/api/history").json()
    mine = [h for h in body["history"] if h["research_id"] == str(session.id)]
    assert len(mine) == 1
    assert mine[0]["source_count"] == 1
    assert mine[0]["has_report"] is True


async def test_history_includes_failed_sessions(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(
        id=uuid4(), query="Failed history question", status="failed"
    )
    db_session.add(session)
    await db_session.commit()

    body = client.get("/api/history").json()
    mine = [h for h in body["history"] if h["research_id"] == str(session.id)]
    assert mine[0]["status"] == "failed"
    assert mine[0]["has_report"] is False


def test_health_reports_missing_config_keys():
    from app.core.config import Settings

    empty = Settings(GROQ_API_KEY="", TAVILY_API_KEY="")
    missing = empty.missing_required_keys()
    assert "GROQ_API_KEY" in missing
    assert "TAVILY_API_KEY" in missing
