import logging
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import menu_handler

logger = logging.getLogger(__name__)


def get_router(deps) -> Router:
    """Возвращает роутер с обработчиками рассылки"""
    router = Router()

    @menu_handler(deps.menu_manager, "mailing_create")
    async def create_mailing(callback: types.CallbackQuery, context: dict):
        """Создать новую рассылку"""
        await callback.message.edit_text(
            "📮 <b>Создание рассылки</b>\n\n"
            "Функция создания рассылок пока в разработке.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_mailing")]
                ]
            ),
        )
        await callback.answer()

    @menu_handler(deps.menu_manager, "mailings_history")
    async def show_mailings_history(callback: types.CallbackQuery, context: dict):
        """Показать историю рассылок"""
        try:
            mailings = await deps.database.get_mailings_history(limit=10)

            if not mailings:
                text = "📊 <b>История рассылок</b>\n\n❌ Рассылки не найдены"
            else:
                text = f"📊 <b>История рассылок</b>\n\n📊 Найдено: {len(mailings)}\n\n"
                for mailing in mailings[:5]:  # Показываем первые 5
                    status_icon = {
                        "pending": "⏳",
                        "running": "🔄",
                        "completed": "✅",
                        "failed": "❌",
                    }.get(mailing.status, "❓")

                    text += f"{status_icon} ID {mailing.id} | {mailing.status}\n"
                    text += (
                        f"📊 {mailing.sent_count}/{mailing.total_chats} отправлено\n\n"
                    )

                if len(mailings) > 5:
                    text += f"... и еще {len(mailings) - 5} рассылок"

            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔄 Обновить", callback_data="mailings_history"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="◀️ Назад", callback_data="menu_mailing"
                            )
                        ],
                    ]
                ),
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка получения истории рассылок: {e}")
            await callback.answer("❌ Ошибка загрузки истории", show_alert=True)

    return router
