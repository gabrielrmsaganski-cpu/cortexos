from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Crawl4AITool:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch_page(self, url: str) -> dict:
        if not self.settings.enable_crawl4ai:
            return {"url": url, "markdown": "", "available": False}
        try:
            from crawl4ai import AsyncWebCrawler  # type: ignore

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
            return {
                "url": url,
                "markdown": getattr(result, "markdown", ""),
                "html": getattr(result, "html", ""),
                "available": True,
            }
        except Exception as exc:
            logger.warning("Crawl4AI page fetch failed: %s", exc)
            return {"url": url, "markdown": "", "available": False, "error": str(exc)}

    async def crawl_site(self, url: str, max_pages: int = 5) -> list[dict]:
        pages: list[dict] = []
        first = await self.fetch_page(url)
        if first.get("available"):
            pages.append(first)
        return pages[:max_pages]
