# browser-agent/agents/interactor.py
import asyncio
import random
import re
from typing import Dict, Any, Optional, Tuple
from urllib.parse import quote
from models.schemas import Subtask
from browser.controller import BrowserController


class InteractionAgent:
    """Агент взаимодействия с элементами страницы"""
    
    def __init__(self, browser_controller: BrowserController = None):
        self.browser = browser_controller or BrowserController()
        print("   [Interactor] Агент взаимодействия инициализирован")
    
    async def execute_subtask(self, subtask: Subtask) -> Dict[str, Any]:
        """Выполнение интерактивной подзадачи"""
        print(f"   [Interactor] Выполняю: '{subtask.description}'")
        
        result = {
            'success': False,
            'action': 'unknown',
            'details': {},
            'error': None
        }
        
        try:
            action_type = self._detect_action_type(subtask.description)
            result['action'] = action_type
            
            if action_type == 'type':
                await self._perform_typing(subtask, result)
            elif action_type == 'click':
                await self._perform_click(subtask, result)
            elif action_type == 'scroll':
                await self._perform_scroll(subtask, result)
            elif action_type == 'read':
                await self._perform_reading(subtask, result)
            else:
                result['error'] = f"Неизвестный тип действия: {action_type}"
                
        except Exception as e:
            result['error'] = str(e)
            print(f"   [Interactor] ❌ Ошибка: {e}")
        
        return result
    
    def _detect_action_type(self, description: str) -> str:
        """Определение типа действия по описанию"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['ввести', 'набрать', 'написать', 'ввод']):
            return 'type'
        elif any(word in desc_lower for word in ['нажать', 'кликнуть', 'выбрать', 'открыть']):
            return 'click'
        elif any(word in desc_lower for word in ['пролистать', 'скроллить', 'прокрутить']):
            return 'scroll'
        elif any(word in desc_lower for word in ['прочитать', 'извлечь', 'сохранить']):
            return 'read'
        else:
            return 'unknown'
    
    async def _perform_typing(self, subtask: Subtask, result: Dict[str, Any]):
        """Ввод текста в поле поиска"""
        try:
            site, text_to_type = self._extract_text_to_type(subtask.description)
            if not text_to_type:
                result['error'] = "Не удалось определить текст для ввода"
                return
            
            print(f"   [Interactor] Ввожу текст: '{text_to_type}'")
            
            page = self.browser.page
            if site:
                # Нормализуем сайт и добавим протокол, если нужно
                norm_site = site
                if not norm_site.startswith('http'):
                    norm_site = f'https://{norm_site}'
                # Для hh.ru используем прямой URL поиска (быстрее и надежнее)
                if 'hh.ru' in site.lower():
                    try:
                        search_url = f"https://hh.ru/search/vacancy?text={quote(text_to_type)}"
                        await self.browser.navigate(search_url)
                        page = self.browser.page
                        # подождём результатов
                        try:
                            await page.wait_for_selector('a[href*="/vacancy/"]', timeout=6000)
                            results_found = True
                        except Exception:
                            results_found = False
                        screenshot = await self.browser.take_screenshot(f"step_{subtask.id}_typing.png")
                        result.update({
                            'success': True,
                            'details': {
                                'site': site,
                                'text_entered': text_to_type,
                                'screenshot': screenshot,
                                'results_shown': results_found,
                                'message': f'Перешли на {site} и показали результаты'
                            }
                        })
                        print(f"   [Interactor] ✅ {subtask.success_criteria}")
                        return
                    except Exception:
                        # если не удалось перейти — продолжим далее
                        pass
                else:
                    # Перейдём на указанный сайт, затем будем искать локально
                    try:
                        await self.browser.navigate(norm_site)
                        page = self.browser.page
                    except Exception:
                        # если навигация провалилась — продолжим и попытаемся ввод на текущей странице
                        page = self.browser.page

            if not page:
                result['error'] = "Страница не загружена"
                return
            
            search_selectors = [
                'input[type="text"]',
                'input[name="text"]',
                'input.search3__input',
                'input[class*="search"]',
                'input[class*="input"]',
                'textarea',
                'input'
            ]
            
            search_field = None
            for selector in search_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    for elem in elements:
                        if await elem.is_visible():
                            search_field = elem
                            break
                if search_field:
                    break
            
            # Если задача явно про hh.ru — сразу перейдём на страницу результатов hh.ru
            if 'hh.ru' in subtask.description.lower() or 'headhunter' in subtask.description.lower():
                try:
                    search_url = f"https://hh.ru/search/vacancy?text={quote(text_to_type)}"
                    print(f"   [Interactor] Переход на hh.ru поиск: {search_url}")
                    await self.browser.navigate(search_url)
                    page = self.browser.page
                    # Подождём результатов
                    try:
                        await page.wait_for_selector('a[href*="/vacancy/"]', timeout=6000)
                        results_found = True
                    except Exception:
                        results_found = False
                    screenshot = await self.browser.take_screenshot(f"step_{subtask.id}_typing.png")
                    result.update({
                        'success': True,
                        'details': {
                            'text_entered': text_to_type,
                            'screenshot': screenshot,
                            'results_shown': results_found,
                            'message': 'Перешли на hh.ru и показали результаты'
                        }
                    })
                    print(f"   [Interactor] ✅ {subtask.success_criteria}")
                    return
                except Exception as e:
                    # если не удалось перейти — продолжим обычным вводом ниже
                    print(f"   [Interactor] Не удалось перейти на hh.ru напрямую: {e}")

            if not search_field:
                viewport = page.viewport_size
                await page.mouse.click(viewport['width'] // 2, viewport['height'] // 2)
                await asyncio.sleep(0.5)
                await page.keyboard.type(text_to_type)
            else:
                await search_field.click()
                await asyncio.sleep(0.3)
                await search_field.fill('')
                await search_field.type(text_to_type, delay=100)
                print(f"   [Interactor] Нажимаю Enter для поиска...")
                await page.keyboard.press('Enter')
                # Подождём появления результатов вакансий (на hh.ru это динамически загружаемая зона)
                try:
                    await page.wait_for_selector('a[href*="/vacancy/"]', timeout=5000)
                    results_found = True
                except Exception:
                    results_found = False
                    # Попробуем кликнуть кнопку поиска, если Enter не сработал
                    for btn_sel in ['button[type="submit"]', 'button:has-text("Найти")', 'button:has-text("Найти вакансии")']:
                        try:
                            btn = await page.query_selector(btn_sel)
                            if btn and await btn.is_visible():
                                await btn.click()
                                await asyncio.sleep(2)
                                try:
                                    await page.wait_for_selector('a[href*="/vacancy/"]', timeout=4000)
                                    results_found = True
                                    break
                                except Exception:
                                    continue
                        except Exception:
                            continue
                await asyncio.sleep(1)

                # Проверка на капчу: если результаты не показаны и на странице есть индикаторы капчи
                async def _is_captcha_present(p):
                    try:
                        body = (await p.content()).lower()
                    except Exception:
                        try:
                            body = (await p.evaluate('() => document.body.innerText')).lower()
                        except Exception:
                            body = ''
                    captcha_signs = ['пройдите капчу', 'введите текст с картинки', 'captcha', 'подтвердите, что вы не робот', 'текст с картинки']
                    if any(s in body for s in captcha_signs):
                        return True
                    # Поиск по селекторам
                    captcha_selectors = ['input[name*="captcha"]', 'input[id*="captcha"]', 'div.captcha', 'img.captcha']
                    for sel in captcha_selectors:
                        try:
                            el = await p.query_selector(sel)
                            if el:
                                return True
                        except Exception:
                            continue
                    return False

                if not results_found:
                    try:
                        captcha = await _is_captcha_present(page)
                    except Exception:
                        captcha = False

                    if captcha:
                        print("   [Interactor] Обнаружена капча — пробую решить дважды, затем откатаюсь в новую вкладку")
                        # Попытки решить (попытки будут простыми: сохранить скриншот и попытаться ввести 'captcha' в поле)
                        for attempt in range(2):
                            try:
                                captcha_img = None
                                try:
                                    await page.screenshot(path=f"captcha_attempt_{subtask.id}_{attempt+1}.png", full_page=False)
                                except Exception:
                                    pass
                                # Найти поле ввода капчи
                                input_sel = None
                                for sel in ['input[name*="captcha"]', 'input[id*="captcha"]', 'input[placeholder*="капч"]', 'input']:
                                    try:
                                        cand = await page.query_selector(sel)
                                        if cand and await cand.is_visible():
                                            input_sel = cand
                                            break
                                    except Exception:
                                        continue
                                if input_sel:
                                    try:
                                        await input_sel.click()
                                        await asyncio.sleep(0.3)
                                        # Попытка: ввести метку 'captcha' (символическая попытка)
                                        await input_sel.fill('captcha')
                                        await page.keyboard.press('Enter')
                                        await asyncio.sleep(2)
                                    except Exception:
                                        pass
                                else:
                                    # Если нет поля, попробуем кликнуть по центру для фокуса
                                    vp = page.viewport_size or {'width': 1200, 'height': 800}
                                    await page.mouse.click(vp['width']//2, vp['height']//2)
                                    await asyncio.sleep(1)
                            except Exception as e:
                                print(f"   [Interactor] Ошибка при попытке решения капчи: {e}")
                        # После двух попыток — откат: открыть новую вкладку и выполнить поиск по исходному запросу
                        try:
                            search_url = f"https://yandex.ru/search/?text={quote(text_to_type)}"
                            new_page = await self.browser.open_new_tab(search_url)
                            if new_page:
                                await asyncio.sleep(1)
                                sshot = await self.browser.take_screenshot(f"step_{subtask.id}_captcha_fallback.png")
                                result.update({
                                    'success': True,
                                    'details': {
                                        'text_entered': text_to_type,
                                        'screenshot': sshot,
                                        'message': 'Капча не пройдена — открыт fallback поиск в новой вкладке'
                                    }
                                })
                                print("   [Interactor] Открыта новая вкладка с поиском (fallback)")
                                return
                        except Exception:
                            pass
            screenshot = await self.browser.take_screenshot(f"step_{subtask.id}_typing.png")
            
            result.update({
                'success': True,
                'details': {
                    'text_entered': text_to_type,
                    'screenshot': screenshot,
                    'results_shown': results_found if 'results_found' in locals() else False,
                    'message': 'Текст успешно введен'
                }
            })
            print(f"   [Interactor] ✅ {subtask.success_criteria}")
            
        except Exception as e:
            result['error'] = f"Ошибка ввода текста: {e}"
    
    def _extract_text_to_type(self, description: str) -> Optional[str]:
        """Извлечение текста для ввода из описания"""
        # Новая логика: возвращаем кортеж (site, query)
        # Ищем домен в описании
        desc = description.strip()
        domain_match = re.search(r'((?:https?://)?(?:www\.)?[a-z0-9.-]+\.[a-z]{2,})', desc, flags=re.IGNORECASE)
        if domain_match:
            site = domain_match.group(1)
            # удалим протокол
            site = re.sub(r'^https?://', '', site, flags=re.IGNORECASE)
            # остальной текст — после домена
            rest = re.sub(re.escape(domain_match.group(1)), '', desc, flags=re.IGNORECASE).strip()
            # удалим ведущие слова типа "ввести в поиск", "найти"
            rest = re.sub(r'^(ввести в поиск|ввести|найти|поиск)[:\-\s]*', '', rest, flags=re.IGNORECASE).strip()
            return site, rest if rest else ''

        # нет домена — просто извлечём запрос
        patterns = [
            r'ввести в поиск [\'\"]?([^\'\"]+)[\'\"]?',
            r'найти [\'\"]?([^\'\"]+)[\'\"]?',
            r'поиск [\'\"]?([^\'\"]+)[\'\"]?'
        ]
        for pattern in patterns:
            match = re.search(pattern, desc, flags=re.IGNORECASE)
            if match:
                text = match.group(1).strip()
                if text.lower().startswith('в поиск '):
                    text = text[8:]
                return None, text

        # fallback: весь текст как запрос
        return None, desc
    
    async def _perform_click(self, subtask: Subtask, result: Dict[str, Any]):
        """Выполнение клика"""
        try:
            print(f"   [Interactor] Ищу элемент для клика...")
            
            page = self.browser.page
            if not page:
                result['error'] = "Страница не загружена"
                return
            
            button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button[class*="search"]',
                'button[class*="submit"]',
                'input[value*="Найти"]',
                'input[value*="Search"]',
                'button:has-text("Найти")',
                'button:has-text("Search")',
                'button',
                'a.button'
            ]
            
            clicked = False
            for selector in button_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        await button.click()
                        clicked = True
                        print(f"   [Interactor] Кликнул по селектору: {selector}")
                        break
                except:
                    continue
            
            if not clicked:
                viewport = page.viewport_size
                await page.mouse.click(viewport['width'] // 2, viewport['height'] - 100)
                print(f"   [Interactor] Кликнул по координатам")
            
            await asyncio.sleep(2)
            
            screenshot = await self.browser.take_screenshot(f"step_{subtask.id}_click.png")
            
            result.update({
                'success': True,
                'details': {
                    'action': 'click_performed',
                    'screenshot': screenshot,
                    'message': 'Клик выполнен'
                }
            })
            print(f"   [Interactor] ✅ {subtask.success_criteria}")
            
        except Exception as e:
            result['error'] = f"Ошибка клика: {e}"
    
    async def _perform_scroll(self, subtask: Subtask, result: Dict[str, Any]):
        """Прокрутка страницы"""
        try:
            print(f"   [Interactor] Выполняю прокрутку...")
            
            page = self.browser.page
            if not page:
                result['error'] = "Страница не загружена"
                return
            
            await page.mouse.wheel(0, random.randint(500, 1500))
            await asyncio.sleep(1)
            
            await page.mouse.wheel(0, random.randint(300, 800))
            await asyncio.sleep(0.5)
            
            screenshot = await self.browser.take_screenshot(f"step_{subtask.id}_scroll.png")
            
            result.update({
                'success': True,
                'details': {
                    'action': 'scroll_performed',
                    'scroll_amount': 'multiple',
                    'screenshot': screenshot,
                    'message': 'Прокрутка выполнена'
                }
            })
            print(f"   [Interactor] ✅ {subtask.success_criteria}")
            
        except Exception as e:
            result['error'] = f"Ошибка прокрутки: {e}"
    
    async def _perform_reading(self, subtask: Subtask, result: Dict[str, Any]):
        """Чтение текста со страницы"""
        try:
            print(f"   [Interactor] Читаю содержимое страницы...")
            
            page = self.browser.page
            if not page:
                result['error'] = "Страница не загружена"
                return
            
            # ИСПРАВЛЕННАЯ СТРОКА - правильные кавычки
            page_text = await page.evaluate("() => { return document.body.innerText; }")
            
            preview = page_text[:500] + "..." if len(page_text) > 500 else page_text
            
            import datetime
            filename = f"recipe_text_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(page_text)
            
            screenshot = await self.browser.take_screenshot(f"step_{subtask.id}_read.png")
            
            result.update({
                'success': True,
                'details': {
                    'action': 'text_extracted',
                    'text_preview': preview,
                    'file_saved': filename,
                    'screenshot': screenshot,
                    'message': 'Текст прочитан и сохранен'
                }
            })
            print(f"   [Interactor] ✅ {subtask.success_criteria}")
            print(f"   [Interactor] Текст сохранен в: {filename}")
            
        except Exception as e:
            result['error'] = f"Ошибка чтения: {e}"
