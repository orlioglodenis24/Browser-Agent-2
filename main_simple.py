# browser-agent/main_simple.py (рабочая упрощенная версия)
import asyncio
import sys
from agents.planner import MasterPlanner
from agents.navigator import NavigationAgent
from agents.interactor import InteractionAgent
from agents.context_manager import ContextManager
from browser.controller import BrowserController

async def main():
    print("🤖 УПРОЩЕННАЯ ВЕРСИЯ AI-АГЕНТА")
    print("=" * 60)
    
    # Инициализация
    context_mgr = ContextManager()
    browser_controller = BrowserController()
    
    # Получение задачи
    if len(sys.argv) > 1:
        user_task = " ".join(sys.argv[1:])
    else:
        user_task = input("\n🎯 Введите задачу: ").strip()
    
    if not user_task:
        return
    
    print(f"\n📋 Анализирую: '{user_task}'")
    
    # Планирование
    planner = MasterPlanner()
    plan = await planner.create_plan(user_task, context_mgr)
    
    print(f"\n📊 План из {len(plan.subtasks)} подзадач:")
    for st in plan.subtasks:
        print(f"   • {st.description}")
    
    # Создание агентов
    navigator = NavigationAgent(browser_controller)
    interactor = InteractionAgent(browser_controller)
    
    # Выполнение
    for subtask in plan.subtasks:
        print(f"\n{'='*50}")
        print(f"🚀 {subtask.id}. {subtask.description}")
        
        # Простая проверка безопасности
        if any(word in subtask.description.lower() for word in ['удалить', 'купить', 'парол']):
            resp = input(f"   ⚠️  Опасное действие. Продолжить? (y/n): ")
            if resp.lower() not in ['y', 'да']:
                print("   ⏸️  Пропущено")
                continue
        
        # Выполнение
        if subtask.agent_type.value == "navigator":
            result = await navigator.execute_subtask(subtask)
        elif subtask.agent_type.value == "interactor":
            result = await interactor.execute_subtask(subtask)
        else:
            continue
        
        # Логирование
        if result.get('success'):
            print(f"   ✅ Успешно")
        else:
            print(f"   ❌ Ошибка: {result.get('error', 'Неизвестно')}")
        
        await asyncio.sleep(1)
    
    print(f"\n{'='*60}")
    print("🎉 ЗАДАЧА ВЫПОЛНЕНА!")
    print(f"   Цель: {plan.main_goal}")
    
    input("\n👀 Нажмите Enter для завершения → ")
    await browser_controller.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Прервано")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
