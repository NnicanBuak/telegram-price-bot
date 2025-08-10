from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional, Any


class KeyboardUtils:
    """Утилиты для создания клавиатур"""

    @staticmethod
    def paginated_list(
        items: List[Any],
        page: int = 0,
        page_size: int = 5,
        item_callback_prefix: str = "view",
        page_callback_prefix: str = "page",
        icon: str = "📄",
    ) -> InlineKeyboardMarkup:
        """Пагинированный список элементов"""
        start = page * page_size
        end = start + page_size
        page_items = items[start:end]

        buttons = []

        # Элементы страницы
        for item in page_items:
            item_name = getattr(item, "name", str(item))
            # Ограничиваем длину названия
            display_name = item_name[:30] + "..." if len(item_name) > 30 else item_name

            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"{icon} {display_name}",
                        callback_data=f"{item_callback_prefix}_{item.id}",
                    )
                ]
            )

        # Навигация
        nav_row = []
        if page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    text="◀️", callback_data=f"{page_callback_prefix}_{page-1}"
                )
            )
        if end < len(items):
            nav_row.append(
                InlineKeyboardButton(
                    text="▶️", callback_data=f"{page_callback_prefix}_{page+1}"
                )
            )

        if nav_row:
            buttons.append(nav_row)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def toggle_list(
        items: List[Any],
        selected_items: List[int],
        toggle_callback_prefix: str = "toggle",
        item_name_attr: str = "name",
    ) -> List[List[InlineKeyboardButton]]:
        """Список с возможностью выбора нескольких элементов"""
        buttons = []

        for item in items:
            item_name = getattr(item, item_name_attr, str(item))
            is_selected = item.id in selected_items

            # Иконка в зависимости от выбора
            icon = "✅" if is_selected else "☐"
            button_text = f"{icon} {item_name}"

            buttons.append(
                [
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"{toggle_callback_prefix}_{item.id}",
                    )
                ]
            )

        return buttons
