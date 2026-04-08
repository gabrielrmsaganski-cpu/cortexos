from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class PlaywrightTool:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def render(self, url: str) -> dict:
        if not self.settings.enable_playwright:
            return {"url": url, "text": "", "html": "", "available": False}
        try:
            from playwright.async_api import async_playwright  # type: ignore

            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=60_000)
                text = await page.locator("body").inner_text()
                html = await page.content()
                await browser.close()
            return {"url": url, "text": text, "html": html, "available": True}
        except Exception as exc:
            logger.warning("Playwright render failed: %s", exc)
            return {"url": url, "text": "", "html": "", "available": False, "error": str(exc)}
