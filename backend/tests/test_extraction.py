import pytest

from app.core.exceptions import ExtractionError
from app.services.extraction import (
    ExtractionService,
    classify_source_type,
    clean_page_text,
)
from app.services.search import SearchResult


def _result(url="https://example.com/a", **kw):
    from urllib.parse import urlparse

    return SearchResult(
        title=kw.get("title", "Example"),
        url=url,
        content=kw.get("content", "snippet text"),
        score=kw.get("score", 0.5),
        domain=kw.get("domain") or urlparse(url).netloc,
        normalized_url=url,
    )


def _service(scrape_behaviour):
    """ExtractionService with Firecrawl's sync scrape replaced."""

    class _FakeApp:
        def scrape_url(self, url, params=None):
            return scrape_behaviour(url)

    svc = ExtractionService.__new__(ExtractionService)
    svc._api_key = "test"
    svc._firecrawl_app = _FakeApp()
    svc.max_sources = 5
    svc.max_source_chars = 6000
    return svc


def test_classify_source_type_is_conservative():
    assert classify_source_type("https://arxiv.org/abs/1234") == "Research paper"
    assert classify_source_type("https://web.mit.edu/x") == "Research paper"
    assert classify_source_type("https://www.cdc.gov/thing") == "Government"
    assert classify_source_type("https://www.nist.gov/x") == "Government"
    assert classify_source_type("https://docs.python.org/3/") == "Official documentation"
    assert classify_source_type("https://www.reuters.com/x") == "News"
    assert classify_source_type("https://random-blog.example/x") == "Web article"
    assert classify_source_type("") == "Web article"


def test_clean_page_text_collapses_noise():
    assert clean_page_text("a  \n\n\n\nb") == "a\n\nb"
    assert clean_page_text("   ") == ""


async def test_extract_marks_full_pages():
    svc = _service(lambda url: {"markdown": "full page content here"})
    out = await svc.extract([_result()])
    assert len(out) == 1
    assert out[0].retrieval_method == "firecrawl"
    assert out[0].content == "full page content here"
    assert out[0].text == "full page content here"


async def test_extract_falls_back_to_snippet_on_scrape_failure():
    def boom(url):
        raise RuntimeError("firecrawl down")

    svc = _service(boom)
    out = await svc.extract([_result(content="the search snippet")])
    assert len(out) == 1
    assert out[0].retrieval_method == "tavily_snippet"
    assert out[0].content == ""
    assert out[0].text == "the search snippet"


async def test_extract_falls_back_when_page_is_empty():
    svc = _service(lambda url: {"markdown": ""})
    out = await svc.extract([_result(content="only a snippet")])
    assert out[0].retrieval_method == "tavily_snippet"
    assert out[0].text == "only a snippet"


async def test_extract_raises_when_every_source_is_empty():
    svc = _service(lambda url: {"markdown": ""})
    with pytest.raises(ExtractionError):
        await svc.extract(
            [
                _result(url="https://a.com/x", content=""),
                _result(url="https://b.com/x", content=""),
            ]
        )


async def test_extract_survives_a_mix_of_good_and_bad_pages():
    def selective(url):
        if "bad" in url:
            raise RuntimeError("nope")
        return {"markdown": "real content"}

    svc = _service(selective)
    out = await svc.extract(
        [_result(url="https://bad.com/x", content="bad snippet"),
         _result(url="https://good.com/x", content="good snippet")]
    )
    methods = {s.domain: s.retrieval_method for s in out}
    assert methods["bad.com"] == "tavily_snippet"
    assert methods["good.com"] == "firecrawl"


async def test_extract_caps_per_source_characters():
    svc = _service(lambda url: {"markdown": "x" * 10000})
    svc.max_source_chars = 100
    out = await svc.extract([_result()])
    assert len(out[0].content) == 100


async def test_extract_caps_number_of_sources():
    svc = _service(lambda url: {"markdown": "content"})
    svc.max_sources = 2
    results = [_result(url=f"https://site{i}.com") for i in range(6)]
    assert len(await svc.extract(results)) == 2


async def test_extract_rejects_unfetchable_candidates():
    svc = _service(lambda url: {"markdown": "content"})
    with pytest.raises(ExtractionError):
        await svc.extract([_result(url="file:///etc/passwd")])
