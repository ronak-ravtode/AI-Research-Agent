"""The coverage agent decides whether the evidence is good enough to write from."""

from app.services.extraction import RetrievedSource


def _source(n, content="body"):
    return RetrievedSource(
        title=f"Source {n}",
        url=f"https://site{n}.com/page",
        domain=f"site{n}.com",
        source_type="Web article",
        snippet=f"snippet {n}",
        content=content,
        retrieval_method="firecrawl" if content else "tavily_snippet",
        search_score=0.5,
    )


class _FakeLLM:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = []

    async def structured_generate(self, prompt, system_prompt=None, **kwargs):
        self.calls.append((prompt, system_prompt))
        if self.error:
            raise self.error
        return self.payload


async def test_sufficient_evidence_returns_write_decision(monkeypatch):
    from app.services.coverage import coverage_service

    fake = _FakeLLM(
        {"sufficient": True, "followup_queries": [], "reason": "covers both angles"}
    )
    monkeypatch.setattr("app.services.coverage.llm_service", fake)

    decision = await coverage_service.assess(
        "What are the risks?", [_source(1), _source(2)], ["risks of ai"]
    )

    assert decision.sufficient is True
    assert decision.followup_queries == []
    assert decision.reason == "covers both angles"


async def test_insufficient_evidence_returns_new_queries(monkeypatch):
    from app.services.coverage import coverage_service

    fake = _FakeLLM(
        {
            "sufficient": False,
            "followup_queries": ["ai privacy harms", "model misuse evidence"],
            "reason": "only one angle is covered",
        }
    )
    monkeypatch.setattr("app.services.coverage.llm_service", fake)

    decision = await coverage_service.assess(
        "What are the risks?", [_source(1)], ["risks of ai"]
    )

    assert decision.sufficient is False
    assert decision.followup_queries == ["ai privacy harms", "model misuse evidence"]
    assert decision.reason


async def test_duplicate_and_already_tried_queries_are_removed(monkeypatch):
    from app.services.coverage import coverage_service

    fake = _FakeLLM(
        {
            "sufficient": False,
            "followup_queries": ["AI Privacy Harms", "ai privacy harms", "risks of AI"],
            "reason": "gap",
        }
    )
    monkeypatch.setattr("app.services.coverage.llm_service", fake)

    decision = await coverage_service.assess(
        "What are the risks?", [_source(1)], ["risks of AI"]
    )

    assert decision.followup_queries == ["AI Privacy Harms"]


async def test_followup_queries_are_capped(monkeypatch):
    from app.services.coverage import coverage_service

    fake = _FakeLLM(
        {
            "sufficient": False,
            "followup_queries": [f"query {i}" for i in range(10)],
            "reason": "gap",
        }
    )
    monkeypatch.setattr("app.services.coverage.llm_service", fake)

    decision = await coverage_service.assess("q", [_source(1)], [])

    assert len(decision.followup_queries) <= coverage_service.max_queries


async def test_model_failure_defaults_to_writing(monkeypatch):
    from app.services.coverage import coverage_service

    monkeypatch.setattr(
        "app.services.coverage.llm_service",
        _FakeLLM(error=RuntimeError("groq down")),
    )

    decision = await coverage_service.assess("q", [_source(1)], [])

    assert decision.sufficient is True
    assert decision.followup_queries == []
    assert decision.reason


async def test_malformed_payload_defaults_to_writing(monkeypatch):
    from app.services.coverage import coverage_service

    monkeypatch.setattr(
        "app.services.coverage.llm_service",
        _FakeLLM({"unexpected": "shape"}),
    )

    decision = await coverage_service.assess("q", [_source(1)], [])

    assert decision.sufficient is True


async def test_prompt_includes_question_sources_and_tried_queries(monkeypatch):
    from app.services.coverage import coverage_service

    fake = _FakeLLM({"sufficient": True, "followup_queries": [], "reason": "ok"})
    monkeypatch.setattr("app.services.coverage.llm_service", fake)

    await coverage_service.assess(
        "What are the risks?", [_source(1)], ["first query"]
    )

    prompt = fake.calls[0][0]
    assert "What are the risks?" in prompt
    assert "Source 1" in prompt
    assert "first query" in prompt
