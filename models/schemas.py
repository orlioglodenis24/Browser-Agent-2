# browser-agent/models/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union, Dict, Any
from enum import Enum

class AgentType(str, Enum):
    PLANNER = "planner"
    NAVIGATOR = "navigator"
    INTERACTOR = "interactor"
    VALIDATOR = "validator"

class Subtask(BaseModel):
    id: int = Field(..., description="Уникальный ID подзадачи")
    description: str = Field(..., description="Чёткое описание подзадачи")
    agent_type: AgentType = Field(..., description="Какой агент должен выполнять")
    success_criteria: str = Field(..., description="Критерии успешного выполнения")
    potential_risks: List[str] = Field(default_factory=list, description="Возможные проблемы")
    
    @field_validator('agent_type', mode='before')
    @classmethod
    def validate_agent_type(cls, v):
        """Конвертируем строку в AgentType enum"""
        if isinstance(v, str):
            v = v.lower()
            if v == "navigator":
                return AgentType.NAVIGATOR
            elif v == "interactor":
                return AgentType.INTERACTOR
            elif v == "validator":
                return AgentType.VALIDATOR
        return v
    
    @field_validator('potential_risks', mode='before')
    @classmethod  
    def validate_risks(cls, v):
        """Обеспечиваем, что риски это список строк"""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            # Конвертируем все элементы в строки
            return [str(item) for item in v]
        return [str(v)]

class TaskPlan(BaseModel):
    main_goal: str = Field(..., description="Краткая формулировка цели")
    assumptions: List[str] = Field(default_factory=list, description="Предположения")
    subtasks: List[Subtask] = Field(..., description="Список подзадач")
    dependencies: str = Field("", description="Зависимости между подзадачами")
    
    @field_validator('assumptions', mode='before')
    @classmethod
    def validate_assumptions(cls, v):
        """Обеспечиваем, что предположения это список строк"""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return [str(item) for item in v]
        return [str(v)]
    
    @field_validator('dependencies', mode='before')
    @classmethod
    def validate_dependencies(cls, v):
        """Конвертируем зависимости в строку"""
        if v is None:
            return ""
        if isinstance(v, list):
            return "; ".join(str(item) for item in v)
        return str(v)

# Дополнительные схемы для взаимодействия агентов
class NavigationResult(BaseModel):
    """Результат навигации"""
    target_found: bool = Field(False, description="Найдена ли цель")
    target_description: str = Field("", description="Описание найденного элемента")
    coordinates: Dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0})
    element_info: Dict[str, Any] = Field(default_factory=dict)
    suggested_action: str = Field("", description="Предлагаемое действие")
    confidence_score: float = Field(0.0, ge=0, le=1, description="Уверенность")

class ActionResult(BaseModel):
    """Результат выполнения действия"""
    success: bool = Field(False, description="Успешно ли выполнено")
    action_type: str = Field("", description="Тип выполненного действия")
    result_summary: str = Field("", description="Описание результата")
    details: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    duration: float = Field(0.0, description="Время выполнения в секундах")
