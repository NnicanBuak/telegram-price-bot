from typing import List, Optional, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ..models import Menu, MenuItem


class BaseKeyboard:
    """Базовый класс для создания клавиатур"""

    @staticmethod
    def create_empty() -> InlineKeyboardMarkup:
        """Создать пустую клавиатуру"""
        return InlineKeyboardMarkup(inline_keyboard=[])

    @staticmethod
    def create_single_button(
        text: str, callback_data: str = "", url: str = ""
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру с одной кнопкой"""
        if url:
            button = InlineKeyboardButton(text=text, url=url)
        else:
            button = InlineKeyboardButton(text=text, callback_data=callback_data)

        return InlineKeyboardMarkup(inline_keyboard=[[button]])

    @staticmethod
    def create_back_button(
        text: str = "◀️ Назад", callback_data: str = "back"
    ) -> List[InlineKeyboardButton]:
        """Создать кнопку назад"""
        return [InlineKeyboardButton(text=text, callback_data=callback_data)]

    @staticmethod
    def create_row_buttons(
        buttons_data: List[Dict[str, str]],
    ) -> List[InlineKeyboardButton]:
        """Создать ряд кнопок из данных"""
        buttons = []
        for button_data in buttons_data:
            if "url" in button_data:
                button = InlineKeyboardButton(
                    text=button_data["text"], url=button_data["url"]
                )
            else:
                button = InlineKeyboardButton(
                    text=button_data["text"],
                    callback_data=button_data.get("callback_data", ""),
                )
            buttons.append(button)
        return buttons

    @staticmethod
    def create_columns_layout(
        items: List[Any], columns: int, item_to_button_func
    ) -> List[List[InlineKeyboardButton]]:
        """Создать макет с колонками"""
        buttons = []

        for i in range(0, len(items), columns):
            row = []
            for j in range(columns):
                if i + j < len(items):
                    button = item_to_button_func(items[i + j])
                    row.append(button)

            if row:
                buttons.append(row)

        return buttons


class MenuKeyboard(BaseKeyboard):
    """Клавиатура для отображения меню"""

    @staticmethod
    def create_from_menu(
        menu: Menu,
        user_id: int,
        admin_ids: List[int],
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру из объекта меню"""
        buttons = []

        # Получаем видимые элементы
        visible_items = menu.get_visible_items(user_id, admin_ids)

        # Создаем кнопки для элементов меню
        item_buttons = MenuKeyboard._create_menu_item_buttons(
            visible_items, menu.columns
        )
        buttons.extend(item_buttons)

        # Добавляем дополнительные кнопки
        if additional_buttons:
            buttons.extend(additional_buttons)

        # Добавляем кнопку назад
        if menu.back_button and menu.back_to:
            back_button = BaseKeyboard.create_back_button(
                text=menu.back_button_text, callback_data=f"menu_{menu.back_to}"
            )
            buttons.append(back_button)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def _create_menu_item_buttons(
        items: List[MenuItem], columns: int
    ) -> List[List[InlineKeyboardButton]]:
        """Создать кнопки для элементов меню"""

        def item_to_button(item: MenuItem) -> InlineKeyboardButton:
            if item.url:
                return InlineKeyboardButton(text=item.button_text, url=item.url)
            else:
                return InlineKeyboardButton(
                    text=item.button_text, callback_data=item.callback_data
                )

        return BaseKeyboard.create_columns_layout(items, columns, item_to_button)


class UtilityKeyboards:
    """Утилитарные клавиатуры"""

    @staticmethod
    def create_yes_no(
        yes_text: str = "✅ Да",
        no_text: str = "❌ Нет",
        yes_callback: str = "yes",
        no_callback: str = "no",
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру Да/Нет"""
        buttons = [
            [
                InlineKeyboardButton(text=yes_text, callback_data=yes_callback),
                InlineKeyboardButton(text=no_text, callback_data=no_callback),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_numbered_list(
        items: List[str], callback_prefix: str = "select", start_number: int = 1
    ) -> InlineKeyboardMarkup:
        """Создать пронумерованный список"""
        buttons = []

        for i, item in enumerate(items):
            number = start_number + i
            button = InlineKeyboardButton(
                text=f"{number}. {item}", callback_data=f"{callback_prefix}_{i}"
            )
            buttons.append([button])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_toggle_list(
        items: List[Dict[str, Any]],
        selected_ids: List[Any],
        toggle_prefix: str = "toggle",
    ) -> InlineKeyboardMarkup:
        """Создать список с возможностью переключения"""
        buttons = []

        for item in items:
            item_id = item.get("id")
            text = item.get("text", str(item_id))
            is_selected = item_id in selected_ids

            icon = "✅" if is_selected else "☐"
            button_text = f"{icon} {text}"

            button = InlineKeyboardButton(
                text=button_text, callback_data=f"{toggle_prefix}_{item_id}"
            )
            buttons.append([button])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_action_menu(
        actions: Dict[str, str], back_callback: str = "back"
    ) -> InlineKeyboardMarkup:
        """Создать меню действий"""
        buttons = []

        for text, callback_data in actions.items():
            button = InlineKeyboardButton(text=text, callback_data=callback_data)
            buttons.append([button])

        # Кнопка назад
        back_button = BaseKeyboard.create_back_button(callback_data=back_callback)
        buttons.append(back_button)

        return InlineKeyboardMarkup(inline_keyboard=buttons)


class NavigationKeyboards:
    """Клавиатуры для навигации"""

    @staticmethod
    def create_breadcrumb(
        breadcrumbs: List[Dict[str, str]], separator: str = " › "
    ) -> InlineKeyboardMarkup:
        """Создать навигационные крошки"""
        if not breadcrumbs:
            return BaseKeyboard.create_empty()

        # Если крошек много, показываем только последние
        max_breadcrumbs = 3
        if len(breadcrumbs) > max_breadcrumbs:
            breadcrumbs = breadcrumbs[-max_breadcrumbs:]

        buttons = []
        for breadcrumb in breadcrumbs:
            button = InlineKeyboardButton(
                text=breadcrumb["text"], callback_data=breadcrumb["callback_data"]
            )
            buttons.append([button])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_quick_navigation(
        nav_items: Dict[str, str], columns: int = 2
    ) -> InlineKeyboardMarkup:
        """Создать быструю навигацию"""
        items = [
            {"text": text, "callback_data": callback}
            for text, callback in nav_items.items()
        ]

        def item_to_button(item):
            return InlineKeyboardButton(
                text=item["text"], callback_data=item["callback_data"]
            )

        button_rows = BaseKeyboard.create_columns_layout(items, columns, item_to_button)
        return InlineKeyboardMarkup(inline_keyboard=button_rows)
