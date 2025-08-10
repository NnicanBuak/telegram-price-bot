"""Обработчики для работы с шаблонами"""

from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from typing import TYPE_CHECKING

from shared.menu_builder import MenuBuilder
from shared.keyboard_utils import KeyboardUtils

if TYPE_CHECKING:
    from database import Database

templates_router = Router()


@templates_router.callback_query(F.data == "templates_list")
async def show_templates_list(callback: types.CallbackQuery, database: "Database"):
    """Показать список шаблонов с пагинацией"""
    templates = await database.get_templates()

    if not templates:
        menu = MenuBuilder.back_menu(
            "📋 <b>Список шаблонов</b>\n\n❌ Нет созданных шаблонов", "menu_templates"
        )
        await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])
        return

    # Используем готовую пагинацию
    keyboard = KeyboardUtils.paginated_list(
        templates,
        page=0,
        item_callback_prefix="template_view",
        page_callback_prefix="templates_page",
        icon="📄",
    )

    # Добавляем кнопку "Назад"
    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_templates")]
    )

    text = f"📋 <b>Список шаблонов</b>\n\nВсего: {len(templates)}"
    await callback.message.edit_text(text, reply_markup=keyboard)


@templates_router.callback_query(F.data == "template_create")
async def create_template(callback: types.CallbackQuery):
    """Создание нового шаблона"""
    # Здесь ваша логика создания шаблона
    menu = MenuBuilder.back_menu(
        "📝 <b>Создание шаблона</b>\n\nОтправьте текст для нового шаблона:",
        "menu_templates",
    )
    await callback.message.edit_text(menu["text"], reply_markup=menu["keyboard"])
