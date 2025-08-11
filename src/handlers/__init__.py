"""
Пакет обработчиков для Telegram бота
"""

from .base import (
    HandlerRegistry,
    HandlerModule,
)
from . import commands
from . import menu_navigation
from . import templates
from . import groups
from . import mailing

# Список всех модулей с обработчиками
HANDLER_MODULES = [commands, menu_navigation, templates, groups, mailing]

# Экспортируем все необходимое для удобного использования
__all__ = [
    # Основные классы и функции
    "HandlerRegistry",
    "HandlerModule",
    "HANDLER_MODULES",
    "commands",
    "menu_navigation",
    "templates",
    "groups",
    "mailing",
]
