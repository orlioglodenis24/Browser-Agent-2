# browser-agent/agents/context_manager.py
from models.schemas import TaskPlan

class ContextManager:
    """Менеджер контекста (базовая версия)."""
    
    def __init__(self):
        self.session_id = "session_001"
        self.task_goal = ""
        self.action_history = []
        self.current_plan = None
        print("   [Context Manager] Инициализирован.")
    
    def update_plan(self, plan: TaskPlan):
        """Сохраняет текущий план в контекст."""
        self.current_plan = plan
        self.task_goal = plan.main_goal
        self.log_action("planner", "plan_created", f"Создан план для: {plan.main_goal}")
    
    def log_action(self, agent: str, action: str, result: str):
        """Логирует выполнение действия агентом."""
        import datetime
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "result": result
        }
        self.action_history.append(entry)
        # Пока просто выводим в консоль. На шаге 4 подключим нормальное логирование.
        print(f"   [Context] Записано действие: {agent} -> {action}")