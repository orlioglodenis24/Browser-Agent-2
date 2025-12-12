# browser-agent/agents/navigator.py
import asyncio
import re
from typing import Dict, Any
from models.schemas import Subtask
from browser.controller import BrowserController


class NavigationAgent:
    """Простой агент навигации: открывает URL и делает скриншот"""

    def __init__(self, browser_controller: BrowserController = None):
        self.browser = browser_controller or BrowserController()
        print("   [Navigator] Агент навигации инициализирован")

    async def execute_subtask(self, subtask: Subtask) -> Dict[str, Any]:
        print(f"   [Navigator] Выполняю: '{subtask.description}'")
        result = {
            'success': False,
            'action': 'navigate',
            'details': {},
            'error': None
        }
        try:
            target_url = self._extract_url_from_description(subtask.description)
            if not target_url:
                result['error'] = f"Не удалось определить URL из описания: {subtask.description}"
                return result
            success = await self.browser.navigate(target_url)
            if not success:
                result['error'] = "Не удалось загрузить страницу"
                return result
            page_info = await self.browser.get_page_info()
            screenshot = await self.browser.take_screenshot(f"step_{subtask.id}_navigation.png")
            result.update({
                'success': True,
                'details': {
                    'url': page_info.get('url', ''),
                    'title': page_info.get('title', ''),
                    'screenshot': screenshot
                }
            })
            print(f"   [Navigator] ✅ {subtask.success_criteria}")
        except Exception as e:
            result['error'] = str(e)
            print(f"   [Navigator] ❌ Ошибка: {e}")
        return result

    def _extract_url_from_description(self, description: str) -> str:
        """Извлечение URL из описания задачи"""
        url_patterns = [r'https?://[^\s]+', r'www\.[^\s\.]+\.[^\s]+']
        for pattern in url_patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(0)

        # Простые эвристики для ключевых слов
        desc_lower = description.lower()
        if 'hh.ru' in desc_lower or 'headhunter' in desc_lower:
            return 'https://hh.ru'
        if 'yandex' in desc_lower or 'яндекс' in desc_lower:
            return 'https://yandex.ru'
        if 'youtube' in desc_lower:
            return 'https://www.youtube.com'
        if 'google' in desc_lower:
            return 'https://www.google.com'

        # По умолчанию — поисковая страница
        return 'https://yandex.ru'
