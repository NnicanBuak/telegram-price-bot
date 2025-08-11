import logging
from typing import List, Type, Protocol, Dict, Any
from aiogram import Dispatcher, Router
from menu import MenuManager, MenuRegistry
from config import Config
from database import Database

logger = logging.getLogger(__name__)


class HandlerDependencies:
    """Контейнер зависимостей для обработчиков"""

    def __init__(
        self,
        config: Config,
        database: Database,
        menu_manager: MenuManager,
        menu_registry: MenuRegistry,
    ):
        self.config = config
        self.database = database
        self.menu_manager = menu_manager
        self.menu_registry = menu_registry


class HandlerModule(Protocol):
    """Протокол для модулей с обработчиками"""

    @staticmethod
    def get_router(dependencies: HandlerDependencies) -> Router:
        """Возвращает роутер с настроенными обработчиками"""
        ...

    @staticmethod
    def setup_menus(menu_manager: MenuManager) -> None:
        """Настраивает меню (опционально)"""
        ...


class HandlerRegistry:
    """Реестр для регистрации всех обработчиков"""

    def __init__(
        self,
        config: Config,
        database: Database,
        menu_manager: MenuManager,
        menu_registry: MenuRegistry,
    ):
        self.config = config
        self.database = database
        self.menu_manager = menu_manager
        self.menu_registry = menu_registry
        self._handler_modules: List[HandlerModule] = []
        self._registered_routers: List[Router] = []

    def register_module(self, handler_module: HandlerModule) -> "HandlerRegistry":
        """Зарегистрировать модуль с обработчиками"""
        self._handler_modules.append(handler_module)

        # Настраиваем меню если есть
        if hasattr(handler_module, "setup_menus"):
            try:
                handler_module.setup_menus(self.menu_manager)
                logger.info(f"✅ Меню для {handler_module.__name__} настроены")
            except Exception as e:
                logger.error(f"❌ Ошибка настройки меню {handler_module.__name__}: {e}")

        return self

    def register_modules(self, modules: List[HandlerModule]) -> "HandlerRegistry":
        """Зарегистрировать несколько модулей сразу"""
        for module in modules:
            self.register_module(module)
        return self

    def setup_dispatcher(self, dp: Dispatcher) -> None:
        """Настроить диспетчер со всеми зарегистрированными обработчиками"""
        for handler_module in self._handler_modules:
            try:
                router = handler_module.get_router(
                    self.config, self.database, self.menu_manager, self.menu_registry
                )
                dp.include_router(router)
                self._registered_routers.append(router)
                logger.info(f"✅ Роутер {handler_module.__name__} зарегистрирован")

            except Exception as e:
                logger.error(f"❌ Ошибка регистрации {handler_module.__name__}: {e}")
                raise

    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику зарегистрированных модулей"""
        return {
            "total_modules": len(self._handler_modules),
            "total_routers": len(self._registered_routers),
            "module_names": [module.__name__ for module in self._handler_modules],
            "menu_count": (
                len(self.menu_manager._menus)
                if hasattr(self.menu_manager, "_menus")
                else 0
            ),
        }

    def validate_modules(self) -> Dict[str, bool]:
        """Проверить валидность всех модулей"""
        results = {}
        for module in self._handler_modules:
            module_name = module.__name__
            try:
                # Проверяем наличие обязательной функции get_router
                if not hasattr(module, "get_router"):
                    results[module_name] = False
                    logger.error(f"❌ {module_name}: отсутствует get_router()")
                    continue

                # Пробуем создать роутер
                router = module.get_router(
                    self.config, self.database, self.menu_manager, self.menu_registry
                )

                if not isinstance(router, Router):
                    results[module_name] = False
                    logger.error(f"❌ {module_name}: get_router() вернул не Router")
                    continue

                results[module_name] = True
                logger.info(f"✅ {module_name}: валидация пройдена")

            except Exception as e:
                results[module_name] = False
                logger.error(f"❌ {module_name}: ошибка валидации - {e}")

        return results


def create_handler_registry(
    config: Config,
    database: Database,
    menu_manager: MenuManager,
    menu_registry: MenuRegistry,
) -> HandlerRegistry:
    """Фабричная функция для создания реестра обработчиков"""
    return HandlerRegistry(config, database, menu_manager, menu_registry)


def setup_all_handlers(
    config: Config,
    database: Database,
    menu_manager: MenuManager,
    menu_registry: MenuRegistry,
    dispatcher: Dispatcher,
    handler_modules: List[HandlerModule],
) -> HandlerRegistry:
    """Удобная функция для полной настройки всех обработчиков"""

    logger.info(f"🔧 Настройка {len(handler_modules)} модулей обработчиков...")

    # Создаем реестр
    registry = create_handler_registry(config, database, menu_manager, menu_registry)

    # Регистрируем все модули
    registry.register_modules(handler_modules)

    # Валидируем модули
    validation_results = registry.validate_modules()
    failed_modules = [
        name for name, success in validation_results.items() if not success
    ]

    if failed_modules:
        logger.error(f"❌ Модули с ошибками: {failed_modules}")
        raise RuntimeError(f"Не удалось настроить модули: {failed_modules}")

    # Настраиваем диспетчер
    registry.setup_dispatcher(dispatcher)

    # Выводим статистику
    stats = registry.get_statistics()
    logger.info(
        f"✅ Настройка завершена: {stats['total_modules']} модулей, {stats['menu_count']} меню"
    )

    return registry


def validate_handler_module(module: HandlerModule) -> bool:
    """Проверить один модуль на валидность"""
    try:
        # Проверяем наличие обязательных атрибутов
        if not hasattr(module, "get_router"):
            logger.error(f"❌ {module.__name__}: отсутствует get_router()")
            return False

        # Проверяем, что get_router - это функция
        if not callable(getattr(module, "get_router")):
            logger.error(f"❌ {module.__name__}: get_router не является функцией")
            return False

        # Проверяем setup_menus если есть
        if hasattr(module, "setup_menus") and not callable(
            getattr(module, "setup_menus")
        ):
            logger.error(f"❌ {module.__name__}: setup_menus не является функцией")
            return False

        logger.info(f"✅ {module.__name__}: структура модуля корректна")
        return True

    except Exception as e:
        logger.error(f"❌ {module.__name__}: ошибка валидации - {e}")
        return False
