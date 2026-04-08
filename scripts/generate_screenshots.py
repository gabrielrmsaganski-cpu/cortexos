from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from playwright.async_api import async_playwright


ROOT = Path("/home/saganski/workspace/experiments/cortexos")
OUTPUT = ROOT / "screenshots"
BASE_URL = "http://127.0.0.1:8011"


async def capture(page, route: str, filename: str, wait_for: str) -> None:
    await page.goto(f"{BASE_URL}{route}", wait_until="networkidle")
    await page.wait_for_timeout(1200)
    await page.get_by_text(wait_for, exact=False).first.wait_for(timeout=10000)
    await page.screenshot(path=str(OUTPUT / filename), full_page=True)


async def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    chrome_path = shutil.which("google-chrome")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            executable_path=chrome_path,
        )
        page = await browser.new_page(viewport={"width": 1600, "height": 1100})
        await capture(page, "/", "dashboard.png", "Product Console")
        await capture(page, "/query", "query.png", "Query Studio")
        await capture(page, "/explain", "explain.png", "Explain Center")
        await capture(page, "/conflicts", "conflict.png", "Conflict Center")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
