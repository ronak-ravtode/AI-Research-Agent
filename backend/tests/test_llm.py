"""LLM retry behaviour: transient provider errors are retried, real errors are not."""

import pytest

from app.services.llm import (
    BACKOFF_BASE_SECONDS,
    MAX_ATTEMPTS,
    LLMService,
    is_transient,
)


def _service_with(client):
    svc = LLMService.__new__(LLMService)
    svc.client = client
    svc.model = "test-model"
    return svc


def test_transient_conditions_are_recognised():
    assert is_transient("Error code: 429 - rate limit reached")
    assert is_transient("Request timed out")
    assert is_transient("503 Service Unavailable")
    assert is_transient("connection reset by peer")


def test_permanent_conditions_are_not_transient():
    assert not is_transient("invalid api key")
    assert not is_transient("model not found")
    assert not is_transient("")


async def test_rate_limit_is_retried_then_succeeds(monkeypatch):
    monkeypatch.setattr("app.services.llm.asyncio.sleep", _no_sleep)
    calls = {"n": 0}

    class _Completions:
        async def create(self, **kwargs):
            calls["n"] += 1
            if calls["n"] < 3:
                raise RuntimeError("429 rate limit reached for model")
            return _response("recovered answer")

    class _Client:
        chat = type("chat", (), {"completions": _Completions()})()

    svc = _service_with(_Client())
    assert await svc.generate("hi") == "recovered answer"
    assert calls["n"] == 3


async def test_retries_are_bounded(monkeypatch):
    monkeypatch.setattr("app.services.llm.asyncio.sleep", _no_sleep)
    calls = {"n": 0}

    class _Completions:
        async def create(self, **kwargs):
            calls["n"] += 1
            raise RuntimeError("429 rate limit reached")

    class _Client:
        chat = type("chat", (), {"completions": _Completions()})()

    svc = _service_with(_Client())
    with pytest.raises(RuntimeError):
        await svc.generate("hi")
    assert calls["n"] == MAX_ATTEMPTS


async def test_permanent_error_is_not_retried(monkeypatch):
    monkeypatch.setattr("app.services.llm.asyncio.sleep", _no_sleep)
    calls = {"n": 0}

    class _Completions:
        async def create(self, **kwargs):
            calls["n"] += 1
            raise RuntimeError("invalid api key")

    class _Client:
        chat = type("chat", (), {"completions": _Completions()})()

    svc = _service_with(_Client())
    with pytest.raises(RuntimeError):
        await svc.generate("hi")
    assert calls["n"] == 1


async def test_generated_response_is_returned():
    class _Completions:
        async def create(self, **kwargs):
            return _response("plain text")

    class _Client:
        chat = type("chat", (), {"completions": _Completions()})()

    assert await _service_with(_Client()).generate("hi") == "plain text"


async def test_structured_generate_parses_fenced_json():
    class _Completions:
        async def create(self, **kwargs):
            return _response('```json\n{"queries": ["a", "b"]}\n```')

    class _Client:
        chat = type("chat", (), {"completions": _Completions()})()

    result = await _service_with(_Client()).structured_generate("hi")
    assert result == {"queries": ["a", "b"]}


async def test_structured_generate_parses_bare_json():
    class _Completions:
        async def create(self, **kwargs):
            return _response('{"queries": ["x"]}')

    class _Client:
        chat = type("chat", (), {"completions": _Completions()})()

    assert await _service_with(_Client()).structured_generate("hi") == {"queries": ["x"]}


async def test_structured_generate_handles_prose_around_json():
    class _Completions:
        async def create(self, **kwargs):
            return _response('Sure! {"queries": ["y"]} hope that helps')

    class _Client:
        chat = type("chat", (), {"completions": _Completions()})()

    assert await _service_with(_Client()).structured_generate("hi") == {"queries": ["y"]}


async def test_structured_generate_raises_on_unparseable_output():
    import json as _json

    class _Completions:
        async def create(self, **kwargs):
            return _response("no json at all")

    class _Client:
        chat = type("chat", (), {"completions": _Completions()})()

    with pytest.raises(_json.JSONDecodeError):
        await _service_with(_Client()).structured_generate("hi")


def test_backoff_settings_are_bounded():
    assert MAX_ATTEMPTS >= 2
    assert 0 < BACKOFF_BASE_SECONDS <= 10


async def _no_sleep(_seconds):
    return None


def _response(content):
    message = type("msg", (), {"content": content})()
    choice = type("choice", (), {"message": message})()
    return type("resp", (), {"choices": [choice]})()
