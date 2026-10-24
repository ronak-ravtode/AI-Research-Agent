"""The verifier checks the draft against its sources and fails open."""

from app.services.extraction import RetrievedSource


def _source(n):
    return RetrievedSource(
        title=f"Source {n}",
        url=f"https://site{n}.com/page",
        domain=f"site{n}.com",
        source_type="Web article",
        snippet=f"snippet {n}",
        content=f"evidence text {n}",
        retrieval_method="firecrawl",
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


async def test_unsupported_claims_produce_a_revised_body(monkeypatch):
    from app.services.verification import verification_service

    fake = _FakeLLM(
        {
            "supported": False,
            "revised_body": "## Answer\nA supported claim [1].",
            "removed_claims": 1,
            "note": "One claim had no source.",
        }
    )
    monkeypatch.setattr("app.services.verification.llm_service", fake)

    result = await verification_service.verify(
        "What is true?",
        "## Answer\nA supported claim [1]. An invented claim.",
        [_source(1)],
    )

    assert result.revised is True
    assert result.body == "## Answer\nA supported claim [1]."
    assert result.removed_claims == 1
    assert result.note == "One claim had no source."


async def test_supported_draft_is_left_unchanged(monkeypatch):
    from app.services.verification import verification_service

    fake = _FakeLLM(
        {
            "supported": True,
            "revised_body": "A pointless rewrite.",
            "removed_claims": 0,
            "note": "All claims supported.",
        }
    )
    monkeypatch.setattr("app.services.verification.llm_service", fake)

    body = "## Answer\nEverything checks out [1]."
    result = await verification_service.verify("q", body, [_source(1)])

    assert result.body == body
    assert result.revised is False


async def test_model_failure_keeps_the_original_draft(monkeypatch):
    from app.services.verification import verification_service

    monkeypatch.setattr(
        "app.services.verification.llm_service",
        _FakeLLM(error=RuntimeError("groq down")),
    )
    body = "## Answer\nStill usable [1]."
    result = await verification_service.verify("q", body, [_source(1)])

    assert result.body == body
    assert result.revised is False
    assert result.note


async def test_empty_revision_keeps_the_original_draft(monkeypatch):
    from app.services.verification import verification_service

    monkeypatch.setattr(
        "app.services.verification.llm_service",
        _FakeLLM(
            {"supported": False, "revised_body": "   ", "removed_claims": 2, "note": ""}
        ),
    )
    body = "## Answer\nKeep me [1]."
    result = await verification_service.verify("q", body, [_source(1)])

    assert result.body == body
    assert result.revised is False


async def test_no_sources_skips_the_model(monkeypatch):
    from app.services.verification import verification_service

    fake = _FakeLLM({"supported": False, "revised_body": "x"})
    monkeypatch.setattr("app.services.verification.llm_service", fake)

    body = "## Answer\nNo sources."
    result = await verification_service.verify("q", body, [])

    assert result.body == body
    assert fake.calls == []


async def test_prompt_includes_question_draft_and_sources(monkeypatch):
    from app.services.verification import verification_service

    fake = _FakeLLM(
        {"supported": True, "revised_body": "", "removed_claims": 0, "note": "ok"}
    )
    monkeypatch.setattr("app.services.verification.llm_service", fake)

    await verification_service.verify(
        "What is true?", "## Answer\nA claim [1].", [_source(1)]
    )

    prompt = fake.calls[0][0]
    assert "What is true?" in prompt
    assert "A claim [1]." in prompt
    assert "Source 1" in prompt
