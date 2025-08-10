"""
Templates feature - управление шаблонами сообщений

Упрощенный API для работы с шаблонами в MVP версии.
"""

from .handlers import TemplateHandlers
from .services import TemplateService
from .models import TemplateData, ValidationError

__all__ = [
    "TemplateHandlers",
    "TemplateService",
    "TemplateData",
    "ValidationError",
    "create_template_feature",
]


def create_template_feature(database) -> tuple[TemplateHandlers, TemplateService]:
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
