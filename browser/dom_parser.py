# browser-agent/browser/dom_parser.py
import asyncio
from typing import Dict, Any, List, Optional
from playwright.async_api import Page

class DOMParser:
    """Парсер DOM для интеллектуального поиска элементов"""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def find_element_by_semantics(self, description: str) -> Dict[str, Any]:
        """Поиск элемента по семантическому описанию"""
        print(f"   [DOMParser] Ищу элемент: '{description}'")
        
        # Эвристики для разных типов элементов
        element_mappings = {
            # Поисковые поля
            'поиск': ['input[type="text"]', 'input[name="q"]', 'input[name="text"]', 'search', 'find'],
            'найти': ['input[type="text"]', 'button:has-text("Найти")', 'button:has-text("Search")'],
            
            # Кнопки
            'кнопка': ['button', 'input[type="button"]', 'input[type="submit"]', 'a.button'],
            'отправить': ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Отправить")'],
            'далее': ['button:has-text("Далее")', 'button:has-text("Next")', 'a:has-text("Продолжить")'],
            
            # Ссылки
            'ссылка': ['a', 'a[href]', 'link'],
            'подробнее': ['a:has-text("Подробнее")', 'a:has-text("More")'],
            
            # Формы
            'форма': ['form', 'div.form', 'section.form'],
            'логин': ['input[name="login"]', 'input[name="username"]', '#username', '#login'],
            'пароль': ['input[type="password"]', 'input[name="password"]', '#password'],
        }
        
        desc_lower = description.lower()
        found_elements = []
        
        # Поиск по ключевым словам
        for keyword, selectors in element_mappings.items():
            if keyword in desc_lower:
                for selector in selectors:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            element_info = await self._get_element_info(element)
                            element_info['confidence'] = 0.7
                            found_elements.append(element_info)
        
        # Если не нашли по ключевым словам, ищем по общим селекторам
        if not found_elements:
            general_selectors = [
                'button', 'input', 'a', 'div[role="button"]',
                'button:visible', 'input:visible', 'a:visible'
            ]
            
            for selector in general_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        element_text = await element.text_content() or ""
                        element_text_lower = element_text.lower()
                        
                        # Проверяем, соответствует ли текст элемента описанию
                        if any(word in element_text_lower for word in desc_lower.split()[:3]):
                            element_info = await self._get_element_info(element)
                            element_info['confidence'] = 0.5
                            found_elements.append(element_info)
        
        # Выбираем элемент с наибольшей уверенностью
        if found_elements:
            found_elements.sort(key=lambda x: x['confidence'], reverse=True)
            return {
                'found': True,
                'element': found_elements[0],
                'alternatives': found_elements[1:3]
            }
        
        return {
            'found': False,
            'message': f"Элемент не найден по описанию: '{description}'"
        }
    
    async def _get_element_info(self, element) -> Dict[str, Any]:
        """Получение информации об элементе"""
        try:
            # Получаем координаты
            box = await element.bounding_box()
            
            # Получаем атрибуты
            tag_name = await element.evaluate("el => el.tagName")
            element_id = await element.get_attribute('id') or ''
            element_class = await element.get_attribute('class') or ''
            element_text = await element.text_content() or ''
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()
            
            return {
                'tag': tag_name.lower(),
                'text': element_text.strip()[:100],
                'attributes': {
                    'id': element_id,
                    'class': element_class,
                    'type': await element.get_attribute('type') or ''
                },
                'coordinates': {
                    'x': int(box['x'] + box['width'] / 2) if box else 0,
                    'y': int(box['y'] + box['height'] / 2) if box else 0
                },
                'size': {
                    'width': int(box['width']) if box else 0,
                    'height': int(box['height']) if box else 0
                },
                'is_visible': is_visible,
                'is_interactable': is_visible and is_enabled
            }
        except Exception as e:
            return {
                'tag': 'unknown',
                'text': '',
                'attributes': {},
                'coordinates': {'x': 0, 'y': 0},
                'size': {'width': 0, 'height': 0},
                'is_visible': False,
                'is_interactable': False,
                'error': str(e)
            }
    
    async def get_page_structure(self) -> Dict[str, Any]:
        """Получение структуры страницы"""
        try:
            # Получаем основные элементы страницы
            buttons = await self.page.query_selector_all('button:visible')
            inputs = await self.page.query_selector_all('input:visible, textarea:visible')
            links = await self.page.query_selector_all('a:visible')
            
            # Анализируем структуру
            structure = {
                'title': await self.page.title(),
                'url': self.page.url,
                'elements_count': {
                    'buttons': len(buttons),
                    'inputs': len(inputs),
                    'links': len(links)
                },
                'main_sections': await self._extract_main_sections(),
                'interactive_elements': []
            }
            
            # Собираем информацию об интерактивных элементах
            for element in buttons[:10]:  # Ограничиваем количество
                info = await self._get_element_info(element)
                if info['is_interactable']:
                    structure['interactive_elements'].append(info)
            
            return structure
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _extract_main_sections(self) -> List[Dict[str, Any]]:
        """Извлечение основных секций страницы"""
        sections = []
        
        # Ищем основные структурные элементы
        section_selectors = [
            'header', 'nav', 'main', 'section', 'article',
            'aside', 'footer', 'div[role="main"]', 'div.main'
        ]
        
        for selector in section_selectors:
            elements = await self.page.query_selector_all(selector)
            for element in elements[:3]:  # Берем первые 3 каждого типа
                if await element.is_visible():
                    try:
                        text = await element.text_content() or ""
                        sections.append({
                            'type': selector,
                            'text_preview': text[:200].strip(),
                            'visible': True
                        })
                    except:
                        pass
        
        return sections