"""
Templates feature - управление шаблонами сообщений

Публичный API для работы с шаблонами.
Экспортирует только необходимые компоненты для использования в других частях приложения.
"""

from .handlers import TemplateHandlers
from .services import TemplateService
from .models import (
    CreateTemplateData,
    UpdateTemplateData,
    TemplateResponse,
    TemplateValidationError,
)

# Экспортируем только публичный API
__all__ = [
    # Основные компоненты
    "TemplateHandlers",
    "TemplateService",
    # DTOs
    "CreateTemplateData",
    "UpdateTemplateData",
    "TemplateResponse",
    # Исключения
    "TemplateValidationError",
    # Функции инициализации
    "create_template_feature",
]


def add_template_feature(database) -> tuple[TemplateHandlers, TemplateService]:
    """
    Фабрика для создания feature шаблонов

    Args:
        database: Экземпляр базы данных

    Returns:
        tuple: (handlers, service) - готовые к использованию компоненты
    """
    service = TemplateService(database)
    handlers = TemplateHandlers(service)

    return handlers, service


# Метаданные feature
FEATURE_NAME = "templates"
FEATURE_VERSION = "1.0.0"
FEATURE_DESCRIPTION = "Управление шаблонами сообщений для рассылки"
