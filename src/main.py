import asyncio
import logging
import sys
import os
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

# Добавляем src в Python path для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Импорты основных компонентов
from config import Config
from database import Database
from shared.menu_system import MenuManager, MenuMiddleware

from features import get_all_routers, setup_all_menus

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DependencyInjectionMiddleware:
    """Middleware для внедрения зависимостей в обработчики"""

    def __init__(self, database: Database, menu_manager: MenuManager):
        self.database = database
        self.menu_manager = menu_manager

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Добавляем зависимости в контекст обработчика"""
        data.update({"database": self.database, "menu_manager": self.menu_manager})
        return await handler(event, data)


def setup_basic_handlers(dp: Dispatcher, menu_manager: MenuManager):
    """Настройка базовых обработчиков команд"""

    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        """Обработчик команды /start"""
        user_id = message.from_user.id
        text, keyboard = menu_manager.render_menu("main", user_id)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        """Обработчик команды /help"""
        help_text = """🤖 <b>Telegram Price Bot - Справка</b>

<b>📋 Основные функции:</b>
• Создание шаблонов сообщений с файлами
• Управление группами чатов для рассылки
• Автоматическая рассылка по выбранным группам
• История и статистика рассылок

<b>🚀 Быстрый старт:</b>
1. Создайте шаблон сообщения
2. Создайте группу чатов для рассылки
3. Запустите рассылку, выбрав шаблон и группы

<b>📝 Команды:</b>
/start - Главное меню
/help - Справка
/id - Получить ID текущего чата
/templates - Шаблоны сообщений
/groups - Группы чатов
/mailing - Рассылка

<b>📝 Примечания:</b>
• Бот должен быть администратором в чатах
• Можно прикреплять файлы к шаблонам
• Поддерживается HTML разметка в тексте"""
        await message.answer(help_text, parse_mode="HTML")

    @dp.message(Command("id"))
    async def cmd_id(message: types.Message):
        """Обработчик команды /id - получение ID чата"""
        chat_info = f"💬 <b>Информация о чате:</b>\n\n"
        chat_info += f"ID: <code>{message.chat.id}</code>\n"
        chat_info += f"Тип: {message.chat.type}\n"

        if message.chat.type != "private":
            chat_info += f"Название: {message.chat.title or 'Без названия'}\n"
            if message.chat.username:
                chat_info += f"Username: @{message.chat.username}\n"

        chat_info += f"\n<b>Пользователь:</b>\n"
        chat_info += f"ID: <code>{message.from_user.id}</code>\n"
        chat_info += f"Имя: {message.from_user.first_name}"

        if message.from_user.last_name:
            chat_info += f" {message.from_user.last_name}"

        if message.from_user.username:
            chat_info += f"\nUsername: @{message.from_user.username}"

        await message.answer(chat_info, parse_mode="HTML")

    @dp.message(Command("templates"))
    async def cmd_templates(message: types.Message):
        """Быстрый переход к шаблонам"""
        user_id = message.from_user.id
        text, keyboard = menu_manager.render_menu("templates", user_id)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    @dp.message(Command("groups"))
    async def cmd_groups(message: types.Message):
        """Быстрый переход к группам"""
        user_id = message.from_user.id
        text, keyboard = menu_manager.render_menu("groups", user_id)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    @dp.message(Command("mailing"))
    async def cmd_mailing(message: types.Message):
        """Быстрый переход к рассылке"""
        user_id = message.from_user.id
        text, keyboard = menu_manager.render_menu("mailing", user_id)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    # Обработчик навигации по меню
    @dp.callback_query(lambda c: c.data.startswith("menu_"))
    async def handle_menu_navigation(callback: types.CallbackQuery):
        """Обработчик навигации по меню"""
        menu_id = callback.data.replace("menu_", "")
        success = await menu_manager.navigate_to(menu_id, callback)
        if not success:
            await callback.answer("❌ Ошибка навигации", show_alert=True)


def setup_routers(dp: Dispatcher):
    """Настройка роутеров для разных модулей"""
    routers = get_all_routers()
    for router in routers:
        dp.include_router(router)


def setup_middlewares(
    dp: Dispatcher, config: Config, database: Database, menu_manager: MenuManager
):
    """Настройка middleware"""
    # Middleware для проверки доступа и внедрения зависимостей
    menu_middleware = MenuMiddleware(menu_manager, config.admin_ids)
    dp.message.middleware.register(menu_middleware)
    dp.callback_query.middleware.register(menu_middleware)

    # Middleware для внедрения зависимостей
    di_middleware = DependencyInjectionMiddleware(database, menu_manager)
    dp.message.middleware.register(di_middleware)
    dp.callback_query.middleware.register(di_middleware)


async def main():
    """Основная функция запуска бота"""
    logger.info("🚀 Запуск Telegram Price Bot...")

    try:
        cfg = Config()

        # Инициализация компонентов
        logger.info("📊 Инициализация базы данных...")
        database = Database(cfg.database_url)
        await database.init_database()

        logger.info("🎛️ Инициализация системы меню...")
        menu_manager = MenuManager(cfg.admin_ids)
        setup_all_menus(menu_manager)

        logger.info("🤖 Инициализация бота...")
        bot = Bot(token=cfg.bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)

        # Настройка компонентов
        logger.info("🔧 Настройка обработчиков...")
        setup_basic_handlers(dp, menu_manager)
        setup_routers(dp)
        setup_middlewares(dp, cfg, database, menu_manager)

        # Проверка конфигурации
        logger.info("✅ Проверка конфигурации...")
        logger.info(f"📋 Администраторы: {cfg.admin_ids}")
        logger.info(f"💾 База данных: {cfg.database_url}")

        # Запуск бота
        logger.info("🎯 Бот запущен и готов к работе!")
        await dp.start_polling(
            bot, allowed_updates=["message", "callback_query"], skip_updates=True
        )

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        logger.info("🛑 Завершение работы бота...")
        if "database" in locals():
            await database.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал завершения (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка: {e}")
        sys.exit(1)
