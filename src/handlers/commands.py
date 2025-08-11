import logging
from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from menu import MenuManager, MenuRegistry
from config import Config
from database import Database

logger = logging.getLogger(__name__)


def get_router(
    config: Config,
    database: Database,
    menu_manager: MenuManager,
    menu_registry: MenuRegistry,
) -> Router:
    """Возвращает роутер с командами"""
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: types.Message):
        """Команда /start"""
        user_id = message.from_user.id

        if not config.is_admin(user_id):
            logger.warning(f"Неавторизованный доступ от пользователя {user_id}")
            await message.answer(
                "❌ <b>Доступ запрещен</b>\n\n"
                "Этот бот доступен только администраторам.",
                parse_mode="HTML",
            )
            return

        logger.info(f"Администратор {user_id} запустил бота")

        # Показываем главное меню
        await menu_manager.navigate_to("main", message, user_id)

    @router.message(Command("help"))
    async def cmd_help(message: types.Message):
        """Команда /help"""
        help_text = """📋 <b>Справка по боту</b>

<b>🔹 Основные функции:</b>
- <b>Шаблоны</b> - создание сообщений с файлами и текстом
- <b>Группы</b> - объединение чатов для рассылки
- <b>Рассылка</b> - отправка по выбранным группам
- <b>История</b> - статистика и мониторинг отправок

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

    @router.message(Command("id"))
    async def cmd_id(message: types.Message):
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

    @router.message(Command("config"))
    async def cmd_config(message: types.Message):
        """Команда /config - показать конфигурацию"""
        user_id = message.from_user.id

        if not config.is_admin(user_id):
            await message.answer("❌ Команда доступна только администраторам")
            return

        try:
            config_summary = config.get_config_summary()

            # Проверяем конфигурацию на ошибки
            errors = config.validate_config()
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

    @router.message(Command("status"))
    async def cmd_status(message: types.Message):
        """Команда /status - статус системы"""
        user_id = message.from_user.id

        if not config.is_admin(user_id):
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
- Статус: ✅ Активен
- Администраторы: {len(config.admin_ids)}
- Режим отладки: {'🔧 Вкл' if config.debug else '🔒 Выкл'}

💾 <b>База данных:</b>
- Шаблоны: {templates_count}
- Группы: {groups_count}  
- Рассылки: {mailings_count}

🖥️ <b>Система:</b>
- Память: {memory_usage:.1f}%
- Диск: {disk_usage:.1f}%
- Аптайм: {str(uptime).split('.')[0]}

📁 <b>Директории:</b>
- Данные: {config.data_dir} ({'✅' if config.data_dir.exists() else '❌'})
- Логи: {config.log_dir} ({'✅' if config.log_dir.exists() else '❌'})
- БД: {config.db_dir} ({'✅' if config.db_dir.exists() else '❌'})"""

            await message.answer(status_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            await message.answer(f"❌ Ошибка получения статуса: {e}")

    return router
