import logging
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command

from shared.menu import create_menu_system, MenuBuilder, create_crud_menu
from config import Config
from database import Database

logger = logging.getLogger(__name__)


# Инициализация меню
def setup_menus(menu_manager):
    # Главное меню
    main_menu = (
        MenuBuilder("main")
        .title("🏠 Главное меню")
        .description(
            "Добро пожаловать в Telegram Price Bot!\n\nВыберите нужную функцию:"
        )
        .add_menu_link("📄 Шаблоны сообщений", "templates")
        .add_menu_link("👥 Группы чатов", "groups")
        .add_menu_link("📮 Рассылка", "mailing")
        .add_action("📊 История рассылок", "mailings_history")
        .add_menu_link("⚙️ Настройки", "settings")
        .no_back_button()
        .build()
    )

    # CRUD меню для шаблонов
    templates_menu = (
        create_crud_menu("templates", "📄 Управление шаблонами")
        .back_button("main")
        .build()
    )

    # CRUD меню для групп
    groups_menu = (
        create_crud_menu("groups", "👥 Управление группами чатов")
        .back_button("main")
        .build()
    )

    # Меню рассылки
    mailing_menu = (
        MenuBuilder("mailing")
        .title("📮 Рассылка сообщений")
        .description(
            "Создавайте и запускайте рассылки по группам чатов.\nВыберите действие:"
        )
        .add_action("📮 Создать рассылку", "mailing_create")
        .add_action("📊 История рассылок", "mailings_history")
        .back_button("main")
        .build()
    )

    # Меню настроек
    settings_menu = (
        MenuBuilder("settings")
        .title("⚙️ Настройки системы")
        .description("Управление конфигурацией и мониторинг системы.")
        .add_action("📊 Статус системы", "system_status")
        .add_action("📋 Конфигурация", "system_config")
        .add_action("📝 Логи", "system_logs")
        .back_button("main")
        .build()
    )

    # Регистрируем все меню
    for menu in [main_menu, templates_menu, groups_menu, mailing_menu, settings_menu]:
        menu_manager.register_menu(menu)


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
        self.router.message(Command("config"))(self.cmd_config)
        self.router.message(Command("status"))(self.cmd_status)

        # Обработчики меню
        self.router.callback_query(F.data == "menu_main")(self.show_main_menu)
        self.router.callback_query(F.data == "menu_templates")(self.show_templates_menu)
        self.router.callback_query(F.data == "menu_groups")(self.show_groups_menu)
        self.router.callback_query(F.data == "menu_mailing")(self.show_mailing_menu)
        self.router.callback_query(F.data == "menu_settings")(self.show_settings_menu)

    async def cmd_start(self, message: types.Message):
        """Команда /start"""
        user_id = message.from_user.id

        if not self.config.is_admin(user_id):
            logger.warning(f"Неавторизованный доступ от пользователя {user_id}")
            await message.answer(
                "❌ <b>Доступ запрещен</b>\n\n"
                "Этот бот доступен только администраторам.",
                parse_mode="HTML",
            )
            return

        logger.info(f"Администратор {user_id} запустил бота")

        # Показываем главное меню через обновленный интерфейс
        await self.show_main_menu_direct(message)

    async def show_main_menu_direct(self, message: types.Message):
        """Показать главное меню напрямую"""
        text = """🏠 <b>Главное меню</b>

Добро пожаловать в Telegram Price Bot!

Выберите нужную функцию:"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📄 Шаблоны сообщений", callback_data="menu_templates"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 Группы чатов", callback_data="menu_groups"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📮 Рассылка", callback_data="menu_mailing"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 История рассылок", callback_data="mailings_history"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ Настройки", callback_data="menu_settings"
                    )
                ],
            ]
        )

        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    async def cmd_help(self, message: types.Message):
        """Команда /help"""
        help_text = """📋 <b>Справка по боту</b>

<b>🔹 Основные функции:</b>
• <b>Шаблоны</b> - создание сообщений с файлами и текстом
• <b>Группы</b> - объединение чатов для рассылки
• <b>Рассылка</b> - отправка по выбранным группам
• <b>История</b> - статистика и мониторинг отправок

<b>🔹 Команды:</b>
/start - главное меню
/help - эта справка
/id - получить ID чата
/config - информация о конфигурации
/status - статус системы

<b>🔹 Как начать:</b>
1. Создайте шаблон сообщения
2. Добавьте группы чатов (получите ID командой /id в чатах)
3. Запустите рассылку

