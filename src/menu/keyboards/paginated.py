from typing import List, Optional, Callable, Any, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .base import BaseKeyboard
from ..paginator import Paginator, PaginationConfig, PaginationHelper


class PaginatedKeyboard(BaseKeyboard):
    """Класс для создания пагинированных клавиатур"""

    @staticmethod
    def create_from_paginator(
        paginator: Paginator,
        item_to_button_func: Callable[[Any], InlineKeyboardButton],
        config: Optional[PaginationConfig] = None,
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """Создать пагинированную клавиатуру из пагинатора"""
        if config is None:
            config = PaginationConfig()

        buttons = []

        # Кнопки элементов текущей страницы
        for item in paginator.current_items:
            button = item_to_button_func(item)
            buttons.append([button])

        # Добавляем дополнительные кнопки (если есть)
        if additional_buttons:
            buttons.extend(additional_buttons)

        # Навигация по страницам
        if config.show_navigation and paginator.total_pages > 1:
            nav_buttons = PaginatedKeyboard._create_navigation_buttons(
                paginator, config
            )
            if nav_buttons:
                buttons.append(nav_buttons)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_from_items(
        items: List[Any],
        page: int = 0,
        item_to_button_func: Optional[Callable[[Any], InlineKeyboardButton]] = None,
        config: Optional[PaginationConfig] = None,
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """Создать пагинированную клавиатуру из списка элементов"""
        if config is None:
            config = PaginationConfig()

        paginator = Paginator(items, config.items_per_page, page)

        # Функция по умолчанию для создания кнопок
        if item_to_button_func is None:

            def default_item_to_button(item):
                text = getattr(item, "name", getattr(item, "title", str(item)))
                callback_data = getattr(
                    item, "callback_data", f"item_{getattr(item, 'id', '')}"
                )
                return InlineKeyboardButton(text=text, callback_data=callback_data)

            item_to_button_func = default_item_to_button

        return PaginatedKeyboard.create_from_paginator(
            paginator, item_to_button_func, config, additional_buttons
        )

    @staticmethod
    def _create_navigation_buttons(
        paginator: Paginator, config: PaginationConfig
    ) -> List[InlineKeyboardButton]:
        """Создать кнопки навигации"""
        nav_buttons = []
        icons = config.navigation_icons

        # Кнопка "Назад"
        if paginator.has_previous:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=icons["previous"],
                    callback_data=f"{config.page_callback_prefix}_{paginator.current_page - 1}",
                )
            )

        # Информация о странице
        if config.show_page_info:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=paginator.page_info, callback_data="noop"  # Неактивная кнопка
                )
            )

        # Кнопка "Вперед"
        if paginator.has_next:
            nav_buttons.append(
                InlineKeyboardButton(
                    text=icons["next"],
                    callback_data=f"{config.page_callback_prefix}_{paginator.current_page + 1}",
                )
            )

        return nav_buttons


