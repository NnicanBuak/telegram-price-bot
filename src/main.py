#!/usr/bin/env python3
"""
Telegram бот для рассылки прайс-листов по группам
Исправленная версия с новым aiogram API и полным функционалом
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database import Database
from menu_system import MenuManager, MenuMiddleware
from bot.menus import setup_bot_menus
from bot.handlers.menu_handlers import menu_router
from bot.handlers.mailing_handlers import mailing_router
from bot.handlers.template_handlers import template_router
from bot.handlers.group_handlers import group_router

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

    logger.info("🚀 Запуск Telegram Price Bot...")

    # Инициализация конфигурации
    logger.info("⚙️ Инициализация конфигурации...")
    try:
        config = Config()
        logger.info(f"✅ Конфигурация загружена (режим: {config.environment})")
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
        return

    # Создание бота с новым API
    logger.info("🤖 Создание бота...")
    try:
        bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                protect_content=False,
                allow_sending_without_reply=True,
            ),
        )

        # Проверяем подключение
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот подключен: @{bot_info.username} (ID: {bot_info.id})")

    except Exception as e:
        logger.error(f"❌ Ошибка создания бота: {e}")
        return

    # Создание диспетчера
    logger.info("📡 Создание диспетчера...")
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Инициализация базы данных
    logger.info("🗄️ Инициализация базы данных...")
    try:
        db = Database(config.database_url)
        await db.init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return

    # Настройка системы меню
    logger.info("📋 Настройка системы меню...")
    try:
        menu_manager = MenuManager(admin_ids=config.admin_ids)
        bot_menus = setup_bot_menus(menu_manager, db)
        logger.info("✅ Система меню настроена")
    except Exception as e:
        logger.error(f"❌ Ошибка настройки меню: {e}")
        return

    # Настройка middleware
    logger.info("🔧 Настройка middleware...")
    menu_middleware = MenuMiddleware(menu_manager, db)
    dp.message.middleware(menu_middleware)
    dp.callback_query.middleware(menu_middleware)

    # Регистрация роутеров
    logger.info("🔗 Регистрация обработчиков...")
    dp.include_router(menu_router)
    dp.include_router(template_router)
    dp.include_router(group_router)
    dp.include_router(mailing_router)

    # Отправка уведомлений админам о запуске
    if config.send_startup_notifications:
        logger.info("📨 Отправка уведомлений о запуске...")
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    "🚀 <b>Price Bot запущен!</b>\n\n"
                    f"🤖 Бот: @{bot_info.username}\n"
                    f"⚙️ Режим: {config.environment}\n"
                    f"📊 БД: {'SQLite' if 'sqlite' in config.database_url else 'PostgreSQL'}\n\n"
                    "✅ Все системы готовы к работе",
                )
            except Exception as e:
                logger.warning(
                    f"⚠️ Не удалось отправить уведомление админу {admin_id}: {e}"
                )

    # Запуск бота
    logger.info("🎯 Запуск polling...")
    try:
        await dp.start_polling(
            bot, allowed_updates=["message", "callback_query"], close_bot_session=True
        )
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка бота по Ctrl+C...")
    except Exception as e:
        logger.error(f"❌ Ошибка при работе бота: {e}")
    finally:
        logger.info("🔄 Завершение работы...")

        # Отправка уведомлений о остановке
        if config.send_startup_notifications:
            for admin_id in config.admin_ids:
                try:
                    await bot.send_message(
                        admin_id,
                        "⏹️ <b>Price Bot остановлен</b>\n\n" "🔧 Бот завершил работу",
                    )
                except:
                    pass  # Игнорируем ошибки при завершении

        await bot.session.close()
        logger.info("✅ Завершение работы завершено")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Остановка...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
