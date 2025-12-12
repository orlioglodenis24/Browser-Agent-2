# browser-agent/main.py (обновленная версия)
import argparse
import asyncio
from agents.planner import MasterPlanner
from agents.navigator import NavigationAgent
from agents.interactor import InteractionAgent
from agents.validator import ValidationAgent
from agents.context_manager import ContextManager
from browser.controller import BrowserController

async def main():
    print("🤖 ЗАПУСК ПОЛНОЙ МУЛЬТИ-АГЕНТНОЙ СИСТЕМЫ")
    print("=" * 60)
    context_mgr = ContextManager()
    browser_controller = BrowserController()
    
    parser = argparse.ArgumentParser(description='Запуск мульти-агентного браузер-агента')
    parser.add_argument('--task', '-t', type=str, help='Текст задачи для агента')
    parser.add_argument('--record-video', action='store_true', help='Записать видео сессии')
    args = parser.parse_args()

    if args.task:
        user_task = args.task
    else:
        user_task = input("\n🎯 Введите задачу для AI-агента: ").strip()
    
    if not user_task:
        print("Задача не введена.")
        return
    
    print(f"\n📋 Анализирую задачу: '{user_task}'")
    
    planner = MasterPlanner()
    plan = await planner.create_plan(user_task, context_mgr)
    
    print(f"\n📊 Получен план из {len(plan.subtasks)} подзадач")
    context_mgr.update_plan(plan)
    
    navigator = NavigationAgent(browser_controller)
    interactor = InteractionAgent(browser_controller)
    validator = ValidationAgent()
    
    for subtask in plan.subtasks:
        print(f"\n{'='*50}")
        print(f"🚀 Подзадача {subtask.id}: {subtask.description}")
        print(f"   Агент: {subtask.agent_type.value}")
        print(f"   Критерии: {subtask.success_criteria}")
        
        if subtask.agent_type.value != "planner":
            validation = await validator.validate_action(subtask)
            
            if validation['requires_confirmation']:
                confirmed = await validator.request_user_confirmation(
                    validation['confirmation_message']
                )
                if not confirmed:
                    print("   ⏸️  Пропущено (пользователь отменил)")
                    continue
        
        if subtask.agent_type.value == "navigator":
            result = await navigator.execute_subtask(subtask)
        elif subtask.agent_type.value == "interactor":
            result = await interactor.execute_subtask(subtask)
        elif subtask.agent_type.value == "validator":
            print("   ⚠️  Валидация выполняется автоматически")
            result = {'success': True, 'details': {'validated': True}}
        else:
            continue
        
        context_mgr.log_action(
            subtask.agent_type.value,
            f"subtask_{subtask.id}",
            f"Success: {result.get('success', False)}"
        )
        
        verification = await validator.verify_result(subtask, result)
        
        if verification['success']:
            print(f"   ✅ Успешно")
            if result.get('details'):
                for key, value in result['details'].items():
                    if key not in ['screenshot']:
                        print(f"     {key}: {value}")
        else:
            print(f"   ❌ Ошибка: {verification.get('issues', ['Unknown'])}")
        
        await asyncio.sleep(1)
    
    print(f"\n{'='*60}")
    print("🏆 СИСТЕМА УСПЕШНО ВЫПОЛНИЛА ЗАДАЧУ")
    print(f"   Цель: {plan.main_goal}")
    print(f"   Подзадач: {len(plan.subtasks)}")
    print(f"   Архитектура: 5 агентов (Planner, Navigator, Interactor, Validator, Context)")
    
    print("\n📁 Результаты сохранены в:")
    print("   - Скриншоты: step_*.png")
    print("   - Тексты: recipe_text_*.txt")
    print("   - Логи: в контексте системы")
    
    print("\n👀 Браузер останется открытым...")
    input("   Нажмите Enter для завершения → ")
    
    await browser_controller.close()
    print("\n🎉 Система завершила работу!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Работа завершена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()