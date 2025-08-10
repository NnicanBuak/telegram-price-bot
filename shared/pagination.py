"""
Утилиты для пагинации в Telegram ботах
Вынесено из handlers для переиспользования
"""

from typing import List, Any, Optional, Callable
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class PaginationHelper:
    """Помощник для создания пагинированных клавиатур"""

    @staticmethod
    def create_paginated_keyboard(
        items: List[Any],
        page: int = 0,
        items_per_page: int = 5,
        item_text_func: Optional[Callable[[Any], str]] = None,
        item_callback_func: Optional[Callable[[Any], str]] = None,
        item_icon: str = "📄",
        page_callback_prefix: str = "page",
        show_navigation: bool = True,
        show_page_info: bool = True,
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """
        Создать пагинированную клавиатуру

        Args:
            items: Список элементов для отображения
            page: Номер текущей страницы (начинается с 0)
            items_per_page: Количество элементов на странице
            item_text_func: Функция для получения текста кнопки из элемента
            item_callback_func: Функция для получения callback_data из элемента
            item_icon: Иконка для элементов
            page_callback_prefix: Префикс для callback_data навигации
            show_navigation: Показывать ли кнопки навигации
            show_page_info: Показывать ли информацию о странице
            additional_buttons: Дополнительные кнопки внизу
        """
        buttons = []
        total_items = len(items)
        total_pages = (
            (total_items + items_per_page - 1) // items_per_page
            if total_items > 0
            else 1
        )

        # Ограничиваем номер страницы
        page = max(0, min(page, total_pages - 1))

        # Элементы текущей страницы
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_items = items[start_idx:end_idx]

        # Создаем кнопки для элементов страницы
        for item in page_items:
            if item_text_func:
                text = item_text_func(item)
            else:
                # Пытаемся получить текст из атрибутов объекта
                text = getattr(item, "name", getattr(item, "title", str(item)))

            if item_callback_func:
                callback_data = item_callback_func(item)
            else:
                # Пытаемся получить ID из атрибутов объекта
                item_id = getattr(item, "id", None)
                callback_data = f"item_{item_id}" if item_id else "unknown"

            button_text = f"{item_icon} {text}".strip() if item_icon else text
            buttons.append(
                [InlineKeyboardButton(text=button_text, callback_data=callback_data)]
            )

        # Навигация
        if show_navigation and total_pages > 1:
            nav_row = []

            # Кнопка "Назад"
            if page > 0:
                nav_row.append(
                    InlineKeyboardButton(
                        text="◀️", callback_data=f"{page_callback_prefix}_{page-1}"
                    )
                )

            # Информация о странице
            if show_page_info:
                nav_row.append(
                    InlineKeyboardButton(
                        text=f"{page + 1}/{total_pages}",
                        callback_data="noop",  # Неактивная кнопка
                    )
                )

            # Кнопка "Вперед"
            if page < total_pages - 1:
                nav_row.append(
                    InlineKeyboardButton(
                        text="▶️", callback_data=f"{page_callback_prefix}_{page+1}"
                    )
                )

            if nav_row:
                buttons.append(nav_row)

        # Дополнительные кнопки
        if additional_buttons:
            buttons.extend(additional_buttons)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_simple_list_keyboard(
        items: List[Any],
        item_text_func: Optional[Callable[[Any], str]] = None,
        item_callback_func: Optional[Callable[[Any], str]] = None,
        item_icon: str = "📄",
        columns: int = 1,
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """
        Создать простую клавиатуру со списком (без пагинации)

        Args:
            items: Список элементов
            item_text_func: Функция для получения текста кнопки
            item_callback_func: Функция для получения callback_data
            item_icon: Иконка для элементов
            columns: Количество колонок
            additional_buttons: Дополнительные кнопки
        """
        buttons = []

        # Группируем элементы по колонкам
        for i in range(0, len(items), columns):
            row = []
            for j in range(columns):
                if i + j < len(items):
                    item = items[i + j]

                    if item_text_func:
                        text = item_text_func(item)
                    else:
                        text = getattr(item, "name", getattr(item, "title", str(item)))

                    if item_callback_func:
                        callback_data = item_callback_func(item)
                    else:
                        item_id = getattr(item, "id", None)
                        callback_data = f"item_{item_id}" if item_id else "unknown"

                    button_text = f"{item_icon} {text}".strip() if item_icon else text
                    row.append(
                        InlineKeyboardButton(
                            text=button_text, callback_data=callback_data
                        )
                    )

            if row:
                buttons.append(row)

        # Дополнительные кнопки
        if additional_buttons:
            buttons.extend(additional_buttons)

        return InlineKeyboardMarkup(inline_keyboard=buttons)


class ConfirmationHelper:
    """Помощник для создания клавиатур подтверждения"""

    @staticmethod
    def create_confirmation_keyboard(
        confirm_text: str = "✅ Да",
        cancel_text: str = "❌ Отмена",
        confirm_callback: str = "confirm",
        cancel_callback: str = "cancel",
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру подтверждения"""
        buttons = [
            [
                InlineKeyboardButton(text=confirm_text, callback_data=confirm_callback),
                InlineKeyboardButton(text=cancel_text, callback_data=cancel_callback),
            ]
        ]

        if additional_buttons:
            buttons.extend(additional_buttons)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_back_keyboard(
        back_text: str = "◀️ Назад",
        back_callback: str = "back",
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру только с кнопкой назад"""
        buttons = [[InlineKeyboardButton(text=back_text, callback_data=back_callback)]]

        if additional_buttons:
            buttons.extend(additional_buttons)

        return InlineKeyboardMarkup(inline_keyboard=buttons)


class MenuHelper:
    """Помощник для создания стандартных меню"""

    @staticmethod
    def create_crud_menu(
        title: str,
        create_text: str = "➕ Создать",
        list_text: str = "📋 Список",
        create_callback: str = "create",
        list_callback: str = "list",
        back_text: str = "◀️ Назад",
        back_callback: str = "back",
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> tuple[str, InlineKeyboardMarkup]:
        """
        Создать стандартное CRUD меню

        Returns:
            tuple: (text, keyboard)
        """
        buttons = [
            [InlineKeyboardButton(text=create_text, callback_data=create_callback)],
            [InlineKeyboardButton(text=list_text, callback_data=list_callback)],
        ]

        if additional_buttons:
            buttons.extend(additional_buttons)

        buttons.append(
            [InlineKeyboardButton(text=back_text, callback_data=back_callback)]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return title, keyboard

    @staticmethod
    def create_edit_menu(
        item_name: str,
        edit_name_callback: str = "edit_name",
        edit_content_callback: str = "edit_content",
        delete_callback: str = "delete",
        back_callback: str = "back",
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """Создать меню редактирования элемента"""
        buttons = [
            [
                InlineKeyboardButton(
                    text="✏️ Название", callback_data=edit_name_callback
                ),
                InlineKeyboardButton(
                    text="📝 Содержимое", callback_data=edit_content_callback
                ),
            ],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data=delete_callback)],
        ]

        if additional_buttons:
            buttons.extend(additional_buttons)

        buttons.append(
            [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)]
        )

        return InlineKeyboardMarkup(inline_keyboard=buttons)


def parse_page_from_callback(callback_data: str, prefix: str = "page") -> int:
    """
    Извлечь номер страницы из callback_data

    Args:
        callback_data: Строка callback_data (например "page_2")
        prefix: Префикс перед номером страницы

    Returns:
        int: Номер страницы (по умолчанию 0)
    """
    try:
        if callback_data.startswith(f"{prefix}_"):
            return int(callback_data.split("_")[-1])
    except (ValueError, IndexError):
        pass
    return 0


def parse_id_from_callback(callback_data: str, prefix: str = "item") -> Optional[int]:
    """
    Извлечь ID из callback_data

    Args:
        callback_data: Строка callback_data (например "view_template_123")
        prefix: Префикс перед ID

    Returns:
        Optional[int]: ID элемента или None
    """
    try:
        parts = callback_data.split("_")
        if len(parts) >= 2:
            return int(parts[-1])
    except (ValueError, IndexError):
        pass
    return None
