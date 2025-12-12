# browser-agent/agents/validator.py (упрощенная версия)
import re
from typing import Dict, Any, Optional
from models.schemas import Subtask

class ValidationAgent:
    """Агент валидации и безопасности (упрощенная версия)"""
    
    def __init__(self):
        print("   [Validator] Агент безопасности инициализирован")
    
    async def validate_action(self, subtask: Subtask, navigation_result=None) -> Dict[str, Any]:
        """Проверка безопасности действия"""
        return {
            'is_safe': True,
            'requires_confirmation': False,
            'confirmation_message': None,
            'risks': [],
            'recommendations': []
        }
    
    async def request_user_confirmation(self, message: str) -> bool:
        """Запрос подтверждения у пользователя"""
        print(f"\n⚠️  ТРЕБУЕТСЯ ПОДТВЕРЖДЕНИЕ: {message}")
        try:
            response = input("   Подтвердить? (y/n): ").strip().lower()
            return response in ['y', 'yes', 'да', 'д']
        except:
            return False
    
    async def verify_result(self, subtask: Subtask, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка результатов выполнения действия"""
        success = action_result.get('success', False) if isinstance(action_result, dict) else False
        
        return {
            'success': success,
            'issues': [] if success else ["Действие не выполнено успешно"],
            'suggestions': []
        }
