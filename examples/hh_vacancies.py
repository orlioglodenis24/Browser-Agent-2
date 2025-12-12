# browser-agent/examples/hh_vacancies.py
import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

from agents.planner import MasterPlanner
from agents.navigator import NavigationAgent
from agents.interactor import InteractionAgent
from agents.validator import ValidationAgent
from agents.context_manager import ContextManager
from browser.controller import BrowserController

async def run_hh_vacancy_scenario():
    """Пример сценария: поиск вакансий на hh.ru"""
    print("🎯 ДЕМОНСТРАЦИОННЫЙ СЦЕНАРИЙ: Поиск вакансий на hh.ru")
    print("=" * 60)
    
    # Инициализация
    context_mgr = ContextManager()
    browser_controller = BrowserController()
    
    # Создаем агентов
    navigator = NavigationAgent(browser_controller)
    interactor = InteractionAgent(browser_controller)
    validator = ValidationAgent()
    
    # Задача пользователя
    user_task = "Найди 3 подходящие вакансии Python разработчика на hh.ru"
    
    print(f"\n📋 Задача: {user_task}")
    
    # Планирование
    planner = MasterPlanner()
    plan = await planner.create_plan(user_task, context_mgr)
    
    print(f"\n📊 Получен план из {len(plan.subtasks)} подзадач:")
    for i, subtask in enumerate(plan.subtasks, 1):
        print(f"   {i}. [{subtask.agent_type.value}] {subtask.description}")
    
    # Выполнение плана
    results = []
    
    for subtask in plan.subtasks:
        print(f"\n{'='*50}")
        print(f"🚀 Выполняю подзадачу {subtask.id}:")
        print(f"   {subtask.description}")
        
        # Валидация
        validation = await validator.validate_action(subtask)
        
        if validation['requires_confirmation']:
            confirmed = await validator.request_user_confirmation(
                validation['confirmation_message']
            )
            if not confirmed:
                print("   ⏸️  Пропущено (пользователь отменил)")
                continue
        
        # Выполнение в зависимости от типа агента
        if subtask.agent_type.value == "navigator":
            result = await navigator.execute_subtask(subtask)
            agent_name = "navigator"
        elif subtask.agent_type.value == "interactor":
            result = await interactor.execute_subtask(subtask)
            agent_name = "interactor"
        else:
            print(f"   ⚠️  Агент {subtask.agent_type.value} пока не реализован")
            continue
        
        # Логирование
        context_mgr.log_action(agent_name, f"subtask_{subtask.id}", 
                             f"Success: {result.get('success', False)}")
        
        # Верификация результата
        verification = await validator.verify_result(subtask, result)
        
        if verification['success']:
            print(f"   ✅ Успешно выполнено")
            results.append({
                'subtask_id': subtask.id,
                'success': True,
                'result': result.get('details', {})
            })
        else:
            print(f"   ❌ Ошибка: {verification.get('issues', ['Unknown'])}")
            if verification.get('suggestions'):
                print(f"   💡 Предложения: {verification['suggestions']}")
            results.append({
                'subtask_id': subtask.id,
                'success': False,
                'error': verification.get('issues', ['Unknown'])
            })
        
        # Пауза между задачами
        await asyncio.sleep(1)
    
    # Генерация отчета
    print(f"\n{'='*60}")
    print("📈 ФИНАЛЬНЫЙ ОТЧЕТ:")
    
    successful = sum(1 for r in results if r['success'])
    print(f"   Успешно выполнено: {successful} из {len(results)} подзадач")
    
    # Извлечение найденных данных
    found_data = []
    for result in results:
        if result['success'] and 'result' in result:
            details = result['result']
            if 'text_extracted' in str(details):
                found_data.append(details)
    
    if found_data:
        print(f"\n📁 Найденные данные сохранены в:")
        for data in found_data:
            if 'file_saved' in data:
                print(f"   - {data['file_saved']}")
    
    print(f"\n🎉 Демонстрационный сценарий завершен!")
    print("   Для реального поиска вакансий требуется доработка:")
    print("   1. Добавление логики анализа HTML структуры hh.ru")
    print("   2. Реализация фильтрации вакансий")
    print("   3. Добавление функционала отправки откликов")
    
    # Закрываем браузер
    await browser_controller.close()
    return results

if __name__ == "__main__":
    print("🤖 АВТОНОМНЫЙ AI-АГЕНТ: Демо сценарий hh.ru")
    print("=" * 60)
    
    try:
        results = asyncio.run(run_hh_vacancy_scenario())
        print(f"\n✅ Сценарий выполнен. Результатов: {len(results)}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Сценарий прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка выполнения сценария: {e}")
        import traceback
        traceback.print_exc()