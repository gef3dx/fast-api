"""
Конфигурация pytest для тестирования FastAPI приложения
"""

import asyncio
import pytest


# Настройка event loop для async тестов
@pytest.fixture(scope="session")
def event_loop():
    """Создать event loop для всей сессии тестирования"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Маркеры для pytest
def pytest_configure(config):
    """Регистрация custom маркеров"""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
