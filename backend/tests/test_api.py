from datetime import datetime, timezone
from uuid import UUID, uuid4

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


async def test_post_creates_a_followup_with_parent_context(
    client, db_session, monkeypatch
):
    from app.database.models import ResearchSession
    from app.api import research as research_api

    async def no_background(_research_id):
        return None

    monkeypatch.setattr(research_api, "_run_in_background", no_background)

    parent = ResearchSession(
        id=uuid4(), query="Parent question about risks", status="completed"
    )
    db_session.add(parent)
    await db_session.commit()

    response = client.post(
        "/api/research",
        json={
            "query": "What about privacy specifically?",
            "parent_research_id": str(parent.id),
        },
    )

    assert response.status_code == 200
    research_id = response.json()["research_id"]
    child = await db_session.get(ResearchSession, UUID(research_id))
    assert child is not None
    assert child.parent_session_id == parent.id


def test_post_rejects_unknown_parent(client):
    response = client.post(
        "/api/research",
        json={"query": "A follow-up question here", "parent_research_id": str(uuid4())},
    )
    assert response.status_code == 404


def test_post_rejects_malformed_parent(client):
    response = client.post(
        "/api/research",
        json={"query": "A follow-up question here", "parent_research_id": "not-a-uuid"},
    )
    assert response.status_code == 400


async def test_post_rejects_unfinished_parent(client, db_session):
    from app.database.models import ResearchSession

    parent = ResearchSession(
        id=uuid4(), query="Still running question", status="running"
    )
    db_session.add(parent)
    await db_session.commit()

    response = client.post(
        "/api/research",
        json={"query": "A follow-up question here", "parent_research_id": str(parent.id)},
    )
    assert response.status_code == 400


async def test_status_includes_plan_and_parent(client, db_session):
    from app.database.models import ResearchSession

    parent = ResearchSession(
        id=uuid4(), query="The earlier question", status="completed"
    )
    child = ResearchSession(
        id=uuid4(),
        query="The follow-up question",
        status="completed",
        parent_session_id=parent.id,
        planned_queries='["alpha query", "beta query"]',
    )
    db_session.add_all([parent, child])
    await db_session.commit()

    body = client.get(f"/api/research/{child.id}").json()
    assert body["planned_queries"] == ["alpha query", "beta query"]
    assert body["parent_research_id"] == str(parent.id)


