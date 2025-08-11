"""
Архитектура handlers без дублирования кода
Одна функция для событий Telegram И программного вызова
"""

from typing import Dict, List, Optional, Any, Union, Callable
from abc import ABC, abstractmethod
from aiogram import Router, types, Bot
from aiogram.filters import CommandStart, Command
import logging

from config import Config
from database import Database
from menu import MenuManager

logger = logging.getLogger(__name__)


class HandlerContext:
    """Контекст выполнения handler - универсальный для событий и программных вызовов"""

    def __init__(
        self,
        chat_id: int,
        user_id: int = None,
        bot: Bot = None,
        message: types.Message = None,
        callback: types.CallbackQuery = None,
        **extra_data,
    ):
        self.chat_id = chat_id
        self.user_id = user_id  # Для групп user_id может быть None
        self.bot = bot
        self.message = message
        self.callback = callback
        self.extra_data = extra_data

        # Для программных вызовов
        self.is_programmatic = message is None and callback is None

    async def send_message(self, text: str, **kwargs):
        """Универсальная отправка сообщения"""
        if self.message:
            return await self.message.answer(text, **kwargs)
        elif self.callback:
            return await self.callback.message.answer(text, **kwargs)
        elif self.bot:
            return await self.bot.send_message(self.chat_id, text, **kwargs)
        else:
            raise ValueError("Нет способа отправить сообщение")

    async def send_photo(self, photo, caption=None, **kwargs):
        """Универсальная отправка фото"""
        if self.message:
            return await self.message.answer_photo(photo, caption=caption, **kwargs)
        elif self.callback:
            return await self.callback.message.answer_photo(
                photo, caption=caption, **kwargs
            )
        elif self.bot:
            return await self.bot.send_photo(
                self.chat_id, photo, caption=caption, **kwargs
            )
        else:
            raise ValueError("Нет способа отправить фото")

    async def edit_message(self, text: str, **kwargs):
        """Редактирование сообщения (только для callback)"""
        if self.callback:
            await self.callback.message.edit_text(text, **kwargs)
            await self.callback.answer()
        else:
            # Для программных вызовов просто отправляем новое
            await self.send_message(text, **kwargs)

    @classmethod
    def from_message(cls, message: types.Message, bot: Bot = None) -> "HandlerContext":
        """Создать контекст из Message"""
        return cls(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            bot=bot,
            message=message,
        )

    @classmethod
    def from_callback(
        cls, callback: types.CallbackQuery, bot: Bot = None
    ) -> "HandlerContext":
        """Создать контекст из CallbackQuery"""
        return cls(
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id,
            bot=bot,
            callback=callback,
        )

    @classmethod
    def for_chat(cls, chat_id: int, bot: Bot, **extra_data) -> "HandlerContext":
        """Создать контекст для программного вызова"""
        return cls(chat_id=chat_id, user_id=chat_id, bot=bot, **extra_data)  # Для групп


class BaseHandler(ABC):
    """Базовый класс для handlers"""

    def __init__(self, config: Config, database: Database, menu_manager: MenuManager):
        self.config = config
        self.database = database
        self.menu_manager = menu_manager
        self.name = self.__class__.__name__

    @abstractmethod
    async def execute(self, ctx: HandlerContext) -> Any:
        """
        ЕДИНСТВЕННАЯ функция handler!
        Работает и для событий Telegram, и для программных вызовов
        """
        pass

    def get_filters(self) -> List[Any]:
        """Фильтры для регистрации в роутере"""
        return []

    def can_be_called_programmatically(self) -> bool:
        """Можно ли вызывать программно"""
        return True


class HandlerModule:
    """Модуль с коллекцией handlers"""

    def __init__(
        self, name: str, config: Config, database: Database, menu_manager: MenuManager
    ):
        self.name = name
        self.config = config
        self.database = database
        self.menu_manager = menu_manager
        self.handlers: Dict[str, BaseHandler] = {}
        self._setup_handlers()

    def _setup_handlers(self):
        """Переопределяется в наследниках"""
        pass

    def register_handler(self, name: str, handler: BaseHandler):
        """Зарегистрировать handler"""
        self.handlers[name] = handler

    def get_handler(self, name: str) -> Optional[BaseHandler]:
        """Получить handler"""
        return self.handlers.get(name)

    def get_router(self) -> Router:
        """Создать роутер"""
        router = Router()

        for handler in self.handlers.values():
            filters = handler.get_filters()

            for filter_obj in filters:
                if isinstance(filter_obj, CommandStart):

                    @router.message(filter_obj)
                    async def cmd_handler(message: types.Message, bot: Bot):
                        ctx = HandlerContext.from_message(message, bot)
                        await handler.execute(ctx)

                elif isinstance(filter_obj, Command):

                    @router.message(filter_obj)
                    async def msg_handler(message: types.Message, bot: Bot):
                        ctx = HandlerContext.from_message(message, bot)
                        await handler.execute(ctx)

        return router


class HandlerRegistry:
    """Реестр handlers"""

    def __init__(self):
        self._handler_modules: Dict[str, HandlerModule] = {}
        self.handlers: Dict[str, BaseHandler] = {}

    def register_module(self, module: HandlerModule):
        """Зарегистрировать модуль"""
        self._handler_modules[module.name] = module

        # Добавляем handlers в общий реестр
        for handler_name, handler in module.handlers.items():
            full_name = f"{module.name}.{handler_name}"
            self.handlers[full_name] = handler

    async def call_handler(
        self, handler_name: str, chat_id: int, bot: Bot, **extra_data
    ) -> Any:
        handler = self.handlers.get(handler_name)
        if not handler:
            raise ValueError(f"Handler {handler_name} не найден")

        ctx = HandlerContext.for_chat(chat_id, bot, **extra_data)
        return await handler.execute(ctx)

    def setup_dispatcher(self, dispatcher):
        """Настроить диспетчер"""
        for module in self._handler_modules.values():
            router = module.get_router()
            dispatcher.include_router(router)

    def get_handler(self, name: str) -> Optional[BaseHandler]:
        return self.handlers.get(name)

    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику зарегистрированных модулей и хэндлеров"""
        return {
            "total_modules": len(self._handler_modules),
            "total_handlers": len(self.handlers),
            "module_names": list(self._handler_modules.keys()),
            "modules": {
                module_name: list(module.handlers.keys())
                for module_name, module in self._handler_modules.items()
            },
        }

    def validate_modules(self) -> None:
        """
        Проверить корректность зарегистрированных модулей:
        - уникальные имена хэндлеров
        - наличие хотя бы одного хэндлера в модуле
        - метод execute переопределён
        """
        seen_names = set()

        for module_name, module in self._handler_modules.items():
            if not module.handlers:
                raise ValueError(f"Модуль {module_name} не содержит хэндлеров")

            for handler_name, handler in module.handlers.items():
                full_name = f"{module_name}.{handler_name}"
                if full_name in seen_names:
                    raise ValueError(f"Дубликат имени хэндлера: {full_name}")
                seen_names.add(full_name)

                # Проверка, что execute переопределён
                if handler.__class__.execute is BaseHandler.execute:
                    raise TypeError(
                        f"Хэндлер {full_name} не переопределяет метод execute()"
                    )

        logger.info("Валидация модулей пройдена успешно")
