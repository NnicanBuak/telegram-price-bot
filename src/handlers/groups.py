import logging
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import menu_handler

logger = logging.getLogger(__name__)


def get_router(deps) -> Router:
    """Возвращает роутер с обработчиками групп"""
    router = Router()

    @menu_handler(deps.menu_manager, "groups_create")
    async def create_group(callback: types.CallbackQuery, context: dict):
        """Создать новую группу"""
        await callback.message.edit_text(
            "➕ <b>Создание группы чатов</b>\n\n"
            "Функция создания групп пока в разработке.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_groups")]
                ]
            ),
        )
        await callback.answer()

    @menu_handler(deps.menu_manager, "groups_list")
    async def list_groups(callback: types.CallbackQuery, context: dict):
        """Показать список групп"""
        try:
            groups = await deps.database.get_chat_groups()

            if not groups:
                text = "👥 <b>Список групп чатов</b>\n\n❌ Группы не найдены"
            else:
                text = f"👥 <b>Список групп чатов</b>\n\n📊 Найдено: {len(groups)}\n\n"
                for group in groups[:5]:  # Показываем первые 5
                    text += f"👥 {group.name} ({len(group.chat_ids)} чатов)\n"

                if len(groups) > 5:
                    text += f"\n... и еще {len(groups) - 5} групп"

            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="◀️ Назад", callback_data="menu_groups"
                            )
                        ]
                    ]
                ),
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка получения списка групп: {e}")
            await callback.answer("❌ Ошибка загрузки списка", show_alert=True)

    return router
