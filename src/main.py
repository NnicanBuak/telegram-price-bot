#!/usr/bin/env python3
"""
Telegram бот для рассылки прайс-листов по группам
Финальная версия с правильной архитектурой
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database import Database
from menu_system import MenuManager, MenuMiddleware
from bot.menus import setup_bot_menus
from bot.handlers.menu_handlers import register_menu_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Глобальные переменные для использования в обработчиках
db = None
menu_manager = None
bot_menus = None


async def main():
    """Основная функция запуска бота"""
    global db, menu_manager, bot_menus

    logger.info("Инициализация конфигурации...")
    config = Config()

    logger.info("Создание бота...")
    bot = Bot(token=config.bot_token)

    logger.info("Создание диспетчера...")
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    logger.info("Инициализация базы данных...")
    db = Database(config.database_url)
    await db.init_db()

    logger.info("Настройка системы меню...")
    menu_manager = MenuManager(admin_ids=config.admin_ids)
    bot_menus = setup_bot_menus(menu_manager)

    logger.info("Настройка middleware...")
    menu_middleware = MenuMiddleware(menu_manager)
    dp.message.middleware(menu_middleware)
    dp.callback_query.middleware(menu_middleware)

    logger.info("Регистрация обработчиков...")
    register_menu_handlers(dp, menu_manager, db, bot_menus)

    logger.info("Запуск бота...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Остановка бота по Ctrl+C...")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        logger.info("Завершение работы...")
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
