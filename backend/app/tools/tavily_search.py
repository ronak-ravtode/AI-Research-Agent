from tavily import AsyncTavilyClient
from dataclasses import dataclass
from app.core.config import get_settings
from typing import Optional


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float
    domain: Optional[str] = None


class TavilySearch:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    async def search_web(
        self,
        query: str,
        max_results: int = 8,
    ) -> list[SearchResult]:
        response = await self.client.search(
            query=query,
            max_results=max_results,
            include_answer=False,
        )

        results = []
        for item in response.get("results", []):
            url = item.get("url", "")
            domain = None
            if url:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc

            results.append(SearchResult(
                title=item.get("title", ""),
                url=url,
                content=item.get("content", ""),
                score=item.get("score", 0.0),
                domain=domain,
            ))

        return results


tavily_search = TavilySearch()
