# browser-agent/agents/planner.py
import asyncio
import json
import requests
from typing import Optional
from models.schemas import TaskPlan, Subtask, AgentType
from models.prompts import PLANNER_PROMPT
from models.config import AgentConfig

class MasterPlanner:
    """Главный планировщик с интеграцией Llama через Ollama"""
    
    def __init__(self):
        self.config = AgentConfig()
        print("   [Planner] Инициализирован с моделью Llama 3.2")
    
    async def ask_llama(self, prompt: str, model: str = "llama3.2") -> str:
        """Запрос к локальной модели через Ollama API"""
        try:
            response = requests.post(
                f"{self.config.OLLAMA_CONFIG['base_url']}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 1000
                    }
                },
                timeout=self.config.OLLAMA_CONFIG['timeout']
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                print(f"   [Planner] Ошибка API: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"   [Planner] Ошибка подключения к Ollama: {e}")
            return ""
    
    async def create_plan(self, user_task: str, context_manager=None) -> TaskPlan:
        """Создает интеллектуальный план с помощью Llama"""
        print(f"   [Planner] Анализирую задачу: '{user_task}'")
        
        # 1. Подготовка промта
        prompt = f"""{PLANNER_PROMPT}

ПОЛЬЗОВАТЕЛЬСКАЯ ЗАДАЧА: {user_task}

Создай подробный план выполнения. Верни ТОЛЬКО JSON без пояснений.
"""
        
        # 2. Запрос к Llama
        print("   [Planner] Консультируюсь с Llama 3.2...")
        response = await self.ask_llama(prompt)
        
        # 3. Парсинг ответа
        plan_data = self._parse_llama_response(response, user_task)
        
        # 4. Преобразование в объект TaskPlan
        return self._create_task_plan(plan_data, user_task)
    
    def _parse_llama_response(self, response: str, user_task: str) -> dict:
        """Парсинг JSON из ответа Llama"""
        try:
            # Ищем JSON в ответе
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                plan_data = json.loads(json_str)
                print("   [Planner] Получен JSON план от Llama")
                return plan_data
        except json.JSONDecodeError as e:
            print(f"   [Planner] Ошибка парсинга JSON: {e}")
        
        # Fallback: если не удалось распарсить, создаем простой план
        print("   [Planner] Использую fallback-план")
        return self._create_fallback_plan(user_task)
    
    def _create_fallback_plan(self, user_task: str) -> dict:
        """Создание резервного плана"""
        return {
            "main_goal": f"Найти информацию: {user_task}",
            "assumptions": ["Браузер закрыт", "Есть доступ в интернет"],
            "subtasks": [
                {
                    "id": 1,
                    "description": f"Открыть поисковую систему Яндекс",
                    "agent_type": "navigator",
                    "success_criteria": "Страница поисковика загружена",
                    "potential_risks": ["Сайт недоступен", "Нет интернета"]
                },
                {
                    "id": 2,
                    "description": f"Ввести в поиск '{user_task}'",
                    "agent_type": "interactor",
                    "success_criteria": "Текст введен в поле поиска",
                    "potential_risks": ["Не найдено поле поиска"]
                },
                {
                    "id": 3,
                    "description": "Нажать кнопку поиска",
                    "agent_type": "interactor",
                    "success_criteria": "Выполнен поиск, показаны результаты",
                    "potential_risks": ["Кнопка не найдена"]
                },
                {
                    "id": 4,
                    "description": "Сохранить результаты поиска",
                    "agent_type": "interactor",
                    "success_criteria": "Информация сохранена в файл",
                    "potential_risks": ["Нет результатов"]
                }
            ],
            "dependencies": "Последовательное выполнение"
        }
    
    def _create_task_plan(self, plan_data: dict, user_task: str) -> TaskPlan:
        """Создание объекта TaskPlan из данных"""
        subtasks = []
        
        # Обработка подзадач
        for i, subtask_data in enumerate(plan_data.get("subtasks", []), 1):
            try:
                # Безопасное получение данных
                subtask_id = subtask_data.get("id", i)
                description = str(subtask_data.get("description", f"Подзадача {i}"))
                agent_type_str = str(subtask_data.get("agent_type", "navigator")).lower()
                success_criteria = str(subtask_data.get("success_criteria", f"Успешно выполнено: {description}"))
                
                # Преобразуем строковый agent_type в enum
                agent_type = AgentType.NAVIGATOR  # по умолчанию
                if agent_type_str == "interactor":
                    agent_type = AgentType.INTERACTOR
                elif agent_type_str == "validator":
                    agent_type = AgentType.VALIDATOR
                
                # Обработка потенциальных рисков (ИСПРАВЛЕННАЯ ЧАСТЬ!)
                potential_risks = subtask_data.get("potential_risks", [])
                if isinstance(potential_risks, str):
                    potential_risks = [potential_risks]
                elif not isinstance(potential_risks, list):
                    potential_risks = ["Неизвестные риски"]
                
                # Преобразуем все элементы списка в строки
                processed_risks = []
                for risk in potential_risks:
                    if isinstance(risk, dict):
                        # Если риск это словарь, берем первое значение
                        processed_risks.append(str(list(risk.values())[0]) if risk else "Неизвестный риск")
                    else:
                        processed_risks.append(str(risk))
                
                subtask = Subtask(
                    id=subtask_id,
                    description=description,
                    agent_type=agent_type,
                    success_criteria=success_criteria,
                    potential_risks=processed_risks
                )
                subtasks.append(subtask)
                
            except Exception as e:
                print(f"   [Planner] Ошибка создания подзадачи {i}: {e}")
                # Создаем минимальную подзадачу
                subtask = Subtask(
                    id=i,
                    description=f"Подзадача {i}",
                    agent_type=AgentType.NAVIGATOR,
                    success_criteria="Минимальные требования выполнены",
                    potential_risks=["Ошибка при создании плана"]
                )
                subtasks.append(subtask)
        
        # Обработка предположений (ИСПРАВЛЕННАЯ ЧАСТЬ!)
        assumptions = self._safe_process_assumptions(plan_data.get("assumptions", []))
        
        # Обработка зависимостей
        dependencies = plan_data.get("dependencies", "")
        if isinstance(dependencies, list):
            dependencies = "; ".join(str(dep) for dep in dependencies)
        
        # Создаем основной план
        return TaskPlan(
            main_goal=str(plan_data.get("main_goal", user_task)),
            assumptions=assumptions,
            subtasks=subtasks,
            dependencies=str(dependencies)
        )
    
    def _safe_process_assumptions(self, assumptions) -> list:
        """Безопасная обработка предположений"""
        result = []
        
        if isinstance(assumptions, str):
            result.append(assumptions)
        elif isinstance(assumptions, list):
            for item in assumptions:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict):
                    # Если это словарь, берем первое строковое значение
                    for value in item.values():
                        if isinstance(value, str):
                            result.append(value)
                            break
                else:
                    result.append(str(item))
        elif assumptions:
            result.append(str(assumptions))
        
        # Если нет предположений, добавляем стандартные
        if not result:
            result = ["Браузер закрыт", "Есть доступ в интернет"]
        
        return result
