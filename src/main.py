import asyncio
import logging
import sys
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from database import Database
from features import setup_features
from shared.menu_system import MenuMiddleware


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CoreHandlers:
    """Основные обработчики приложения"""

    def __init__(self, config: Config, menu_manager):
        self.config = config
        self.menu_manager = menu_manager
        self.router = Router()
        self._setup_handlers()

    def _setup_handlers(self):
        """Настройка основных обработчиков"""
        self.router.message(CommandStart())(self.cmd_start)
        self.router.message(Command("help"))(self.cmd_help)
        self.router.message(Command("id"))(self.cmd_id)

        # Обработчики меню
        self.router.callback_query(F.data == "menu_main")(self.show_main_menu)
        self.router.callback_query(F.data == "menu_templates")(self.show_templates_menu)
        self.router.callback_query(F.data == "menu_groups")(self.show_groups_menu)
        self.router.callback_query(F.data == "menu_mailing")(self.show_mailing_menu)

    async def cmd_start(self, message: types.Message):
        """Команда /start"""
        user_id = message.from_user.id

        if not self.config.is_admin(user_id):
            await message.answer(
                "❌ <b>Доступ запрещен</b>\n\n"
                "Этот бот доступен только администраторам.",
                parse_mode="HTML",
            )
            return

        # Показываем главное меню
        text, keyboard = self.menu_manager.render_menu("main", user_id)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    async def cmd_help(self, message: types.Message):
        """Команда /help"""
        await message.answer(
            "📋 <b>Справка по боту</b>\n\n"
            "🔹 <b>Шаблоны</b> - создание сообщений с файлами\n"
            "🔹 <b>Группы</b> - объединение чатов для рассылки\n"
            "🔹 <b>Рассылка</b> - отправка по выбранным группам\n"
            "🔹 <b>История</b> - статистика отправок\n\n"
            "<b>Команды:</b>\n"
            "/start - главное меню\n"
            "/help - справка\n"
            "/id - получить ID чата",
            parse_mode="HTML",
        )

    async def cmd_id(self, message: types.Message):
        """Команда /id"""
        info = (
            f"💬 <b>Информация о чате</b>\n\n"
            f"ID чата: <code>{message.chat.id}</code>\n"
            f"Тип чата: {message.chat.type}\n"
            f"ID пользователя: <code>{message.from_user.id}</code>\n"
        )

        if message.chat.title:
            info += f"Название: {message.chat.title}\n"
        if message.from_user.username:
            info += f"Username: @{message.from_user.username}\n"

        info += "\n💡 <i>Используйте ID чата для добавления в группы</i>"

        await message.answer(info, parse_mode="HTML")

    async def show_main_menu(self, callback: types.CallbackQuery):
        """Показать главное меню"""
        await self.menu_manager.navigate_to("main", callback)

    async def show_templates_menu(self, callback: types.CallbackQuery):
        """Показать меню шаблонов"""
        await self.menu_manager.navigate_to("templates", callback)

    async def show_groups_menu(self, callback: types.CallbackQuery):
        """Показать меню групп"""
        await self.menu_manager.navigate_to("groups", callback)

    async def show_mailing_menu(self, callback: types.CallbackQuery):
        """Показать меню рассылки"""
        await self.menu_manager.navigate_to("mailing", callback)


class DependencyMiddleware:
    """Middleware для внедрения зависимостей"""

    def __init__(self, database: Database, feature_registry, menu_manager):
        self.database = database
        self.feature_registry = feature_registry
        self.menu_manager = menu_manager

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
                "feature_registry": self.feature_registry,
                "menu_manager": self.menu_manager,
                # Добавляем сервисы для удобства
                **self.feature_registry.get_all_services(),
            }
        )
        return await handler(event, data)


async def main():
    """Основная функция запуска бота"""

    logger.info("🚀 Запуск Telegram Price Bot...")

    try:
        # Инициализация конфигурации
        logger.info("⚙️ Загрузка конфигурации...")
        config = Config()
        logger.info(f"✅ Администраторы: {config.admin_ids}")

        # Инициализация базы данных
        logger.info("📊 Инициализация базы данных...")
        database = Database(config.database_url)
        await database.init()
        logger.info("✅ База данных готова")

        # Инициализация features
        logger.info("🔧 Настройка features...")
        feature_registry = setup_features(database)
        logger.info("✅ Features инициализированы")

        # Инициализация системы меню
        logger.info("📋 Настройка системы меню...")
        menu_manager = feature_registry.setup_menu_system(config.admin_ids)
        logger.info("✅ Система меню готова")

        # Инициализация бота
        logger.info("🤖 Запуск бота...")
        bot = Bot(token=config.bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # Настройка middleware
        menu_middleware = MenuMiddleware(menu_manager, config.admin_ids)
        dependency_middleware = DependencyMiddleware(
            database, feature_registry, menu_manager
        )

        # Регистрируем middleware для проверки доступа и меню
        dp.message.middleware.register(menu_middleware)
        dp.callback_query.middleware.register(menu_middleware)

        # Регистрируем middleware для внедрения зависимостей
        dp.message.middleware.register(dependency_middleware)
        dp.callback_query.middleware.register(dependency_middleware)

        # Регистрация основных обработчиков
        core_handlers = CoreHandlers(config, menu_manager)
        dp.include_router(core_handlers.router)

        # Регистрация роутеров features
        for router in feature_registry.get_routers():
            dp.include_router(router)

        logger.info("✅ Обработчики зарегистрированы")

        # Проверка подключения к Telegram
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот @{bot_info.username} готов к работе!")

        # Запуск polling
        logger.info("🎯 Начало обработки сообщений...")
        await dp.start_polling(
            bot, allowed_updates=["message", "callback_query"], skip_updates=True
        )

    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise
    finally:
        logger.info("🛑 Завершение работы...")
        if "database" in locals():
            await database.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚡ Получен сигнал завершения (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка: {e}")
        sys.exit(1)
