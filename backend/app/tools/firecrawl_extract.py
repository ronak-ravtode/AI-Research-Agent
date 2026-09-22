import asyncio
from firecrawl import FirecrawlApp
from dataclasses import dataclass
from app.core.config import get_settings
from typing import Optional


@dataclass
class ExtractedContent:
    url: str
    title: Optional[str]
    content: str
    markdown: Optional[str] = None


class FirecrawlExtract:
    def __init__(self):
        self._app = None

    @property
    def app(self):
        if self._app is None:
            settings = get_settings()
            self._app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
        return self._app

    async def extract_url(self, url: str) -> ExtractedContent:
        try:
            result = await asyncio.to_thread(
                self.app.scrape_url, url, params={"formats": ["markdown"]}
            )

            return ExtractedContent(
                url=url,
                title=result.get("metadata", {}).get("title"),
                content=result.get("markdown", result.get("content", "")),
                markdown=result.get("markdown"),
            )
        except Exception as e:
            return ExtractedContent(
                url=url,
                title=None,
                content=f"Extraction failed: {str(e)}",
            )


firecrawl_extract = FirecrawlExtract()
