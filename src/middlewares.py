from typing import Any, Awaitable, Callable, Dict
from aiogram import types

from config import Config
from database import Database


class DependencyMiddleware:
    """Middleware для внедрения зависимостей"""

    def __init__(
        self, database: Database, menu_registry, config: Config, service_registry
    ):
        self.database = database
        self.menu_registry = menu_registry
        self.config = config
        self.service_registry = service_registry

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Внедрение зависимостей в обработчики"""
        data.update(
            {
                "database": self.database,
                "menu_registry": self.menu_registry,
                "config": self.config,
                "service_registry": self.service_registry,
                **self.service_registry.get_all_services(),
            }
        )
        return await handler(event, data)
