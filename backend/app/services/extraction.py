"""Stage 3 — page extraction via Firecrawl, with a search-snippet fallback.

One unreadable page must not fail the run. A source whose scrape fails keeps whatever the
search provider returned and is marked `tavily_snippet`, so the report can still cite it and
the UI can be honest about how much was actually read.
"""

import asyncio
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from app.core.config import get_settings
from app.core.exceptions import ExtractionError
from app.core.logging import logger
from app.services.search import SearchResult, is_fetchable_url

# Conservative classification. A page is only labelled with a specific type when its
# domain supports it; everything else is a plain web article.
DOMAIN_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("Research paper", ("arxiv.org", "doi.org", "nature.com", "science.org",
                        "acm.org", "ieee.org", "springer.com", "sciencedirect.com")),
    ("Government", (".gov", ".mil", ".int", "who.int", "un.org", "europa.eu",
                    "nih.gov", "cdc.gov", "nist.gov")),
    ("Official documentation", ("docs.", "developer.", "readthedocs", "wikipedia.org")),
    ("News", ("reuters.com", "apnews.com", "bbc.co", "bbc.com", "nytimes.com",
              "theguardian.com", "washingtonpost.com", "ft.com")),
]
EDU_SUFFIXES = (".edu", ".ac.uk", ".ac.in", ".edu.au")


@dataclass
class RetrievedSource:
    """A source ready to be persisted and cited."""

    title: str
    url: str
    domain: str
    source_type: str
    snippet: str
    content: str
    retrieval_method: str
    search_score: float

    @property
    def text(self) -> str:
        """The best text available: scraped page if any, otherwise the search snippet."""
        return self.content or self.snippet


def classify_source_type(url: str, title: str = "") -> str:
    """Best-effort source-type label. Defaults to the honest generic answer."""
    if not url:
        return "Web article"
    host = urlparse(url).netloc.lower()
    if not host:
        return "Web article"

    bare = host[4:] if host.startswith("www.") else host
    if bare.endswith(EDU_SUFFIXES):
        return "Research paper"
    if any(part in bare for part in ("arxiv", "doi.org", "springer", "acm.org", "ieee")):
        return "Research paper"
    for label, markers in DOMAIN_PATTERNS:
        if any(marker in bare for marker in markers):
            return label
    return "Web article"


# Firecrawl annotates scraped markdown with markers such as 【2†L1-L4】 that point at
# links inside that one page. Those line references are meaningless once several pages are
# read together, and models copy them verbatim into the answer, displacing the real [n]
# citations. They are removed from every source before the model sees it.
FIRECRAWL_MARKER_RE = re.compile(r"【\d+†[^】]*】[ \t]*")


def clean_page_text(text: str) -> str:
    """Drop Firecrawl's inline link markers and collapse scraped boilerplate."""
    if not text:
        return ""
    text = FIRECRAWL_MARKER_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class ExtractionService:
    def __init__(self):
        settings = get_settings()
        self._api_key = settings.FIRECRAWL_API_KEY
        self._client = None
        self.max_sources = settings.MAX_EXTRACT_SOURCES
        self.max_source_chars = settings.MAX_SOURCE_CHARS

    async def extract(self, results: list[SearchResult]) -> list[RetrievedSource]:
        """Read the best pages, degrading any failure to that source's search snippet."""
        candidates = [r for r in results if is_fetchable_url(r.url)][: self.max_sources]
        if not candidates:
            raise ExtractionError(detail="no fetchable source URLs")

        settled = await asyncio.gather(
            *(self._extract_one(c) for c in candidates), return_exceptions=True
        )

        sources: list[RetrievedSource] = []
        for candidate, outcome in zip(candidates, settled):
            if isinstance(outcome, BaseException):
                logger.warning(
                    "Extraction failed, falling back to snippet",
                    data={"url": candidate.url, "error": type(outcome).__name__},
                )
                outcome = None
            if outcome is not None:
                sources.append(outcome)
            else:
                sources.append(self._from_snippet(candidate))

        # A source with neither scraped text nor a snippet carries no information.
        usable = [s for s in sources if s.text.strip()]
        if not usable:
            raise ExtractionError(detail="every source came back empty")
        return usable

    async def _extract_one(self, result: SearchResult) -> RetrievedSource | None:
        try:
            content = await self._scrape(result.url)
        except Exception as exc:
            logger.warning(
                "Firecrawl scrape failed",
                data={"url": result.url, "error": type(exc).__name__},
            )
            return None

        content = clean_page_text(content or "")[: self.max_source_chars]
        if not content:
            return None

        return RetrievedSource(
            title=result.title or result.url,
            url=result.url,
            domain=result.domain,
            source_type=classify_source_type(result.url, result.title),
            snippet=result.content[:1000],
            content=content,
            retrieval_method="firecrawl",
            search_score=result.score,
        )

    def _from_snippet(self, result: SearchResult) -> RetrievedSource:
        return RetrievedSource(
            title=result.title or result.url,
            url=result.url,
            domain=result.domain,
            source_type=classify_source_type(result.url, result.title),
            snippet=result.content[:1000],
            content="",
            retrieval_method="tavily_snippet",
            search_score=result.score,
        )

    async def _scrape(self, url: str) -> str:
        """Scrape one URL to markdown, bounded by SCRAPE_TIMEOUT."""
        if self._client is None:
            # Constructed lazily so importing this module never requires a key.
            from firecrawl import AsyncV1FirecrawlApp

            self._client = AsyncV1FirecrawlApp(api_key=self._api_key)

        response = await asyncio.wait_for(
            self._client.scrape_url(
                url, formats=["markdown"], only_main_content=True
            ),
            timeout=get_settings().SCRAPE_TIMEOUT,
        )
        return getattr(response, "markdown", None) or ""


extraction_service = ExtractionService()
