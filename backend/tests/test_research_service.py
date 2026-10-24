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
from app.services.coverage import CoverageDecision
from app.services.extraction import RetrievedSource
from app.services.report import ReportResult
from app.services.search import SearchResult
from app.services.verification import VerificationResult

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

    MAX_SEARCH_RESULTS = 8
    MAX_SEARCH_QUERIES = 2
    MAX_AGENT_ITERATIONS = 2
    MAX_CONTEXT_SOURCES = 3
    MAX_CONTEXT_CHARS = 6000
    MAX_REWRITE_ROUNDS = 1

    def validate_required_keys(self):
        return None

    def missing_required_keys(self):
        return []


@pytest.fixture
def stubs(monkeypatch):
    """Replace every agent/tool with a predictable double."""
    state = {
        "planned": [],
        "plan_contexts": [],
        "searched": [],
        "report_contexts": [],
        "report_body": "## Answer\nAn answer [1].",
        "verify_calls": 0,
        "coverage_calls": 0,
        "coverage_tried": [],
        "coverage": [],
        "verification": None,
        "fail_search": False,
        "fail_followup_search": False,
        "fail_extract": False,
        "fail_report": False,
        "fail_revise": False,
        "revise_body": "## Answer\nRewritten after review [1].",
        "revise_calls": 0,
        "revise_feedbacks": [],
        "plan_fn": None,
        "search_results": list(SEARCH_RESULTS),
        "snippet_only_urls": set(),
        "search_fn": None,
    }

    async def plan_queries(question, context=None):
        if state["plan_fn"] is not None:
            queries = await state["plan_fn"](question, context)
        else:
            queries = ["query one", "query two"]
        state["plan_contexts"].append(context)
        return queries

    async def search(queries):
        if state["fail_search"]:
            from app.core.exceptions import SearchError

            raise SearchError("tavily unreachable")
        if state["fail_followup_search"] and queries == ["gap query"]:
            from app.core.exceptions import SearchError

            raise SearchError("follow-up search unreachable")
        state["searched"].extend(queries)
        if state["search_fn"] is not None:
            return state["search_fn"](queries)
        return list(state["search_results"])

    async def extract(results):
        if state["fail_extract"]:
            from app.core.exceptions import ExtractionError

            raise ExtractionError("nothing readable")
        sources = []
        for result in results:
            known = next((s for s in SOURCES if s.url == result.url), None)
            snippet_only = result.url in state["snippet_only_urls"]
            if known is not None and not snippet_only:
                sources.append(known)
                continue
            sources.append(
                RetrievedSource(
                    title=result.title,
                    url=result.url,
                    domain=result.domain,
                    source_type="Web article",
                    snippet=result.content or "snippet",
                    content="" if snippet_only else f"real page text for {result.url}",
                    retrieval_method=(
                        "tavily_snippet" if snippet_only else "firecrawl"
                    ),
                    search_score=result.score,
                )
            )
        return sources

    async def write_draft(question, sources, prior_context=None):
        if state["fail_report"]:
            from app.core.exceptions import ReportGenerationError

            raise ReportGenerationError("llm failed")
        state["report_contexts"].append(prior_context)
        return state["report_body"]

    def finalize(body, sources, question=""):
        references = "\n".join(
            f"{i}. [{source.title}]({source.url}) — {source.domain}"
            for i, source in enumerate(sources, start=1)
        )
        return ReportResult(
            title="A Title",
            answer_markdown=f"{body}\n\n## References\n\n{references}\n",
        )

    async def revise(question, body, sources, feedback=""):
        if state["fail_revise"]:
            from app.core.exceptions import ReportGenerationError

            raise ReportGenerationError("rewrite failed")
        state["revise_calls"] += 1
        state["revise_feedbacks"].append(feedback)
        return state["revise_body"]

    async def assess(question, sources, tried_queries):
        state["coverage_calls"] += 1
        state["coverage_tried"].append(list(tried_queries))
        if state["coverage"]:
            decision = state["coverage"].pop(0)
        else:
            decision = {
                "sufficient": True,
                "followup_queries": [],
                "reason": "evidence is sufficient",
            }
        return CoverageDecision(**decision)

    async def verify(question, body, sources):
        state["verify_calls"] += 1
        result = state["verification"]
        if result is None:
            return VerificationResult(body=body, revised=False, note="all supported")
        if isinstance(result, list):
            if not result:
                return VerificationResult(body=body, revised=False, note="all supported")
            return VerificationResult(**result.pop(0))
        if isinstance(result, dict):
            return VerificationResult(**result)
        return result

    monkeypatch.setattr("app.services.research.get_settings", lambda: _StubSettings())
    monkeypatch.setattr("app.services.research.planning_service",
                        type("P", (), {"plan_queries": staticmethod(plan_queries)}))
    monkeypatch.setattr("app.services.research.search_service",
                        type("S", (), {"search": staticmethod(search)}))
    monkeypatch.setattr("app.services.research.extraction_service",
                        type("E", (), {"extract": staticmethod(extract)}))
    monkeypatch.setattr(
        "app.services.research.report_service",
        type("R", (), {"write_draft": staticmethod(write_draft),
                       "finalize": staticmethod(finalize),
                       "revise": staticmethod(revise)}),
    )
    monkeypatch.setattr("app.services.research.coverage_service",
                        type("C", (), {"assess": staticmethod(assess)}))
    monkeypatch.setattr("app.services.research.verification_service",
                        type("V", (), {"verify": staticmethod(verify)}))
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
    assert distinct == [
        "planning", "searching", "reading", "deciding", "writing", "verifying", "complete"
    ]


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


