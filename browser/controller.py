"""browser-agent/browser/controller.py

Clean Playwright-only BrowserController implementation.
"""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser, Playwright
from models.config import AgentConfig


class BrowserController:
    """Minimal Playwright-based browser controller."""

    def __init__(self):
        self.config = AgentConfig()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_running = False

    async def launch(self) -> Page:
        if self.is_running and self.page:
            return self.page

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.BROWSER_CONFIG.get('headless', False),
            slow_mo=self.config.BROWSER_CONFIG.get('slow_mo', 0),
            args=self.config.BROWSER_CONFIG.get('args', [])
        )
        self.page = await self.browser.new_page()
        try:
            await self.page.set_viewport_size(self.config.BROWSER_CONFIG.get('viewport', {"width": 1280, "height": 720}))
        except Exception:
            pass
        self.is_running = True
        return self.page

    async def navigate(self, url: str) -> bool:
        if not self.page:
            await self.launch()
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        try:
            response = await self.page.goto(url, wait_until='domcontentloaded', timeout=self.config.BROWSER_CONFIG.get('timeout', 15000))
            await asyncio.sleep(self.config.NAVIGATION_CONFIG.get('default_wait_time', 1))
            return bool(response and response.ok)
        except Exception:
            try:
                await self.page.goto(url, wait_until='load', timeout=self.config.BROWSER_CONFIG.get('timeout', 15000))
                return True
            except Exception:
                return False

    async def take_screenshot(self, filename: Optional[str] = None) -> Optional[str]:
        if not self.page:
            return None
        if not filename:
            import datetime
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        try:
            await self.page.screenshot(path=filename, full_page=True)
            return filename
        except Exception:
            return None

    async def get_page_info(self) -> dict:
        if not self.page:
            return {}
        return {
            'url': self.page.url,
            'title': await self.page.title(),
            'html_length': len(await self.page.content())
        }

    async def close(self):
        try:
            if self.browser:
                await self.browser.close()
        except Exception:
            pass
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
        self.is_running = False

    async def open_new_tab(self, url: str) -> Optional[Page]:
        """Open a new tab (page) and navigate to `url`. Returns the new Page or None."""
        try:
            if not self.browser:
                await self.launch()
            new_page = await self.browser.new_page()
            await new_page.goto(url, wait_until='domcontentloaded', timeout=self.config.BROWSER_CONFIG.get('timeout', 15000))
            return new_page
        except Exception:
            return None
