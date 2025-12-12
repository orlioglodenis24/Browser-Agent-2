"""Небольшой тестовый скрипт для Playwright.

Запускает Chromium, открывает example.com, делает скриншот и печатает заголовок.
"""

import asyncio
from playwright.async_api import async_playwright


async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://example.com")
        title = await page.title()
        print(f"✅ Браузер работает! Заголовок: {title}")
        try:
            await page.screenshot(path="test_success.png")
        except Exception:
            pass
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test())