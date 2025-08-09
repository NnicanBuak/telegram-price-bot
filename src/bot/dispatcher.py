"""
Создание и настройка диспетчера
"""

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import Config
from database.session import Database
from menu.middleware import MenuMiddleware
from menu.manager import MenuManager
from bot.middlewares.auth import AuthMiddleware
from bot.handlers import setup_handlers


def create_dispatcher(config: Config, database: Database) -> Dispatcher:
    """
    Создание и настройка диспетчера

    Args:
        config: Конфигурация приложения
        database: Экземпляр базы данных

    Returns:
        Dispatcher: Настроенный диспетчер
    """
    # Создаем диспетчер с хранилищем в памяти
    dp = Dispatcher(storage=MemoryStorage())

    # Создаем менеджер меню
    menu_manager = MenuManager(admin_ids=config.bot.admin_ids)

    # Регистрируем middleware
    dp.message.middleware(AuthMiddleware(config.bot.admin_ids))
    dp.callback_query.middleware(AuthMiddleware(config.bot.admin_ids))
    dp.message.middleware(MenuMiddleware(menu_manager))
    dp.callback_query.middleware(MenuMiddleware(menu_manager))

    # Добавляем объекты в контекст
    dp["config"] = config
    dp["database"] = database
    dp["menu_manager"] = menu_manager

    # Регистрируем обработчики
    setup_handlers(dp)

    return dp
