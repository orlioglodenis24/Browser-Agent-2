# browser-agent/browser/vision.py
import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
import tempfile
import os

class VisionAnalyzer:
    """Анализатор компьютерного зрения для поиска элементов"""
    
    def __init__(self):
        print("   [Vision] Инициализирован анализатор компьютерного зрения")
    
    async def find_element_on_screenshot(self, 
                                       screenshot_path: str, 
                                       element_description: str) -> Dict[str, Any]:
        """Поиск элемента на скриншоте"""
        print(f"   [Vision] Ищу '{element_description}' на скриншоте...")
        
        try:
            # Загружаем изображение
            image = cv2.imread(screenshot_path)
            if image is None:
                return {'found': False, 'error': 'Не удалось загрузить изображение'}
            
            # В зависимости от описания, используем разные методы поиска
            if any(word in element_description.lower() for word in ['кнопка', 'button']):
                return await self._find_button(image, element_description)
            elif any(word in element_description.lower() for word in ['поле', 'input', 'ввод']):
                return await self._find_input_field(image)
            elif any(word in element_description.lower() for word in ['текст', 'text', 'надпись']):
                return await self._find_text(image, element_description)
            else:
                return await self._find_by_template(image, element_description)
                
        except Exception as e:
            return {'found': False, 'error': str(e)}
    
    async def _find_button(self, image: np.ndarray, description: str) -> Dict[str, Any]:
        """Поиск кнопок на изображении"""
        # Конвертируем в grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Применяем детектор границ
        edges = cv2.Canny(gray, 50, 150)
        
        # Находим контуры
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        buttons = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Фильтруем по размеру (исключаем слишком мелкие и слишком крупные)
            if 50 < w < 500 and 20 < h < 100:
                # Вычисляем соотношение сторон (кнопки обычно прямоугольные)
                aspect_ratio = w / h
                if 1.5 < aspect_ratio < 6:  # Типичное соотношение для кнопок
                    buttons.append({
                        'x': x + w // 2,
                        'y': y + h // 2,
                        'width': w,
                        'height': h,
                        'confidence': 0.7,
                        'type': 'button'
                    })
        
        if buttons:
            # Выбираем кнопку ближе к центру снизу (типичное расположение кнопок отправки)
            height, width = image.shape[:2]
            center_x, center_y = width // 2, height * 3 // 4
            
            # Находим ближайшую к ожидаемой позиции
            buttons.sort(key=lambda b: abs(b['x'] - center_x) + abs(b['y'] - center_y))
            
            return {
                'found': True,
                'element': buttons[0],
                'alternatives': buttons[1:3],
                'method': 'edge_detection'
            }
        
        return {'found': False, 'message': 'Кнопки не найдены'}
    
    async def _find_input_field(self, image: np.ndarray) -> Dict[str, Any]:
        """Поиск полей ввода"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Бинаризация для поиска прямоугольных областей
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Морфологические операции для улучшения
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        input_fields = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Поля ввода обычно шире, чем выше
            if w > h * 2 and 100 < w < 800 and 20 < h < 60:
                input_fields.append({
                    'x': x + w // 2,
                    'y': y + h // 2,
                    'width': w,
                    'height': h,
                    'confidence': 0.6,
                    'type': 'input_field'
                })
        
        if input_fields:
            # Сортируем по положению (обычно поле поиска вверху)
            input_fields.sort(key=lambda f: f['y'])
            return {
                'found': True,
                'element': input_fields[0],
                'alternatives': input_fields[1:3]
            }
        
        return {'found': False, 'message': 'Поля ввода не найдены'}
    
    async def _find_text(self, image: np.ndarray, text_description: str) -> Dict[str, Any]:
        """Поиск текста (упрощенная версия)"""
        # В реальном проекте здесь бы использовался Tesseract OCR
        # Для демонстрации возвращаем фиктивный результат
        
        height, width = image.shape[:2]
        
        # Ищем в типичных местах для текста
        search_regions = [
            (width // 2, height // 4),    # Верхняя часть
            (width // 2, height // 2),    # Центр
            (width // 2, height * 3 // 4) # Нижняя часть
        ]
        
        # Для демонстрации возвращаем первую область
        return {
            'found': True,
            'element': {
                'x': search_regions[0][0],
                'y': search_regions[0][1],
                'confidence': 0.3,
                'type': 'text_region',
                'note': 'Используйте OCR (Tesseract) для реального распознавания текста'
            }
        }
    
    async def _find_by_template(self, image: np.ndarray, description: str) -> Dict[str, Any]:
        """Поиск по шаблону (заглушка для демонстрации)"""
        return {
            'found': False,
            'message': f'Для поиска "{description}" требуется предобученный шаблон',
            'recommendation': 'Добавьте шаблоны для часто используемых элементов'
        }
    
    def save_debug_image(self, image: np.ndarray, elements: list, output_path: str):
        """Сохранение отладочного изображения с выделенными элементами"""
        debug_image = image.copy()
        
        for element in elements:
            x, y = element.get('x', 0), element.get('y', 0)
            w, h = element.get('width', 50), element.get('height', 30)
            
            # Рисуем прямоугольник
            cv2.rectangle(debug_image, 
                         (x - w // 2, y - h // 2),
                         (x + w // 2, y + h // 2),
                         (0, 255, 0), 2)
            
            # Рисуем точку в центре
            cv2.circle(debug_image, (x, y), 5, (0, 0, 255), -1)
            
            # Добавляем текст
            cv2.putText(debug_image, element.get('type', 'element'),
                       (x - w // 2, y - h // 2 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        cv2.imwrite(output_path, debug_image)
        print(f"   [Vision] Отладочное изображение сохранено: {output_path}")