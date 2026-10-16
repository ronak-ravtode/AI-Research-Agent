"""Stage 2 — web search via Tavily.

Provider response shapes are normalised here and nowhere else, so a Tavily change cannot
leak into the rest of the application.
"""

import asyncio
from dataclasses import dataclass, field
from urllib.parse import urlparse, urlunparse

import httpx
from tavily import AsyncTavilyClient

from app.core.config import get_settings
from app.core.exceptions import SearchError
from app.core.logging import logger

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "ref",
}


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float = 0.0
    domain: str = ""
    normalized_url: str = field(default="", repr=False)


def normalize_url(url: str) -> str:
    """Collapse tracking noise so the same page is not retrieved twice.

    `example.com/a`, `example.com/a/` and `example.com/a?utm_source=x` all normalize to
    one key. Non-http(s) URLs are returned unchanged so validation can reject them later.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return url.strip().lower()

    if parsed.scheme not in ("http", "https"):
        return url.strip().lower()

    query = "&".join(
        part
        for part in parsed.query.split("&")
        if part and part.split("=", 1)[0].lower() not in TRACKING_PARAMS
    )
    path = parsed.path.rstrip("/") or "/"
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return urlunparse((parsed.scheme.lower(), netloc, path, "", query, ""))


def is_fetchable_url(url: str) -> bool:
    """Only plain http(s) URLs are ever fetched.

    Search results are the sole source of URLs in this application, so this is defence in
    depth rather than the primary control against SSRF.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


class SearchService:
    def __init__(self):
        settings = get_settings()
        # Tavily's client takes no timeout argument, so the bound is applied by handing it
        # an httpx client that has one. Without this a stalled provider hangs the run.
        self._http = httpx.AsyncClient(timeout=settings.SEARCH_TIMEOUT)
        self._client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY, client=self._http)
        self.max_results = settings.MAX_SEARCH_RESULTS

    async def search(self, queries: list[str]) -> list[SearchResult]:
        """Run every query, merge the results, deduplicate, and cap the total.

        A query that fails is logged and skipped: one bad query should not lose the whole
        run. Only if *every* query fails does this raise.
        """
        unique_queries = [q.strip() for q in queries if q and q.strip()]
        if not unique_queries:
            raise SearchError(detail="no search queries were produced")

        batches = await asyncio.gather(
            *(self._search_one(q) for q in unique_queries),
            return_exceptions=True,
        )

        merged: list[SearchResult] = []
        failures = 0
        for query, batch in zip(unique_queries, batches):
            if isinstance(batch, BaseException):
                failures += 1
                logger.warning(
                    "Search query failed",
                    data={"query": query, "error": type(batch).__name__},
                )
                continue
            merged.extend(batch)

        if failures and failures == len(unique_queries):
            raise SearchError(detail=f"all {failures} search queries failed")

        return self._dedupe(merged)[: self.max_results]

    async def _search_one(self, query: str) -> list[SearchResult]:
        try:
            response = await self._client.search(
                query=query,
                max_results=self.max_results,
                include_answer=False,
            )
        except Exception as exc:
            raise SearchError(detail=f"tavily search failed: {exc}") from exc

        results: list[SearchResult] = []
        for item in response.get("results") or []:
            url = (item.get("url") or "").strip()
            if not url or not is_fetchable_url(url):
                continue
            results.append(
                SearchResult(
                    title=(item.get("title") or url).strip(),
                    url=url,
                    content=(item.get("content") or "").strip(),
                    score=float(item.get("score") or 0.0),
                    domain=urlparse(url).netloc,
                    normalized_url=normalize_url(url),
                )
            )
        return results

    @staticmethod
    def _dedupe(results: list[SearchResult]) -> list[SearchResult]:
        """Keep the highest-scoring copy of each normalized URL, preserving that order."""
        best: dict[str, SearchResult] = {}
        for result in results:
            key = result.normalized_url or result.url.lower()
            existing = best.get(key)
            if existing is None or result.score > existing.score:
                best[key] = result
        return sorted(best.values(), key=lambda r: r.score, reverse=True)


search_service = SearchService()