async def test_planned_queries_are_stored_and_visible(db_session, stubs):
    import json

    from app.services.research import ResearchService

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    assert json.loads(session.planned_queries) == ["query one", "query two"]
    messages = [row.message for row in await _activity(db_session, session.id)]
    assert "Planned queries: query one; query two" in messages


async def test_sufficient_coverage_does_not_search_again(db_session, stubs):
    from app.services.research import ResearchService

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    assert stubs["coverage_calls"] == 1
    assert stubs["searched"] == ["query one", "query two"]


async def test_low_coverage_triggers_a_refinement_search(db_session, stubs):
    from app.services.research import ResearchService

    gap_result = SearchResult(
        title="Gap source",
        url="https://gap.com/x",
        content="gap evidence",
        score=0.8,
        domain="gap.com",
        normalized_url="https://gap.com/x",
    )

    def search(queries):
        if queries == ["gap query"]:
            return [gap_result]
        return list(SEARCH_RESULTS)

    stubs["search_fn"] = search
    stubs["coverage"] = [
        {
            "sufficient": False,
            "followup_queries": ["gap query"],
            "reason": "one angle is missing",
        }
    ]

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    assert "gap query" in stubs["searched"]
    assert stubs["coverage_calls"] == 2
    messages = [row.message for row in await _activity(db_session, session.id)]
    assert any("Following up" in message for message in messages)
    assert any("one angle is missing" in message for message in messages)

    urls = [
        row.url
        for row in (
            await db_session.execute(
                select(Source).where(Source.session_id == session.id)
            )
        ).scalars().all()
    ]
    assert "https://gap.com/x" in urls


async def test_agent_loop_is_bounded(db_session, stubs):
    from app.services.research import ResearchService

    def search(queries):
        if queries == ["query one", "query two"]:
            return list(SEARCH_RESULTS)
        return [
            SearchResult(
                title=f"Extra {queries[0]}",
                url=f"https://extra-{len(queries)}.com/{queries[0].replace(' ', '-')}",
                content="extra evidence",
                score=0.5,
                domain="extra.com",
                normalized_url=f"https://extra-{queries[0]}.com",
            )
        ]

    stubs["search_fn"] = search
    stubs["coverage"] = [
        {"sufficient": False, "followup_queries": [f"gap {i}"], "reason": "gap"}
        for i in range(5)
    ]

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    assert stubs["coverage_calls"] == 2
    assert "gap 2" not in stubs["searched"]
    assert "gap 3" not in stubs["searched"]


async def test_failed_refinement_search_does_not_fail_the_run(db_session, stubs):
    from app.database.models import STATUS_COMPLETED
    from app.services.research import ResearchService

    stubs["coverage"] = [
        {
            "sufficient": False,
            "followup_queries": ["gap query"],
            "reason": "gap",
        }
    ]
    stubs["fail_followup_search"] = True

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    assert session.status == STATUS_COMPLETED
    messages = [row.message for row in await _activity(db_session, session.id)]
    assert any("continuing with the available evidence" in m for m in messages)


async def test_snippet_only_pages_trigger_a_broader_search(db_session, stubs):
    from app.services.research import ResearchService

    extra = SearchResult(
        title="Full page",
        url="https://full.com/page",
        content="full evidence",
        score=0.9,
        domain="full.com",
        normalized_url="https://full.com/page",
    )

    def search(queries):
        if queries == [session.query]:
            return list(SEARCH_RESULTS) + [extra]
        return list(SEARCH_RESULTS)

    stubs["search_fn"] = search
    stubs["snippet_only_urls"] = {r.url for r in SEARCH_RESULTS}

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    assert session.query in stubs["searched"]

    sources = (
        await db_session.execute(
            select(Source).where(Source.session_id == session.id)
        )
    ).scalars().all()
    assert "https://full.com/page" in {s.url for s in sources}
    assert any(s.content for s in sources)


