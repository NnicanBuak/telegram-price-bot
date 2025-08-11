import logging

from .base import HandlerModule, BaseHandler, HandlerContext

logger = logging.getLogger(__name__)


class CommandsModule(HandlerModule):
    def _setup_handlers(self):
        self.register_handler(
            "start", StartCommandHandler(self.config, self.database, self.menu_manager)
        )
        self.register_handler(
            "help", HelpCommandHandler(self.config, self.database, self.menu_manager)
        )
        self.register_handler(
            "id", IdCommandHandler(self.config, self.database, self.menu_manager)
        )


class StartCommandHandler(BaseHandler):
    async def execute(self, ctx: HandlerContext) -> bool:
        user_id = ctx.message.from_user.id

        if not ctx.is_programmatic and not ctx.config.is_admin(user_id):
            logger.warning(f"Неавторизованный доступ от пользователя {user_id}")
            await ctx.message.answer(
                "❌ <b>Доступ запрещен</b>\n\n"
                "Этот бот доступен только администраторам.",
                parse_mode=self.config.parse_mode,
            )
            return

        if not ctx.is_programmatic:
            logger.info(f"Администратор {user_id} запустил бота")
            await self.menu_manager.navigate_to("main", ctx.message, user_id)
        else:
            await self.menu_manager.sender.send_menu("main")


class HelpCommandHandler(BaseHandler):
    async def execute(self, ctx: HandlerContext) -> bool:
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

        await ctx.message.answer(help_text, parse_mode=self.config.parse_mode)


class IdCommandHandler(BaseHandler):
    async def execute(self, ctx: HandlerContext):
        """Команда /id"""
        chat_type_names = {
            "private": "Приватный чат",
            "group": "Группа",
            "supergroup": "Супергруппа",
            "channel": "Канал",
        }

        info = (
            f"💬 <b>Информация о чате</b>\n\n"
            f"🔢 <b>ID чата:</b> <code>{ctx.message.chat.id}</code>\n"
            f"📱 <b>Тип:</b> {chat_type_names.get(ctx.message.chat.type, ctx.message.chat.type)}\n"
            f"👤 <b>Ваш ID:</b> <code>{ctx.message.from_user.id}</code>\n"
        )

        if ctx.message.chat.title:
            info += f"📝 <b>Название:</b> {ctx.message.chat.title}\n"
        if ctx.message.from_user.username:
            info += f"📮 <b>Username:</b> @{ctx.message.from_user.username}\n"

        info += "\n💡 <i>Используйте ID чата для добавления в группы рассылки</i>"

        await ctx.message.answer(info, parse_mode=self.config.parse_mode)
