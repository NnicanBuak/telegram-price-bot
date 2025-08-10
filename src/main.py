#!/usr/bin/env python3
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram import types

from config import Config
from database import Database
from menu_system import MenuManager, MenuMiddleware
from bot.menus import setup_bot_menus
from bot.handlers.menu_handlers import menu_router

# from bot.handlers.mailing_handlers import mailing_router
# from bot.handlers.template_handlers import template_router
# from bot.handlers.group_handlers import group_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Глобальные переменные для использования в обработчиках и тестах
bot = None
db = None
menu_manager = None
bot_menus = None
config = None
dp = None


# ========== КОМАНДЫ ДЛЯ ЭКСПОРТА В ТЕСТЫ ==========


async def cmd_start(message: types.Message):
    """Обработчик команды /start - экспортируется для тестов"""
    global menu_manager
    if not menu_manager:
        await message.answer("❌ Бот еще не инициализирован")
        return

    user_id = message.from_user.id
    text, keyboard = menu_manager.render_menu("main", user_id)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def cmd_help(message: types.Message):
    """Обработчик команды /help - экспортируется для тестов"""
    help_text = """
<b>📚 Доступные команды:</b>

/start - Главное меню
/help - Эта справка
/templates - Управление шаблонами
/groups - Управление группами чатов
/mailing - Создать рассылку
/history - История рассылок
/id - Получить ID чата

<b>💡 Как пользоваться:</b>
1. Создайте шаблон сообщения
2. Создайте группу чатов для рассылки
3. Запустите рассылку

<b>🔧 Техническая поддержка:</b>
Если возникли проблемы, обратитесь к администратору.
    """
    await message.answer(help_text, parse_mode="HTML")


async def cmd_id(message: types.Message):
    """Обработчик команды /id - экспортируется для тестов"""
    chat_id = message.chat.id
    user_id = message.from_user.id

    text = f"<b>📋 Информация о чате:</b>\n\n"
    text += f"🆔 ID чата: <code>{chat_id}</code>\n"
    text += f"👤 Ваш ID: <code>{user_id}</code>\n"
    text += f"📝 Тип чата: {message.chat.type}\n"

    if message.chat.title:
        text += f"📌 Название: {message.chat.title}\n"

    await message.answer(text, parse_mode="HTML")


# ========== ФУНКЦИИ ИНИЦИАЛИЗАЦИИ ==========


async def init_config():
    """Инициализация конфигурации"""
    global config
    logger.info("⚙️ Инициализация конфигурации...")
    try:
        config = Config()
        logger.info(f"✅ Конфигурация загружена (режим: {config.environment})")
        return config
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
        raise


async def init_bot(config: Config):
    """Инициализация бота"""
    global bot
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

        # Проверяем подключение к Telegram API
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот подключен: @{bot_info.username}")
        return bot
    except Exception as e:
        logger.error(f"❌ Ошибка создания бота: {e}")
        raise


async def init_database(config: Config):
    """Инициализация базы данных"""
    global db
    logger.info("🗄️ Инициализация базы данных...")
    try:
        db = Database(config.database_url)
        await db.init_db()
        logger.info("✅ База данных инициализирована")
        return db
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise


async def init_menu_system(config: Config):
    """Инициализация системы меню"""
    global menu_manager, bot_menus
    logger.info("📋 Инициализация системы меню...")
    try:
        menu_manager = MenuManager(config.admin_ids)
        bot_menus = setup_bot_menus(menu_manager)
        logger.info("✅ Система меню инициализирована")
        return menu_manager, bot_menus
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации меню: {e}")
        raise


async def init_dispatcher(config: Config, menu_manager: MenuManager):
    """Инициализация диспетчера"""
    global dp
    logger.info("🚦 Инициализация диспетчера...")
    try:
        # Создаем диспетчер
        dp = Dispatcher(storage=MemoryStorage())

        # Регистрируем middleware
        menu_middleware = MenuMiddleware(menu_manager, config.admin_ids)
        dp.message.middleware(menu_middleware)
        dp.callback_query.middleware(menu_middleware)

        # Регистрируем базовые команды
        dp.message.register(cmd_start, Command("start"))
        dp.message.register(cmd_help, Command("help"))
        dp.message.register(cmd_id, Command("id"))

        # Регистрируем роутеры
        dp.include_router(menu_router)
        # dp.include_router(mailing_router)
        # dp.include_router(template_router)
        # dp.include_router(group_router)

        logger.info("✅ Диспетчер инициализирован")
        return dp
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации диспетчера: {e}")
        raise


# ========== ОСНОВНАЯ ФУНКЦИЯ ==========


async def main():
    """Основная функция запуска бота"""
    global bot, db, menu_manager, bot_menus, config, dp

    logger.info("🚀 Запуск Telegram Price Bot...")

    try:
        # Последовательная инициализация всех компонентов
        config = await init_config()
        bot = await init_bot(config)
        db = await init_database(config)
        menu_manager, bot_menus = await init_menu_system(config)
        dp = await init_dispatcher(config, menu_manager)

        logger.info("🎉 Все компоненты инициализированы успешно!")
        logger.info(f"👥 Администраторы: {config.admin_ids}")
        logger.info(f"🗄️ База данных: {config.database_url}")

        # Запускаем бота
        logger.info("▶️ Запуск polling...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])

    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise
    finally:
        await cleanup()


async def cleanup():
    """Очистка ресурсов при завершении"""
    logger.info("🧹 Очистка ресурсов...")

    global bot, db, dp

    if dp:
        await dp.stop_polling()
        logger.info("✅ Polling остановлен")

    if db:
        await db.close()
        logger.info("✅ База данных закрыта")

    if bot:
        await bot.session.close()
        logger.info("✅ Сессия бота закрыта")

    logger.info("🏁 Очистка завершена")


# ========== ФУНКЦИИ ДЛЯ ТЕСТОВ ==========


async def get_bot_instance():
    """Получить экземпляр бота для тестов"""
    global bot
    if not bot:
        config = await init_config()
        bot = await init_bot(config)
    return bot


async def get_db_instance():
    """Получить экземпляр БД для тестов"""
    global db
    if not db:
        config = await init_config()
        db = await init_database(config)
    return db


async def get_menu_manager_instance():
    """Получить экземпляр менеджера меню для тестов"""
    global menu_manager
    if not menu_manager:
        config = await init_config()
        menu_manager, _ = await init_menu_system(config)
    return menu_manager


def reset_global_state():
    """Сброс глобального состояния для тестов"""
    global bot, db, menu_manager, bot_menus, config, dp
    bot = None
    db = None
    menu_manager = None
    bot_menus = None
    config = None
    dp = None


# ========== ТОЧКА ВХОДА ==========

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До свидания!")
    except Exception as e:
        logger.error(f"💥 Фатальная ошибка: {e}")
        exit(1)