class ListKeyboard:
    """Клавиатуры для списков с различными функциями"""

    @staticmethod
    def create_simple_list(
        items: List[Any],
        item_text_func: Optional[Callable[[Any], str]] = None,
        item_callback_func: Optional[Callable[[Any], str]] = None,
        item_icon: str = "📄",
        columns: int = 1,
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """Создать простой список без пагинации"""

        def create_button(item):
            if item_text_func:
                text = item_text_func(item)
            else:
                text = getattr(item, "name", getattr(item, "title", str(item)))

            if item_callback_func:
                callback_data = item_callback_func(item)
            else:
                callback_data = getattr(
                    item, "callback_data", f"item_{getattr(item, 'id', '')}"
                )

            button_text = f"{item_icon} {text}".strip() if item_icon else text
            return InlineKeyboardButton(text=button_text, callback_data=callback_data)

        button_rows = BaseKeyboard.create_columns_layout(items, columns, create_button)

        # Добавляем дополнительные кнопки
        if additional_buttons:
            button_rows.extend(additional_buttons)

        return InlineKeyboardMarkup(inline_keyboard=button_rows)

    @staticmethod
    def create_selection_list(
        items: List[Dict[str, Any]],
        selected_items: List[Any],
        toggle_callback_prefix: str = "toggle",
        item_name_key: str = "name",
        item_id_key: str = "id",
    ) -> InlineKeyboardMarkup:
        """Создать список с возможностью выбора нескольких элементов"""
        buttons = []

        for item in items:
            item_id = item.get(item_id_key)
            item_name = item.get(item_name_key, str(item_id))
            is_selected = item_id in selected_items

            # Иконка в зависимости от выбора
            icon = "✅" if is_selected else "☐"
            button_text = f"{icon} {item_name}"

            button = InlineKeyboardButton(
                text=button_text, callback_data=f"{toggle_callback_prefix}_{item_id}"
            )
            buttons.append([button])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_numbered_selection(
        items: List[str],
        callback_prefix: str = "select",
        start_number: int = 1,
        max_columns: int = 3,
    ) -> InlineKeyboardMarkup:
        """Создать пронумерованный список для выбора"""
        numbered_items = []

        for i, item in enumerate(items):
            numbered_items.append(
                {
                    "text": f"{start_number + i}",
                    "callback_data": f"{callback_prefix}_{i}",
                    "title": item,
                }
            )

        # Определяем количество колонок
        columns = min(len(numbered_items), max_columns)

        def create_button(item_data):
            return InlineKeyboardButton(
                text=item_data["text"], callback_data=item_data["callback_data"]
            )

        button_rows = BaseKeyboard.create_columns_layout(
            numbered_items, columns, create_button
        )

        return InlineKeyboardMarkup(inline_keyboard=button_rows)


class SearchKeyboard:
    """Клавиатуры для поиска и фильтрации"""

    @staticmethod
    def create_filter_buttons(
        filters: Dict[str, Dict[str, Any]],
        active_filters: List[str],
        filter_callback_prefix: str = "filter",
    ) -> InlineKeyboardMarkup:
        """Создать кнопки фильтров"""
        buttons = []

        for filter_id, filter_info in filters.items():
            text = filter_info.get("text", filter_id)
            icon = filter_info.get("icon", "")
            is_active = filter_id in active_filters

            # Префикс для активного фильтра
            status_icon = "✅" if is_active else "☐"
            button_text = f"{status_icon} {icon} {text}".strip()

            button = InlineKeyboardButton(
                text=button_text, callback_data=f"{filter_callback_prefix}_{filter_id}"
            )
            buttons.append([button])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_search_results(
        results: List[Any],
        page: int = 0,
        items_per_page: int = 5,
        item_formatter: Optional[Callable[[Any], Dict[str, str]]] = None,
        no_results_text: str = "Ничего не найдено",
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру с результатами поиска"""
        if not results:
            return InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=no_results_text, callback_data="noop")]
                ]
            )

        def default_formatter(item):
            return {
                "text": getattr(item, "name", str(item)),
                "callback_data": f"view_{getattr(item, 'id', '')}",
            }

        if item_formatter is None:
            item_formatter = default_formatter

        def create_button(item):
            formatted = item_formatter(item)
            return InlineKeyboardButton(
                text=formatted["text"], callback_data=formatted["callback_data"]
            )

        config = PaginationConfig(items_per_page=items_per_page)
        return PaginatedKeyboard.create_from_items(results, page, create_button, config)


def create_paginated_list(
    items: List[Any],
    page: int = 0,
    items_per_page: int = 5,
    item_icon: str = "📄",
    page_callback_prefix: str = "page",
) -> InlineKeyboardMarkup:
    """Удобная функция для создания пагинированного списка"""
    config = PaginationConfig(
        items_per_page=items_per_page, page_callback_prefix=page_callback_prefix
    )

    def item_to_button(item):
        text = getattr(item, "name", getattr(item, "title", str(item)))
        callback_data = getattr(
            item, "callback_data", f"view_{getattr(item, 'id', '')}"
        )
        button_text = f"{item_icon} {text}".strip() if item_icon else text
        return InlineKeyboardButton(text=button_text, callback_data=callback_data)

    return PaginatedKeyboard.create_from_items(items, page, item_to_button, config)
