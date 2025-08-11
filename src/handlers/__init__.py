"""
Пакет обработчиков для Telegram бота
"""

from .base import (
    HandlerRegistry,
    create_handler_registry,
    setup_all_handlers,
    validate_handler_module,
    HandlerModule,
)
from . import commands
from . import menu_navigation
from . import templates
from . import groups
from . import mailing

# Список всех модулей с обработчиками
HANDLER_MODULES = [commands, menu_navigation, templates, groups, mailing]


# Удобные функции для быстрой настройки
def setup_basic_handlers(config, database, menu_manager, menu_registry, dispatcher):
    """Быстрая настройка всех основных обработчиков"""
    return setup_all_handlers(
        config, database, menu_manager, menu_registry, dispatcher, HANDLER_MODULES
    )


def validate_all_modules():
    """Проверить все модули на валидность"""
    results = {}
    for module in HANDLER_MODULES:
        module_name = module.__name__.split(".")[-1]  # Получаем короткое имя
        results[module_name] = validate_handler_module(module)
    return results


def get_module_by_name(name: str):
    """Получить модуль по имени"""
    module_map = {
        "commands": commands,
        "menu_navigation": menu_navigation,
        "templates": templates,
        "groups": groups,
        "mailing": mailing,
    }
    return module_map.get(name)


# Экспортируем все необходимое для удобного использования
__all__ = [
    # Основные классы и функции
    "HandlerRegistry",
    "HandlerModule",
    "create_handler_registry",
    "setup_all_handlers",
    "validate_handler_module",
    # Удобные функции
    "setup_basic_handlers",
    "validate_all_modules",
    "get_module_by_name",
    # Список модулей
    "HANDLER_MODULES",
    # Отдельные модули (для прямого доступа если нужно)
    "commands",
    "menu_navigation",
    "templates",
    "groups",
    "mailing",
]
