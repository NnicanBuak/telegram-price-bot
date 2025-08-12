"""
Пакет обработчиков для Telegram бота
Простая архитектура с роутерами
"""

from . import commands
from . import menu_navigation
from . import templates
from . import groups
from . import mailing

# Список всех модулей с обработчиками
HANDLER_MODULES = [commands, menu_navigation, templates, groups, mailing]


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

            # Добавляем все сервисы как атрибуты для удобства
            services = service_registry.get_all_services()
            for service_name, service_instance in services.items():
                setattr(self, service_name, service_instance)

    deps = Dependencies()

    # Настраиваем основные меню
    menu_navigation.setup_menus(menu_manager)

    # Регистрируем роутеры всех модулей
    registered_count = 0
    for module in HANDLER_MODULES:
        if hasattr(module, "get_router"):
            try:
                router = module.get_router(deps)
                dispatcher.include_router(router)
                registered_count += 1
                print(f"✅ Зарегистрирован роутер модуля {module.__name__}")
            except Exception as e:
                print(f"❌ Ошибка регистрации роутера модуля {module.__name__}: {e}")

    print(f"🎯 Всего зарегистрировано роутеров: {registered_count}")
    return deps  # Возвращаем deps вместо registry


# Экспортируем все необходимое для удобного использования
__all__ = [
    "HANDLER_MODULES",
    "setup_dispatcher_with_handlers",
    "commands",
    "menu_navigation",
    "templates",
    "groups",
    "mailing",
]
