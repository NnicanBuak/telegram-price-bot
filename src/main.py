import asyncio
import logging
import sys
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database import Database
from menu import create_menu_system
import handlers

# Инициализируем конфигурацию и логирование
config = Config()
config.setup_logging()

logger = logging.getLogger(__name__)


class DependencyMiddleware:
    """Middleware для внедрения зависимостей"""

    def __init__(self, database: Database, menu_registry, config: Config):
        self.database = database
        self.menu_registry = menu_registry
        self.config = config

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
                # Добавляем сервисы для удобства
                **self.menu_registry.get_all_services(),
            }
        )
        return await handler(event, data)


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
        dependency_middleware = DependencyMiddleware(database, menu_registry, config)

        # Регистрируем middleware для внедрения зависимостей
        dp.message.middleware.register(dependency_middleware)
        dp.callback_query.middleware.register(dependency_middleware)

        # Регистрация обработчиков
        registry = handlers.HandlerRegistry()

        registry.register_module(
            handlers.commands.CommandsModule("commands", config, database, menu_manager)
        )

        registry.setup_dispatcher(dp)

        stats = registry.get_statistics()
        logger.info(f"✅ Зарегистрировано модулей: {stats['total_modules']}")
        logger.info(f"📋 Модули: {', '.join(stats['module_names'])}")
        logger.info(f"🧠 Обработчики: {stats['total_handlers']}")

        # Проверка подключения к Telegram
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот @{bot_info.username} готов к работе!")
        logger.info(f"📊 Информация: ID {bot_info.id}, Name: {bot_info.first_name}")

        # Отправка сообщения при разработке
        if config.environment == "development":
            for user_id in config.admin_ids:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text="""Бот начал свою работу.
Автовызов /start...""",
                    )
                    await registry.call_handler(
                        "commands.start", chat_id=user_id, bot=bot
                    )
                    logger.info(f"☑️ Бот начал свою работу для {user_id}")
                except Exception as e:
                    logger.warning(
                        f"""❌ Бот не смог начать свою работу для {user_id} по причние:
                        {e}"""
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
