from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SearxngTool:
    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, query: str, limit: int = 5) -> list[dict]:
        if not self.settings.enable_searxng:
            return []
        try:
            response = httpx.get(
                f"{self.settings.searxng_url}/search",
                params={"q": query, "format": "json"},
                timeout=20,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            return results[:limit]
        except Exception as exc:
            logger.warning("SearXNG search failed: %s", exc)
            return []
