import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database import Database
from menu import create_menu_system
from services import create_service_registry
from middlewares import DependencyMiddleware
import handlers

# Инициализируем конфигурацию и логирование
config = Config()
config.setup_logging()

logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""

    logger.info("🚀 Запуск Telegram Price Bot...")

    try:
        # Валидация конфигурации
        logger.info("⚙️ Проверка конфигурации...")
        errors = config.validate_config()
        if errors:
            logger.error("❌ Ошибки конфигурации:")
            for error in errors:
                logger.error(f"  {error}")
            sys.exit(1)

        logger.info("✅ Конфигурация корректна")
        logger.info(f"👥 Администраторы: {config.admin_ids}")
        logger.info(f"💾 База данных: {config.get_database_info()['type']}")
        logger.info(f"🔧 Режим отладки: {config.debug}")

        # Инициализация базы данных
        logger.info("📊 Инициализация базы данных...")
        database = Database(config.database_url)
        await database.init()
        logger.info("✅ База данных готова")

        # Инициализация системы меню
        logger.info("📋 Настройка системы меню...")
        menu_manager, menu_registry = create_menu_system(config.admin_ids)
        logger.info("✅ Система меню готова")

        # Инициализация бота
        logger.info("🤖 Запуск бота...")
        bot = Bot(token=config.bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # Настройка middleware
        dependency_middleware = DependencyMiddleware(
            database, menu_registry, config, service_registry
        )

        # Регистрируем middleware для внедрения зависимостей
        dp.message.middleware.register(dependency_middleware)
        dp.callback_query.middleware.register(dependency_middleware)

        # Регистрация обработчиков
        handlers_router = handlers.create_handlers_router(
            config, database, menu_manager
        )
        dp.include_router(handlers_router)

        # Проверка подключения к Telegram
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот @{bot_info.username} готов к работе!")
        logger.info(f"📊 Информация: ID {bot_info.id}, Name: {bot_info.first_name}")

        # Инициализация для разработчиков
        if config.environment == "development":
            for user_id in config.admin_ids:
                try:
                    await bot_service.send_startup_notification(user_id, bot)

                    success = await menu_manager.show_menu(
                        menu_id="main", bot=bot, chat_id=user_id
                    )

                    if success:
                        logger.info(
                            f"✅ Главное меню отправлено администратору {user_id}"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Не удалось отправить меню администратору {user_id}"
                        )

                except Exception as e:
                    logger.warning(
                        f"❌ Ошибка отправки приветствия администратору {user_id}: {e}"
                    )

        # Запуск polling
        logger.info("🎯 Начало обработки сообщений...")
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
            skip_updates=True,
            drop_pending_updates=True,
        )

    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        raise
    finally:
        logger.info("🛑 Завершение работы...")
        if "database" in locals():
            await database.close()
            logger.info("💾 База данных закрыта")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚡ Получен сигнал завершения (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка: {e}", exc_info=True)
        sys.exit(1)
