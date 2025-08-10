import asyncio
import logging
from pathlib import Path
import sys
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from database import Database
from features import setup_features


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def create_main_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура приложения"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📄 Шаблоны", callback_data="templates")],
            [InlineKeyboardButton(text="👥 Группы", callback_data="groups")],
            [InlineKeyboardButton(text="📮 Рассылка", callback_data="mailing")],
            [InlineKeyboardButton(text="📊 История", callback_data="history")],
        ]
    )


class CoreHandlers:
    """Основные обработчики приложения"""

    def __init__(self, config: Config):
        self.config = config
        self.router = Router()
        self._setup_handlers()

    def _setup_handlers(self):
        """Настройка основных обработчиков"""
        self.router.message(CommandStart())(self.cmd_start)
        self.router.message(Command("help"))(self.cmd_help)
        self.router.message(Command("id"))(self.cmd_id)
        self.router.callback_query(F.data == "main")(self.show_main)

        # Заглушки для нереализованных features
        self.router.callback_query(F.data == "groups")(self.groups_placeholder)
        self.router.callback_query(F.data == "mailing")(self.mailing_placeholder)
        self.router.callback_query(F.data == "history")(self.history_placeholder)

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

        await message.answer(
            "🤖 <b>Telegram Price Bot</b>\n\n"
            "Добро пожаловать! Выберите нужную функцию:",
            reply_markup=create_main_keyboard(),
            parse_mode="HTML",
        )

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

    async def show_main(self, callback: types.CallbackQuery):
        """Показать главное меню"""
        await callback.message.edit_text(
            "🏠 <b>Главное меню</b>\n\nВыберите нужную функцию:",
            reply_markup=create_main_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()

    # Заглушки для нереализованных features
    async def groups_placeholder(self, callback: types.CallbackQuery):
        await callback.message.edit_text(
            "👥 <b>Группы чатов</b>\n\n"
            "🚧 <i>В разработке...</i>\n\n"
            "Этот раздел будет доступен в следующей версии.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="main")]
                ]
            ),
            parse_mode="HTML",
        )
        await callback.answer()

    async def mailing_placeholder(self, callback: types.CallbackQuery):
        await callback.message.edit_text(
            "📮 <b>Рассылка</b>\n\n"
            "🚧 <i>В разработке...</i>\n\n"
            "Этот раздел будет доступен в следующей версии.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="main")]
                ]
            ),
            parse_mode="HTML",
        )
        await callback.answer()

    async def history_placeholder(self, callback: types.CallbackQuery):
        await callback.message.edit_text(
            "📊 <b>История рассылок</b>\n\n"
            "🚧 <i>В разработке...</i>\n\n"
            "Этот раздел будет доступен в следующей версии.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="main")]
                ]
            ),
            parse_mode="HTML",
        )
        await callback.answer()


class AdminMiddleware:
    """Middleware для проверки прав администратора"""

    def __init__(self, config: Config):
        self.config = config

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Проверка прав доступа"""
        # Проверяем только для личных сообщений
        if hasattr(event, "chat") and event.chat.type == "private":
            user_id = event.from_user.id
            if not self.config.is_admin(user_id):
                if isinstance(event, types.Message):
                    await event.answer(
                        "❌ <b>Доступ запрещен</b>\n\n"
                        "Этот бот доступен только администраторам.",
                        parse_mode="HTML",
                    )
                elif isinstance(event, types.CallbackQuery):
                    await event.answer("❌ Доступ запрещен", show_alert=True)
                return

        return await handler(event, data)


class DependencyMiddleware:
    """Middleware для внедрения зависимостей"""

    def __init__(self, database: Database, feature_registry):
        self.database = database
        self.feature_registry = feature_registry

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
                # Добавляем сервисы для удобства
                **self.feature_registry.get_all_services(),
            }
        )
        return await handler(event, data)


async def main():
    """Основная функция запуска бота"""
    sys.path.append(str(Path(__file__).resolve().parent.parent / "shared"))

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

        # Инициализация бота
        logger.info("🤖 Запуск бота...")
        bot = Bot(token=config.bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # Настройка middleware
        admin_middleware = AdminMiddleware(config)
        dependency_middleware = DependencyMiddleware(database, feature_registry)

        dp.message.middleware.register(admin_middleware)
        dp.callback_query.middleware.register(admin_middleware)
        dp.message.middleware.register(dependency_middleware)
        dp.callback_query.middleware.register(dependency_middleware)

        # Регистрация обработчиков
        core_handlers = CoreHandlers(config)
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
