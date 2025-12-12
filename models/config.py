# browser-agent/models/config.py

class AgentConfig:
    """Конфигурация системы"""
    
    # Настройки Ollama
    OLLAMA_CONFIG = {
        "base_url": "http://localhost:11434",
        "timeout": 45,  # Увеличили для сложных запросов
        "default_model": "llama3.2"
    }
    
    # Настройки браузера
    BROWSER_CONFIG = {
        "headless": False,
        "viewport": {"width": 1280, "height": 720},
        "slow_mo": 800,
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--start-maximized"
        ],
        "timeout": 15000  # 15 секунд на загрузку страницы
    }
    
    # Настройки навигации
    NAVIGATION_CONFIG = {
        "default_wait_time": 2,
        "max_retries": 3,
        "screenshots_enabled": True
    }