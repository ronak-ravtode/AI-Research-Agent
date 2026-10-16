"""The workflow contract: stages happen in order, failures are recorded, nothing escapes."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.database.models import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    Report,
    ResearchActivity,
    ResearchSession,
    Source,
)
from app.services.extraction import RetrievedSource
from app.services.report import ReportResult
from app.services.search import SearchResult

SOURCES = [
    RetrievedSource(
        title="Doc one",
        url="https://one.com/a",
        domain="one.com",
        source_type="Official documentation",
        snippet="s1",
        content="real page text one",
        retrieval_method="firecrawl",
        search_score=0.9,
    ),
    RetrievedSource(
        title="Doc two",
        url="https://two.com/b",
        domain="two.com",
        source_type="Web article",
        snippet="s2",
        content="real page text two",
        retrieval_method="firecrawl",
        search_score=0.7,
    ),
]

SEARCH_RESULTS = [
    SearchResult(
        title="Doc one",
        url="https://one.com/a",
        content="s1",
        score=0.9,
        domain="one.com",
        normalized_url="https://one.com/a",
    ),
    SearchResult(
        title="Doc two",
        url="https://two.com/b",
        content="s2",
        score=0.7,
        domain="two.com",
        normalized_url="https://two.com/b",
    ),
]


class _StubSettings:
    """Passes required-key validation so tests do not depend on a populated .env."""

    def validate_required_keys(self):
        return None

    def missing_required_keys(self):
        return []


@pytest.fixture
def stubs(monkeypatch):
    """Replace the four stage services and the settings gate with predictable doubles."""
    state = {
        "planned": [],
        "searched": [],
        "report_body": (
            "## Answer\nAn answer [1].\n\n## References\n\n"
            "1. [Doc one](https://one.com/a) — one.com (full page)"
        ),
        "fail_search": False,
        "fail_extract": False,
        "fail_report": False,
        "search_results": list(SEARCH_RESULTS),
    }

    async def plan_queries(question):
        state["planned"].append(question)
        return ["query one", "query two"]

    async def search(queries):
        if state["fail_search"]:
            from app.core.exceptions import SearchError

            raise SearchError("tavily unreachable")
        state["searched"].extend(queries)
        return list(state["search_results"])

    async def extract(results):
        if state["fail_extract"]:
            from app.core.exceptions import ExtractionError

            raise ExtractionError("nothing readable")
        return SOURCES

    async def write_report(question, sources):
        if state["fail_report"]:
            from app.core.exceptions import ReportGenerationError

            raise ReportGenerationError("llm failed")
        return ReportResult(title="A Title", answer_markdown=state["report_body"])

    monkeypatch.setattr("app.services.research.get_settings", lambda: _StubSettings())
    monkeypatch.setattr("app.services.research.planning_service",
                        type("P", (), {"plan_queries": staticmethod(plan_queries)}))
    monkeypatch.setattr("app.services.research.search_service",
                        type("S", (), {"search": staticmethod(search)}))
    monkeypatch.setattr("app.services.research.extraction_service",
                        type("E", (), {"extract": staticmethod(extract)}))
    monkeypatch.setattr("app.services.research.report_service",
                        type("R", (), {"write_report": staticmethod(write_report)}))
    return state


async def _new_session(db, status="queued"):
    session = ResearchSession(
        id=uuid4(),
        query="What are the main cybersecurity risks of generative AI?",
        status=status,
    )
    db.add(session)
    await db.commit()
    return session


async def _activity(db, session_id):
    rows = (
        await db.execute(
            select(ResearchActivity)
            .where(ResearchActivity.session_id == session_id)
            .order_by(ResearchActivity.id.asc())
        )
    ).scalars().all()
    return rows


async def test_successful_run_completes(db_session, stubs):
    from app.services.research import ResearchService

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    assert session.status == STATUS_COMPLETED
    assert session.error_message is None
    assert session.completed_at is not None
    assert session.progress_message == "Research complete"


async def test_all_four_stages_run_in_order(db_session, stubs):
    from app.services.research import ResearchService

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    # The distinct stage sequence, ignoring repeats (searching and reading each emit
    # more than one message).
    stages = [row.stage for row in await _activity(db_session, session.id)]
    distinct = [stages[0]] if stages else []
    for stage in stages[1:]:
        if stage != distinct[-1]:
            distinct.append(stage)
    assert distinct == ["planning", "searching", "reading", "writing", "complete"]


async def test_progress_messages_describe_real_events(db_session, stubs):
    from app.services.research import ResearchService

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    messages = [row.message for row in await _activity(db_session, session.id)]
    assert "Breaking the question into search queries" in messages
    assert "Searching the web with Tavily" in messages
    assert any("Found 2 possible sources" in m for m in messages)
    assert "Preparing the cited answer" in messages
    assert "Research complete" in messages


async def test_sources_are_persisted_with_retrieval_method(db_session, stubs):
    from app.services.research import ResearchService

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    rows = (
        await db_session.execute(
            select(Source).where(Source.session_id == session.id).order_by(Source.created_at)
        )
    ).scalars().all()
    assert len(rows) == 2
    assert {r.retrieval_method for r in rows} == {"firecrawl"}
    assert {r.domain for r in rows} == {"one.com", "two.com"}


async def test_report_is_saved_with_references(db_session, stubs):
    from app.services.research import ResearchService

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    report = (
        await db_session.execute(select(Report).where(Report.session_id == session.id))
    ).scalar_one()
    assert report.title == "A Title"
    assert "## References" in report.answer_markdown
    assert "https://one.com/a" in report.answer_markdown


async def test_sources_are_written_before_the_session_completes(db_session, stubs):
    from app.services.research import ResearchService

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    count = (
        await db_session.execute(
            select(Source.id).where(Source.session_id == session.id)
        )
    ).scalars().all()
    assert len(count) == 2


@pytest.mark.parametrize(
    "failure", ["fail_search", "fail_extract", "fail_report"]
)
async def test_provider_failure_marks_session_failed(db_session, stubs, failure):
    from app.services.research import ResearchService

    stubs[failure] = True
    session = await _new_session(db_session)

    # must not raise
    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    assert session.status == STATUS_FAILED
    assert session.error_message
    assert session.completed_at is not None


async def test_failure_message_is_user_safe(db_session, stubs):
    """No key, hostname, or traceback text may reach the stored user-facing message."""
    from app.services.research import ResearchService

    stubs["fail_search"] = True
    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    message = session.error_message
    assert "tavily" not in message.lower()
    assert "Traceback" not in message
    assert "api_key" not in message
    assert "http" not in message.lower()
    assert len(message) < 200


async def test_failure_writes_no_report_or_sources(db_session, stubs):
    from app.services.research import ResearchService

    stubs["fail_report"] = True
    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    reports = (
        await db_session.execute(select(Report).where(Report.session_id == session.id))
    ).scalars().all()
    sources = (
        await db_session.execute(select(Source).where(Source.session_id == session.id))
    ).scalars().all()
    assert reports == []
    assert sources == []


async def test_unexpected_exception_is_still_recorded_as_failed(db_session, stubs, monkeypatch):
    from app.services.research import ResearchService

    async def explode(question, sources):
        raise ValueError("something entirely unexpected happened")

    monkeypatch.setattr(
        "app.services.research.report_service",
        type("R", (), {"write_report": staticmethod(explode)}),
    )
    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    assert session.status == STATUS_FAILED
    # the raw exception text must not be echoed to the user
    assert "unexpected" not in (session.error_message or "").lower()


async def test_missing_session_does_not_raise(db_session, stubs):
    """`run` must never raise: a background task that throws leaves the UI stuck."""
    from app.services.research import ResearchService

    # No exception, and nothing is invented for a session that does not exist.
    await ResearchService(db_session).run(uuid4())


async def test_configuration_failure_marks_session_failed(db_session, monkeypatch):
    """A missing provider key must fail the session, not leave it queued forever."""
    from app.services.research import ResearchService

    class _BrokenSettings:
        def validate_required_keys(self):
            from app.core.exceptions import ConfigurationError

            raise ConfigurationError(detail="missing settings: GROQ_API_KEY")

    monkeypatch.setattr(
        "app.services.research.get_settings", lambda: _BrokenSettings()
    )
    session = await _new_session(db_session)

    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    assert session.status == STATUS_FAILED
    assert session.error_message
    assert "GROQ_API_KEY" not in session.error_message


async def test_vanished_session_is_logged_not_raised(db_session, stubs):
    """A session deleted before the run begins must not raise either."""
    from app.services.research import ResearchService

    await ResearchService(db_session).run(uuid4())


async def test_thin_results_trigger_one_broader_search(
    db_session, stubs, monkeypatch
):
    from app.services.research import ResearchService

    session = await _new_session(db_session)
    stubs["search_results"] = SEARCH_RESULTS[:1]
    calls = []

    async def search(queries):
        calls.append(list(queries))
        # The planned multi-query search comes back thin; the broader fallback on the
        # original single question returns the full set.
        if queries == [session.query]:
            return list(SEARCH_RESULTS)
        return SEARCH_RESULTS[:1]

    monkeypatch.setattr(
        "app.services.research.search_service",
        type("S", (), {"search": staticmethod(search)}),
    )
    await ResearchService(db_session).run(session.id)

    # two planned queries, then exactly one broader fallback on the original question
    assert len(calls) == 2
    assert calls[-1] == [session.query]