async def test_verifier_revision_triggers_a_writer_negotiation(db_session, stubs):
    from app.services.research import ResearchService

    stubs["verification"] = [
        {
            "body": "## Answer\nUncertain claims [1].",
            "revised": True,
            "removed_claims": 2,
            "note": "two unsupported claims removed",
        },
        {
            "body": "## Answer\nNegotiated only [1].",
            "revised": False,
            "removed_claims": 0,
            "note": "now fully supported",
        },
    ]
    stubs["revise_body"] = "## Answer\nRewritten draft [1]."

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    report = (
        await db_session.execute(select(Report).where(Report.session_id == session.id))
    ).scalar_one()
    assert "Negotiated only" in report.answer_markdown
    assert "Uncertain claims" not in report.answer_markdown
    assert stubs["verify_calls"] == 2
    assert stubs["revise_calls"] == 1
    assert "two unsupported claims" in stubs["revise_feedbacks"][0]


async def test_negotiation_loop_is_bounded(db_session, stubs):
    from app.database.models import STATUS_COMPLETED
    from app.services.research import ResearchService

    revised = {
        "body": "## Answer\nStill uncertain [1].",
        "revised": True,
        "removed_claims": 1,
        "note": "still unsupported",
    }
    stubs["verification"] = [dict(revised) for _ in range(10)]

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    assert session.status == STATUS_COMPLETED
    assert stubs["revise_calls"] == 1
    assert stubs["verify_calls"] == 2


async def test_replanning_includes_gap_feedback(db_session, stubs):
    from app.services.research import ResearchService

    gap_result = SearchResult(
        title="Gap source",
        url="https://gap.com/x",
        content="gap evidence",
        score=0.8,
        domain="gap.com",
        normalized_url="https://gap.com/x",
    )
    calls: list[str | None] = []

    async def plan(question, context=None):
        calls.append(context)
        if len(calls) == 1:
            return ["query one", "query two"]
        return ["replan query"]

    stubs["plan_fn"] = plan

    def search(queries):
        if queries == ["replan query"]:
            return [gap_result]
        return list(SEARCH_RESULTS)

    stubs["search_fn"] = search
    stubs["coverage"] = [
        {
            "sufficient": False,
            "followup_queries": ["reviewer query"],
            "reason": "one angle is missing",
        }
    ]

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    assert len(calls) == 2
    feedback = calls[1]
    assert feedback is not None
    assert "one angle is missing" in feedback
    assert "query one" in feedback
    assert "replan query" in stubs["searched"]
    assert "gap query" not in stubs["searched"]


async def test_planner_failure_falls_back_to_reviewer_queries(db_session, stubs):
    from app.database.models import STATUS_COMPLETED
    from app.services.research import ResearchService

    calls: list[str | None] = []

    async def plan(question, context=None):
        calls.append(context)
        if len(calls) == 1:
            return ["query one", "query two"]
        raise RuntimeError("planner down")

    stubs["plan_fn"] = plan
    stubs["coverage"] = [
        {
            "sufficient": False,
            "followup_queries": ["gap query"],
            "reason": "gap",
        }
    ]

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)
    await db_session.refresh(session)

    assert session.status == STATUS_COMPLETED
    assert len(calls) == 2
    assert "gap query" in stubs["searched"]


async def test_planner_repeat_queries_fall_back_to_reviewer_queries(db_session, stubs):
    from app.services.research import ResearchService

    calls: list[list[str]] = []

    async def plan(question, context=None):
        calls.append([])
        return ["query one", "query two"]

    stubs["plan_fn"] = plan
    stubs["coverage"] = [
        {
            "sufficient": False,
            "followup_queries": ["gap query"],
            "reason": "gap",
        }
    ]

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    assert len(calls) == 2
    assert "gap query" in stubs["searched"]


async def test_followup_uses_parent_report_and_sources(db_session, stubs):
    from app.services.research import ResearchService

    parent = ResearchSession(
        id=uuid4(), query="Parent question about AI risk", status="completed"
    )
    db_session.add(parent)
    db_session.add(
        Source(
            session_id=parent.id,
            title="Parent evidence",
            url="https://parent.com/evidence",
            domain="parent.com",
            source_type="Web article",
            snippet="parent snippet",
            content="parent content",
            retrieval_method="firecrawl",
            search_score=0.9,
        )
    )
    db_session.add(
        Report(
            session_id=parent.id,
            title="Parent report",
            answer_markdown="## Answer\nParent answer about risk [1].",
        )
    )
    child = ResearchSession(
        id=uuid4(),
        query="What about privacy specifically?",
        status="queued",
        parent_session_id=parent.id,
    )
    db_session.add(child)
    await db_session.commit()

    await ResearchService(db_session).run(child.id)
    await db_session.refresh(child)

    assert any(
        context and "Parent question about AI risk" in context
        for context in stubs["plan_contexts"]
    )
    assert any(
        context and "Parent answer about risk" in context
        for context in stubs["report_contexts"]
    )

    sources = (
        await db_session.execute(select(Source).where(Source.session_id == child.id))
    ).scalars().all()
    assert "https://parent.com/evidence" in {s.url for s in sources}


async def test_a_primary_run_has_no_prior_context(db_session, stubs):
    from app.services.research import ResearchService

    session = await _new_session(db_session)
    await ResearchService(db_session).run(session.id)

    assert stubs["plan_contexts"] == [None]
    assert stubs["report_contexts"] == [None]
