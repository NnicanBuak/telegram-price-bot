"""
Основной файл Telegram Price Bot
Обновлен для новой архитектуры с разделением по features
"""

import asyncio
import logging
import sys
import os
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

# Добавляем src в Python path для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Импорты основных компонентов
from config import config
from database import Database
from shared.menu_system import MenuManager, MenuMiddleware

# Импорты роутеров из features
from features.templates.handlers import template_router
from features.groups.handlers import group_router
from features.mailing.handlers import mailing_router
from features.common.handlers import menu_router

# Настройка логирования
logging.basicConfig(
    menu_manager.register_menu(mailing_menu)
    
    # Меню настроек
    settings_menu = Menu(
        id="settings",
        title="⚙️ <b>Настройки</b>",
        description="Конфигурация и управление ботом",
        back_to="main",
        admin_only=True,
        columns=1
    )
    
    settings_menu.add_item(MenuItem(
        id="backup",
        text="Резервная копия",
        icon="💾",
        callback_data="backup_create",
        admin_only=True,
        order=1
    ))
    
    settings_menu.add_item(MenuItem(
        id="logs",
        text="Логи системы",
        icon="📋",
        callback_data="logs_view",
        admin_only=True,
        order=2
    ))
    
    settings_menu.add_item(MenuItem(
        id="stats",
        text="Статистика",
        icon="📈",
        callback_data="stats_view",
        admin_only=True,
        order=3
    ))
    
    menu_manager.register_menu(settings_menu)


async def setup_handlers(dp: Dispatcher, menu_manager: MenuManager):
    """Настройка обработчиков команд и callback'ов"""
    
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
    # Включаем роутеры в правильном порядке
    dp.include_router(template_router)
    dp.include_router(group_router) 
    dp.include_router(mailing_router)
    dp.include_router(menu_router)  # Общие обработчики в конце


def setup_middlewares(dp: Dispatcher, database: Database, menu_manager: MenuManager):
    """Настройка middleware"""
    # Middleware для проверки доступа и внедрения зависимостей
    menu_middleware = MenuMiddleware(menu_manager, config.ADMIN_IDS)
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
        # Инициализация компонентов
        logger.info("📊 Инициализация базы данных...")
        database = Database(config.DATABASE_URL)
        await database.init_database()
        
        logger.info("🎛️ Инициализация системы меню...")
        menu_manager = MenuManager(config.ADMIN_IDS)
        setup_main_menus(menu_manager)
        
        logger.info("🤖 Инициализация бота...")
        bot = Bot(token=config.BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Настройка компонентов
        logger.info("🔧 Настройка обработчиков...")
        await setup_handlers(dp, menu_manager)
        setup_routers(dp)
        setup_middlewares(dp, database, menu_manager)
        
        # Проверка конфигурации
        logger.info("✅ Проверка конфигурации...")
        logger.info(f"📋 Администраторы: {config.ADMIN_IDS}")
        logger.info(f"💾 База данных: {config.DATABASE_URL}")
        
        # Запуск бота
        logger.info("🎯 Бот запущен и готов к работе!")
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query"],
            skip_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        logger.info("🛑 Завершение работы бота...")
        if 'database' in locals():
            await database.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал завершения (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка: {e}")
        sys.exit(1)level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
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
        data: Dict[str, Any]
    ) -> Any:
        """Добавляем зависимости в контекст обработчика"""
        data.update({
            'database': self.database,
            'menu_manager': self.menu_manager
        })
        return await handler(event, data)


def setup_main_menus(menu_manager: MenuManager):
    """Настройка основных меню системы"""
    from shared.menu_system import Menu, MenuItem
    
    # Главное меню
    main_menu = Menu(
        id="main",
        title="🏠 <b>Главное меню</b>",
        description="Добро пожаловать в Telegram Price Bot!\n\nВыберите нужную функцию:",
        columns=1
    )
    
    main_menu.add_item(MenuItem(
        id="templates",
        text="Шаблоны сообщений",
        icon="📄",
        callback_data="menu_templates",
        order=1
    ))
    
    main_menu.add_item(MenuItem(
        id="groups", 
        text="Группы чатов",
        icon="👥",
        callback_data="menu_groups",
        order=2
    ))
    
    main_menu.add_item(MenuItem(
        id="mailing",
        text="Рассылка",
        icon="📮",
        callback_data="menu_mailing", 
        order=3
    ))
    
    main_menu.add_item(MenuItem(
        id="history",
        text="История рассылок",
        icon="📊",
        callback_data="mailings_history",
        order=4
    ))
    
    main_menu.add_item(MenuItem(
        id="settings",
        text="Настройки",
        icon="⚙️",
        callback_data="menu_settings",
        admin_only=True,
        order=5
    ))
    
    menu_manager.register_menu(main_menu)
    
    # Меню шаблонов
    templates_menu = Menu(
        id="templates",
        title="📄 <b>Шаблоны сообщений</b>",
        description="Создание и управление шаблонами для рассылки",
        back_to="main",
        columns=1
    )
    
    templates_menu.add_item(MenuItem(
        id="templates_list",
        text="Список шаблонов",
        icon="📋",
        callback_data="templates_list",
        order=1
    ))
    
    templates_menu.add_item(MenuItem(
        id="templates_new",
        text="Создать новый",
        icon="➕",
        callback_data="templates_new",
        order=2
    ))
    
    templates_menu.add_item(MenuItem(
        id="templates_export",
        text="Экспорт шаблонов",
        icon="📤",
        callback_data="template_export_all",
        admin_only=True,
        order=3
    ))
    
    templates_menu.add_item(MenuItem(
        id="templates_import",
        text="Импорт шаблонов", 
        icon="📥",
        callback_data="template_import",
        admin_only=True,
        order=4
    ))
    
    menu_manager.register_menu(templates_menu)
    
    # Меню групп
    groups_menu = Menu(
        id="groups",
        title="👥 <b>Группы чатов</b>",
        description="Управление группами чатов для рассылки",
        back_to="main",
        columns=1
    )
    
    groups_menu.add_item(MenuItem(
        id="groups_list",
        text="Список групп",
        icon="📋", 
        callback_data="groups_list",
        order=1
    ))
    
    groups_menu.add_item(MenuItem(
        id="groups_new",
        text="Создать группу",
        icon="➕",
        callback_data="group_create",
        order=2
    ))
    
    menu_manager.register_menu(groups_menu)
    
    # Меню рассылки
    mailing_menu = Menu(
        id="mailing",
        title="📮 <b>Рассылка сообщений</b>",
        description="Создание и запуск рассылок по группам чатов",
        back_to="main",
        columns=1
    )
    
    mailing_menu.add_item(MenuItem(
        id="mailing_create",
        text="Создать рассылку",
        icon="📮",
        callback_data="mailing_create",
        order=1
    ))
    
    mailing_menu.add_item(MenuItem(
        id="mailing_history",
        text="История рассылок",
        icon="📊",
        callback_data="mailings_history",
        order=2
    ))