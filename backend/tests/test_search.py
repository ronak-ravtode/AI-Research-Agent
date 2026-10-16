import pytest

from app.core.exceptions import SearchError
from app.services.search import (
    SearchService,
    is_fetchable_url,
    normalize_url,
)


def _service_with(results_by_query, cap=None):
    """Build a SearchService whose Tavily calls are replaced by canned responses."""

    class _FakeClient:
        async def search(self, query, max_results, include_answer):
            if query in results_by_query:
                value = results_by_query[query]
                if isinstance(value, BaseException):
                    raise value
                return {"results": value}
            return {"results": []}

    svc = SearchService.__new__(SearchService)
    svc._client = _FakeClient()
    svc.max_results = cap or 8
    return svc


def test_normalize_url_collapses_tracking_noise():
    base = "https://www.Example.com/article/"
    assert normalize_url(base) == normalize_url("https://example.com/article")
    assert normalize_url(base) == normalize_url(
        "https://example.com/article?utm_source=twitter&utm_campaign=x"
    )


def test_normalize_url_keeps_meaningful_query():
    a = normalize_url("https://example.com/p?id=1")
    b = normalize_url("https://example.com/p?id=2")
    assert a != b


def test_is_fetchable_url_rejects_non_http_schemes():
    assert is_fetchable_url("https://example.com/a") is True
    assert is_fetchable_url("http://example.com/a") is True
    assert is_fetchable_url("file:///etc/passwd") is False
    assert is_fetchable_url("javascript:alert(1)") is False
    assert is_fetchable_url("ftp://example.com/x") is False
    assert is_fetchable_url("") is False


async def test_search_deduplicates_by_normalized_url():
    svc = _service_with(
        {
            "q1": [
                {"url": "https://example.com/a", "title": "A", "content": "x", "score": 0.4},
                {"url": "https://example.com/a/", "title": "A dup", "content": "x", "score": 0.9},
            ],
            "q2": [
                {"url": "https://other.org/b", "title": "B", "content": "y", "score": 0.5}
            ],
        }
    )
    results = await svc.search(["q1", "q2"])
    assert len(results) == 2
    # the higher-scoring duplicate wins
    a = next(r for r in results if "example.com" in r.url)
    assert a.score == 0.9
    assert a.title == "A dup"


async def test_search_orders_by_score_descending():
    svc = _service_with(
        {
            "q": [
                {"url": "https://low.com", "title": "low", "content": "", "score": 0.1},
                {"url": "https://high.com", "title": "high", "content": "", "score": 0.9},
            ]
        }
    )
    results = await svc.search(["q"])
    assert [r.domain for r in results] == ["high.com", "low.com"]


async def test_search_respects_result_cap():
    payload = [
        {"url": f"https://site{i}.com", "title": f"T{i}", "content": "", "score": i / 10}
        for i in range(20)
    ]
    svc = _service_with({"q": payload}, cap=8)
    assert len(await svc.search(["q"])) == 8


async def test_search_returns_empty_for_no_results():
    svc = _service_with({"q": []})
    assert await svc.search(["q"]) == []


async def test_search_skips_unfetchable_urls():
    svc = _service_with(
        {
            "q": [
                {"url": "javascript:alert(1)", "title": "bad", "content": ""},
                {"url": "file:///etc/passwd", "title": "worse", "content": ""},
                {"url": "https://ok.com/x", "title": "good", "content": "hi"},
            ]
        }
    )
    results = await svc.search(["q"])
    assert [r.url for r in results] == ["https://ok.com/x"]


async def test_search_tolerates_one_failing_query():
    svc = _service_with(
        {
            "good": [{"url": "https://ok.com", "title": "ok", "content": "hi", "score": 0.5}],
            "bad": RuntimeError("boom"),
        }
    )
    results = await svc.search(["bad", "good"])
    assert [r.url for r in results] == ["https://ok.com"]


async def test_search_raises_when_every_query_fails():
    svc = _service_with({"a": RuntimeError("boom"), "b": RuntimeError("bang")})
    with pytest.raises(SearchError):
        await svc.search(["a", "b"])


async def test_search_raises_on_empty_query_list():
    svc = _service_with({})
    with pytest.raises(SearchError):
        await svc.search(["", "   "])