async def test_status_tolerates_malformed_plan_json(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(
        id=uuid4(),
        query="A question with a bad plan",
        status="completed",
        planned_queries="not json",
    )
    db_session.add(session)
    await db_session.commit()

    body = client.get(f"/api/research/{session.id}").json()
    assert body["planned_queries"] == []


async def test_history_includes_parent_link(client, db_session):
    from app.database.models import ResearchSession

    parent = ResearchSession(
        id=uuid4(), query="History parent question", status="completed"
    )
    child = ResearchSession(
        id=uuid4(),
        query="History follow-up question",
        status="completed",
        parent_session_id=parent.id,
    )
    db_session.add_all([parent, child])
    await db_session.commit()

    body = client.get("/api/history").json()
    mine = [h for h in body["history"] if h["research_id"] == str(child.id)]
    assert mine[0]["parent_research_id"] == str(parent.id)


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


def test_health_reports_providers_limits_and_configured():
    from fastapi import FastAPI
    from app.api.health import router as health_router

    app = FastAPI()
    app.include_router(health_router)
    body = TestClient(app).get("/api/health").json()

    assert set(body["providers"]) == {"llm", "search", "extraction"}
    assert set(body["limits"]) == {
        "max_agent_iterations",
        "max_search_results",
        "max_extract_sources",
    }
    assert isinstance(body["configured"], bool)
    # No secret material may leak into the health payload.
    assert "key" not in str(body["providers"]).lower()


# --------------------------------------------------------------------------------------
# Cancellation
# --------------------------------------------------------------------------------------


async def test_cancel_queued_run_marks_it_cancelled(client, db_session):
    from app.database.models import ResearchActivity, ResearchSession

    session = ResearchSession(id=uuid4(), query="A queued question here", status="queued")
    db_session.add(session)
    await db_session.commit()

    response = client.post(f"/api/research/{session.id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    await db_session.refresh(session)
    assert session.status == "cancelled"
    assert session.cancel_requested is True
    assert session.completed_at is not None

    from sqlalchemy import select

    activity = (
        await db_session.execute(
            select(ResearchActivity).where(ResearchActivity.session_id == session.id)
        )
    ).scalars().all()
    assert any("cancel" in row.message.lower() for row in activity)


async def test_cancel_running_run_only_requests_stop(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(id=uuid4(), query="A running question here", status="running")
    db_session.add(session)
    await db_session.commit()

    response = client.post(f"/api/research/{session.id}/cancel")
    assert response.status_code == 200
    # A running run is not killed mid-flight; it stops at its next stage boundary.
    assert response.json()["status"] == "running"

    await db_session.refresh(session)
    assert session.cancel_requested is True
    assert session.status == "running"


async def test_cancel_is_idempotent_for_finished_runs(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(
        id=uuid4(), query="An already finished question", status="completed"
    )
    db_session.add(session)
    await db_session.commit()

    response = client.post(f"/api/research/{session.id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    await db_session.refresh(session)
    assert session.cancel_requested is False


def test_cancel_unknown_run_returns_404(client):
    response = client.post(f"/api/research/{uuid4()}/cancel")
    assert response.status_code == 404


def test_cancel_rejects_malformed_id(client):
    response = client.post("/api/research/not-a-uuid/cancel")
    assert response.status_code == 400


# --------------------------------------------------------------------------------------
# Rename
# --------------------------------------------------------------------------------------


async def test_rename_sets_display_title_used_by_history(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(
        id=uuid4(), query="The original question text", status="completed"
    )
    db_session.add(session)
    await db_session.commit()

    response = client.patch(
        f"/api/research/{session.id}", json={"title": "  My short name  "}
    )
    assert response.status_code == 200
    assert response.json()["display_title"] == "My short name"

    status = client.get(f"/api/research/{session.id}").json()
    assert status["display_title"] == "My short name"
    # The real question is never overwritten by a display name.
    assert status["query"] == "The original question text"

    history = client.get("/api/history").json()["history"]
    mine = [h for h in history if h["research_id"] == str(session.id)]
    assert mine[0]["title"] == "My short name"


async def test_rename_to_blank_clears_display_title(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(
        id=uuid4(),
        query="Question that keeps its text",
        status="completed",
        display_title="Temporary",
    )
    db_session.add(session)
    await db_session.commit()

    response = client.patch(f"/api/research/{session.id}", json={"title": "   "})
    assert response.status_code == 200
    assert response.json()["display_title"] is None

    history = client.get("/api/history").json()["history"]
    mine = [h for h in history if h["research_id"] == str(session.id)]
    assert mine[0]["title"] == "Question that keeps its text"


def test_rename_rejects_overlong_title(client):
    response = client.patch(f"/api/research/{uuid4()}", json={"title": "x" * 301})
    assert response.status_code == 422


def test_rename_unknown_run_returns_404(client):
    response = client.patch(f"/api/research/{uuid4()}", json={"title": "Anything"})
    assert response.status_code == 404


# --------------------------------------------------------------------------------------
# Delete
# --------------------------------------------------------------------------------------


async def test_delete_removes_session_and_children(client, db_session):
    from sqlalchemy import select

    from app.database.models import Report, ResearchSession, Source

    session = ResearchSession(
        id=uuid4(), query="A session about to be deleted", status="completed"
    )
    db_session.add(session)
    db_session.add(Source(session_id=session.id, title="s", url="https://s.com"))
    db_session.add(Report(session_id=session.id, title="t", answer_markdown="a"))
    await db_session.commit()

    response = client.delete(f"/api/research/{session.id}")
    assert response.status_code == 204

    db_session.expire_all()
    assert await db_session.get(ResearchSession, session.id) is None
    sources = (
        await db_session.execute(select(Source).where(Source.session_id == session.id))
    ).scalars().all()
    reports = (
        await db_session.execute(select(Report).where(Report.session_id == session.id))
    ).scalars().all()
    assert sources == []
    assert reports == []

    assert client.get(f"/api/research/{session.id}").status_code == 404


def test_delete_unknown_run_returns_404(client):
    assert client.delete(f"/api/research/{uuid4()}").status_code == 404


# --------------------------------------------------------------------------------------
# Source detail
# --------------------------------------------------------------------------------------


async def test_source_detail_returns_content_index_and_total(client, db_session):
    from app.database.models import ResearchSession, Source

    session = ResearchSession(id=uuid4(), query="Source detail question", status="completed")
    first = Source(
        session_id=session.id,
        title="First source",
        url="https://first.com/a",
        content="full text of the first page",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    second = Source(
        session_id=session.id,
        title="Second source",
        url="https://second.com/b",
        content="full text of the second page",
        created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    db_session.add_all([first, second])
    await db_session.commit()

    body = client.get(f"/api/research/{session.id}/sources/{second.id}").json()
    assert body["index"] == 2
    assert body["total"] == 2
    assert body["content"] == "full text of the second page"
    assert body["title"] == "Second source"


async def test_source_detail_404_when_source_belongs_to_another_run(client, db_session):
    from app.database.models import ResearchSession, Source

    owner = ResearchSession(id=uuid4(), query="Owner run question here", status="completed")
    other = ResearchSession(id=uuid4(), query="Other run question here", status="completed")
    source = Source(session_id=owner.id, title="Owned", url="https://owned.com")
    db_session.add_all([owner, other, source])
    await db_session.commit()

    response = client.get(f"/api/research/{other.id}/sources/{source.id}")
    assert response.status_code == 404


def test_source_detail_rejects_malformed_ids(client):
    assert client.get(f"/api/research/not-a-uuid/sources/{uuid4()}").status_code == 400
    assert client.get(f"/api/research/{uuid4()}/sources/not-a-uuid").status_code == 400


# --------------------------------------------------------------------------------------
# History: pagination, filtering, search
# --------------------------------------------------------------------------------------


async def test_history_paginates_with_total_and_has_more(client, db_session):
    from app.database.models import ResearchSession

    for day in (1, 2, 3):
        db_session.add(
            ResearchSession(
                id=uuid4(),
                query=f"Paged question number {day}",
                status="completed",
                created_at=datetime(2024, 1, day, tzinfo=timezone.utc),
            )
        )
    await db_session.commit()

    first_page = client.get("/api/history?limit=2&offset=0").json()
    assert first_page["total"] == 3
    assert first_page["limit"] == 2
    assert first_page["offset"] == 0
    assert first_page["has_more"] is True
    assert len(first_page["history"]) == 2
    # Newest first.
    assert first_page["history"][0]["query"] == "Paged question number 3"

    second_page = client.get("/api/history?limit=2&offset=2").json()
    assert second_page["has_more"] is False
    assert len(second_page["history"]) == 1
    assert second_page["history"][0]["query"] == "Paged question number 1"


async def test_history_filters_by_status(client, db_session):
    from app.database.models import ResearchSession

    done = ResearchSession(id=uuid4(), query="A completed question", status="completed")
    broken = ResearchSession(id=uuid4(), query="A failed question", status="failed")
    db_session.add_all([done, broken])
    await db_session.commit()

    body = client.get("/api/history?status=failed").json()
    ids = {h["research_id"] for h in body["history"]}
    assert str(broken.id) in ids
    assert str(done.id) not in ids
    assert body["total"] == 1


async def test_history_searches_query_and_display_title(client, db_session):
    from app.database.models import ResearchSession

    db_session.add_all(
        [
            ResearchSession(
                id=uuid4(), query="How does quantum computing work?", status="completed"
            ),
            ResearchSession(
                id=uuid4(),
                query="Something entirely unrelated",
                status="completed",
                display_title="Quantum primer",
            ),
            ResearchSession(id=uuid4(), query="An unrelated topic", status="completed"),
        ]
    )
    await db_session.commit()

    by_query = client.get("/api/history?q=quantum").json()
    assert by_query["total"] == 2
    assert all(
        "quantum" in h["query"].lower() or "quantum" in (h["title"] or "").lower()
        for h in by_query["history"]
    )

    by_title = client.get("/api/history?q=primer").json()
    assert by_title["total"] == 1
    assert by_title["history"][0]["title"] == "Quantum primer"


def test_history_rejects_unknown_status_filter(client):
    response = client.get("/api/history?status=banana")
    assert response.status_code == 400


# --------------------------------------------------------------------------------------
# Verification + depth persistence
# --------------------------------------------------------------------------------------


async def test_status_surfaces_verification_fields(client, db_session):
    from app.database.models import Report, ResearchSession

    session = ResearchSession(id=uuid4(), query="Verified question here", status="completed")
    db_session.add(session)
    db_session.add(
        Report(
            session_id=session.id,
            title="Verified",
            answer_markdown="Body [1]",
            verification_note="Two claims were unsupported and removed.",
            removed_claims=2,
            verification_revised=True,
            verification_available=True,
        )
    )
    await db_session.commit()

    body = client.get(f"/api/research/{session.id}").json()
    assert body["verification_available"] is True
    assert body["verification_revised"] is True
    assert body["removed_claims"] == 2
    assert "unsupported" in body["verification_note"]


async def test_post_persists_requested_depth(client, db_session, monkeypatch):
    from app.api import research as research_api
    from app.database.models import ResearchSession

    async def no_background(_research_id):
        return None

    monkeypatch.setattr(research_api, "_run_in_background", no_background)

    response = client.post(
        "/api/research",
        json={"query": "How deep does this run go?", "max_iterations": 3},
    )
    assert response.status_code == 200
    research_id = response.json()["research_id"]

    session = await db_session.get(ResearchSession, UUID(research_id))
    assert session.max_iterations == 3

    body = client.get(f"/api/research/{research_id}").json()
    assert body["max_iterations"] == 3


def test_post_rejects_out_of_range_depth(client):
    assert (
        client.post(
            "/api/research", json={"query": "A valid question here", "max_iterations": 9}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/research", json={"query": "A valid question here", "max_iterations": -1}
        ).status_code
        == 422
    )


# --------------------------------------------------------------------------------------
# Legacy status coercion
# --------------------------------------------------------------------------------------


def test_normalize_status_coerces_legacy_values():
    from app.database.models import normalize_status

    assert normalize_status("completed") == "completed"
    assert normalize_status("cancelled") == "cancelled"
    # A stage name stored by an older schema is treated as still running.
    assert normalize_status("planning") == "running"
    assert normalize_status("verifying") == "running"
    assert normalize_status("complete") == "completed"
    # Anything unrecognised stays visible as queued rather than crashing the client.
    assert normalize_status("banana") == "queued"
    assert normalize_status(None) == "queued"


async def test_status_endpoint_accepts_a_legacy_stage_status(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(
        id=uuid4(), query="A row from an older schema", status="planning"
    )
    db_session.add(session)
    await db_session.commit()

    response = client.get(f"/api/research/{session.id}")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


async def test_history_coerces_a_legacy_stage_status(client, db_session):
    from app.database.models import ResearchSession

    session = ResearchSession(
        id=uuid4(), query="Legacy history row here", status="searching"
    )
    db_session.add(session)
    await db_session.commit()

    body = client.get("/api/history").json()
    mine = [h for h in body["history"] if h["research_id"] == str(session.id)]
    assert mine[0]["status"] == "running"