<b>💡 Совет:</b> Добавьте бота в чаты как администратора для корректной работы."""

        await message.answer(help_text, parse_mode="HTML")

    async def cmd_id(self, message: types.Message):
        """Команда /id"""
        chat_type_names = {
            "private": "Приватный чат",
            "group": "Группа",
            "supergroup": "Супергруппа",
            "channel": "Канал",
        }

        info = (
            f"💬 <b>Информация о чате</b>\n\n"
            f"🔢 <b>ID чата:</b> <code>{message.chat.id}</code>\n"
            f"📱 <b>Тип:</b> {chat_type_names.get(message.chat.type, message.chat.type)}\n"
            f"👤 <b>Ваш ID:</b> <code>{message.from_user.id}</code>\n"
        )

        if message.chat.title:
            info += f"📝 <b>Название:</b> {message.chat.title}\n"
        if message.from_user.username:
            info += f"📮 <b>Username:</b> @{message.from_user.username}\n"

        info += "\n💡 <i>Используйте ID чата для добавления в группы рассылки</i>"

        await message.answer(info, parse_mode="HTML")

    async def cmd_config(self, message: types.Message):
        """Команда /config - показать конфигурацию"""
        user_id = message.from_user.id

        if not self.config.is_admin(user_id):
            await message.answer("❌ Команда доступна только администраторам")
            return

        try:
            config_summary = self.config.get_config_summary()

            # Проверяем конфигурацию на ошибки
            errors = self.config.validate_config()
            if errors:
                config_summary += "\n\n⚠️ **Проблемы конфигурации:**\n"
                for error in errors:
                    config_summary += f"• {error}\n"
            else:
                config_summary += "\n\n✅ **Конфигурация корректна**"

            await message.answer(config_summary, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Ошибка получения конфигурации: {e}")
            await message.answer(f"❌ Ошибка получения конфигурации: {e}")

    async def cmd_status(self, message: types.Message, database: Database):
        """Команда /status - статус системы"""
        user_id = message.from_user.id

        if not self.config.is_admin(user_id):
            await message.answer("❌ Команда доступна только администраторам")
            return

        try:
            # Получаем статистику из БД
            templates_count = len(await database.get_templates())
            groups_count = len(await database.get_chat_groups())
            mailings_count = len(await database.get_mailings_history(limit=100))

            # Информация о системе
            import psutil
            import datetime

            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage(".").percent

            uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(
                psutil.boot_time()
            )

            status_text = f"""📊 <b>Статус системы</b>

🤖 <b>Бот:</b>
• Статус: ✅ Активен
• Администраторы: {len(self.config.admin_ids)}
• Режим отладки: {'🔧 Вкл' if self.config.debug else '🔒 Выкл'}

💾 <b>База данных:</b>
• Шаблоны: {templates_count}
• Группы: {groups_count}  
• Рассылки: {mailings_count}

🖥️ <b>Система:</b>
• Память: {memory_usage:.1f}%
• Диск: {disk_usage:.1f}%
• Аптайм: {str(uptime).split('.')[0]}

📁 <b>Директории:</b>
• Данные: {self.config.data_dir} ({'✅' if self.config.data_dir.exists() else '❌'})
• Логи: {self.config.log_dir} ({'✅' if self.config.log_dir.exists() else '❌'})
• БД: {self.config.db_dir} ({'✅' if self.config.db_dir.exists() else '❌'})"""

            await message.answer(status_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            await message.answer(f"❌ Ошибка получения статуса: {e}")

    async def show_main_menu(self, callback: types.CallbackQuery):
        """Показать главное меню через callback"""
        text = """🏠 <b>Главное меню</b>

Добро пожаловать в Telegram Price Bot!

Выберите нужную функцию:"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📄 Шаблоны сообщений", callback_data="menu_templates"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 Группы чатов", callback_data="menu_groups"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📮 Рассылка", callback_data="menu_mailing"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 История рассылок", callback_data="mailings_history"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⚙️ Настройки", callback_data="menu_settings"
                    )
                ],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    async def show_templates_menu(self, callback: types.CallbackQuery):
        """Показать меню шаблонов"""
        text = """📄 <b>Управление шаблонами</b>

Создавайте и управляйте шаблонами сообщений для рассылки.
Выберите действие:"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Создать", callback_data="template_create"
                    )
                ],
                [InlineKeyboardButton(text="📋 Список", callback_data="template_list")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    async def show_groups_menu(self, callback: types.CallbackQuery):
        """Показать меню групп"""
        text = """👥 <b>Управление группами чатов</b>

Создавайте группы чатов для организации рассылок.
Выберите действие:"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Создать группу", callback_data="group_create"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Список групп", callback_data="groups_list"
                    )
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    async def show_mailing_menu(self, callback: types.CallbackQuery):
        """Показать меню рассылки"""
        text = """📮 <b>Рассылка сообщений</b>

Создавайте и запускайте рассылки по группам чатов.
Выберите действие:"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📮 Создать рассылку", callback_data="mailing_create"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 История рассылок", callback_data="mailings_history"
                    )
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    async def show_settings_menu(self, callback: types.CallbackQuery):
        """Показать меню настроек"""
        text = """⚙️ <b>Настройки системы</b>

Управление конфигурацией и мониторинг системы.
Выберите действие:"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 Статус системы", callback_data="system_status"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Конфигурация", callback_data="system_config"
                    )
                ],
                [InlineKeyboardButton(text="📝 Логи", callback_data="system_logs")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
