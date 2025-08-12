from . import commands
from . import menu_navigation
from . import templates
from . import groups
from . import mailing

# Список всех модулей с обработчиками
HANDLER_MODULES = [commands, menu_navigation, templates, groups, mailing]


def create_handler_registry(
    config, database, menu_manager, menu_registry, service_registry
):
    """Создать и настроить реестр обработчиков"""
    registry = HandlerRegistry()

    # Регистрируем модуль команд
    registry.register_module(
        commands.CommandsModule("commands", config, database, menu_manager)
    )

    # Настраиваем основные меню
    menu_navigation.setup_menus(menu_manager)

    return registry


def setup_dispatcher_with_handlers(
    dispatcher, config, database, menu_manager, menu_registry, service_registry
):
    """Настроить диспетчер со всеми обработчиками"""

    # Создаем объект deps для передачи в роутеры
    class Dependencies:
        def __init__(self):
            self.config = config
            self.database = database
            self.menu_manager = menu_manager
            self.menu_registry = menu_registry
            self.service_registry = service_registry

    deps = Dependencies()

    # Настраиваем основные меню
    menu_navigation.setup_menus(menu_manager)

    # Регистрируем роутеры
    for module in HANDLER_MODULES:
        if hasattr(module, "get_router"):
            try:
                router = module.get_router(deps)
                dispatcher.include_router(router)
            except Exception as e:
                print(f"Ошибка регистрации роутера модуля {module.__name__}: {e}")

    # Создаем реестр обработчиков для команд
    registry = create_handler_registry(
        config, database, menu_manager, menu_registry, service_registry
    )
    registry.setup_dispatcher(dispatcher)

    return registry


# Экспортируем все необходимое для удобного использования
__all__ = [
    # Основные классы и функции
    "HandlerRegistry",
    "HandlerModule",
    "HANDLER_MODULES",
    "create_handler_registry",
    "setup_dispatcher_with_handlers",
    "commands",
    "menu_navigation",
    "templates",
    "groups",
    "mailing",
]
