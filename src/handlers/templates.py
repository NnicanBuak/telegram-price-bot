import logging
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from menu import menu_handler

logger = logging.getLogger(__name__)


def get_router(deps) -> Router:
    """Возвращает роутер с обработчиками шаблонов"""
    router = Router()

    @menu_handler(deps.menu_manager, "templates_create")
    async def create_template(callback: types.CallbackQuery, context: dict):
        """Создать новый шаблон"""
        await callback.message.edit_text(
            "➕ <b>Создание шаблона</b>\n\n"
            "Функция создания шаблонов пока в разработке.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад", callback_data="menu_templates"
                        )
                    ]
                ]
            ),
        )
        await callback.answer()

    @menu_handler(deps.menu_manager, "templates_list")
    async def list_templates(callback: types.CallbackQuery, context: dict):
        """Показать список шаблонов"""
        try:
            templates = await deps.database.get_templates()

            if not templates:
                text = "📄 <b>Список шаблонов</b>\n\n❌ Шаблоны не найдены"
            else:
                text = f"📄 <b>Список шаблонов</b>\n\n📊 Найдено: {len(templates)}\n\n"
                for template in templates[:5]:  # Показываем первые 5
                    icon = "📎" if template.file_id else "📄"
                    text += f"{icon} {template.name}\n"

                if len(templates) > 5:
                    text += f"\n... и еще {len(templates) - 5} шаблонов"

            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="◀️ Назад", callback_data="menu_templates"
                            )
                        ]
                    ]
                ),
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка получения списка шаблонов: {e}")
            await callback.answer("❌ Ошибка загрузки списка", show_alert=True)

    return router
