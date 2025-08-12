import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command

from services import bot

logger = logging.getLogger(__name__)


def get_router(deps) -> Router:
    """Возвращает роутер с обработчиками команд"""
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: types.Message):
        """Команда /start"""
        user_id = message.from_user.id

        if not deps.config.is_admin(user_id):
            await message.answer(
                "❌ <b>Доступ запрещен</b>\n\n"
                "Этот бот доступен только администраторам.",
                parse_mode=deps.config.parse_mode,
            )
            return

        logger.info(f"Администратор {user_id} запустил бота")

        success = await deps.menu_manager.show_menu(
            menu_id="main", bot=bot, chat_id=message.chat.id
        )

        if not success:
            await message.answer("❌ Ошибка загрузки меню")

    @router.message(Command("help"))
    async def cmd_help(message: types.Message):
        """Команда /help"""
        help_text = await bot.get_help_text()
        await message.answer(help_text, parse_mode=deps.config.parse_mode)

    @router.message(Command("id"))
    async def cmd_id(message: types.Message):
        """Команда /id"""
        info_text = bot.get_chat_info(message)
        await message.answer(info_text, parse_mode=deps.config.parse_mode)

    return router
