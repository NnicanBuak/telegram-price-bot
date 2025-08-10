from typing import List, Any, Optional, Callable, Tuple
from math import ceil


class Paginator:
    """Класс для работы с пагинацией"""

    def __init__(
        self, items: List[Any], items_per_page: int = 5, current_page: int = 0
    ):
        self.items = items
        self.items_per_page = max(1, items_per_page)
        self._current_page = 0
        self.current_page = current_page

    @property
    def current_page(self) -> int:
        """Текущая страница"""
        return self._current_page

    @current_page.setter
    def current_page(self, page: int):
        """Установить текущую страницу с валидацией"""
        self._current_page = max(0, min(page, self.total_pages - 1))

    @property
    def total_items(self) -> int:
        """Общее количество элементов"""
        return len(self.items)

    @property
    def total_pages(self) -> int:
        """Общее количество страниц"""
        if self.total_items == 0:
            return 1
        return ceil(self.total_items / self.items_per_page)

    @property
    def start_index(self) -> int:
        """Начальный индекс для текущей страницы"""
        return self.current_page * self.items_per_page

    @property
    def end_index(self) -> int:
        """Конечный индекс для текущей страницы"""
        return min(self.start_index + self.items_per_page, self.total_items)

    @property
    def current_items(self) -> List[Any]:
        """Элементы текущей страницы"""
        return self.items[self.start_index : self.end_index]

    @property
    def has_previous(self) -> bool:
        """Есть ли предыдущая страница"""
        return self.current_page > 0

    @property
    def has_next(self) -> bool:
        """Есть ли следующая страница"""
        return self.current_page < self.total_pages - 1

    @property
    def page_info(self) -> str:
        """Информация о странице в формате "1/5" """
        return f"{self.current_page + 1}/{self.total_pages}"

    def next_page(self) -> bool:
        """Перейти на следующую страницу"""
        if self.has_next:
            self.current_page += 1
            return True
        return False

    def previous_page(self) -> bool:
        """Перейти на предыдущую страницу"""
        if self.has_previous:
            self.current_page -= 1
            return True
        return False

    def go_to_page(self, page: int) -> bool:
        """Перейти на указанную страницу"""
        if 0 <= page < self.total_pages:
            self.current_page = page
            return True
        return False

    def get_page_slice(self, page: int) -> Tuple[int, int]:
        """Получить границы среза для указанной страницы"""
        start = page * self.items_per_page
        end = min(start + self.items_per_page, self.total_items)
        return start, end

    def get_page_items(self, page: int) -> List[Any]:
        """Получить элементы для указанной страницы"""
        if 0 <= page < self.total_pages:
            start, end = self.get_page_slice(page)
            return self.items[start:end]
        return []


class PaginationConfig:
    """Конфигурация для пагинации"""

    def __init__(
        self,
        items_per_page: int = 5,
        show_navigation: bool = True,
        show_page_info: bool = True,
        navigation_icons: dict = None,
        page_callback_prefix: str = "page",
    ):
        self.items_per_page = items_per_page
        self.show_navigation = show_navigation
        self.show_page_info = show_page_info
        self.page_callback_prefix = page_callback_prefix

        # Иконки навигации по умолчанию
        default_icons = {
            "previous": "◀️",
            "next": "▶️",
            "first": "⏮️",
            "last": "⏭️",
            "page_separator": "/",
        }
        self.navigation_icons = navigation_icons or default_icons


class PaginationHelper:
    """Помощник для создания пагинации"""

    @staticmethod
    def create_paginator(
        items: List[Any], page: int = 0, config: Optional[PaginationConfig] = None
    ) -> Paginator:
        """Создать пагинатор с конфигурацией"""
        if config is None:
            config = PaginationConfig()

        return Paginator(
            items=items, items_per_page=config.items_per_page, current_page=page
        )

    @staticmethod
    def parse_page_from_callback(callback_data: str, prefix: str = "page") -> int:
        """Извлечь номер страницы из callback_data"""
        try:
            if callback_data.startswith(f"{prefix}_"):
                return int(callback_data.split("_")[-1])
        except (ValueError, IndexError):
            pass
        return 0

    @staticmethod
    def create_page_callback(page: int, prefix: str = "page") -> str:
        """Создать callback_data для страницы"""
        return f"{prefix}_{page}"

    @staticmethod
    def get_navigation_callbacks(paginator: Paginator, prefix: str = "page") -> dict:
        """Получить callback_data для навигации"""
        return {
            "previous": (
                f"{prefix}_{paginator.current_page - 1}"
                if paginator.has_previous
                else None
            ),
            "next": (
                f"{prefix}_{paginator.current_page + 1}" if paginator.has_next else None
            ),
            "first": f"{prefix}_0" if paginator.current_page > 0 else None,
            "last": (
                f"{prefix}_{paginator.total_pages - 1}"
                if paginator.current_page < paginator.total_pages - 1
                else None
            ),
        }


def paginate_items(
    items: List[Any], page: int = 0, items_per_page: int = 5
) -> Tuple[List[Any], Paginator]:
    """Удобная функция для пагинации списка"""
    paginator = Paginator(items, items_per_page, page)
    return paginator.current_items, paginator


def create_pagination_info(
    current_page: int, total_pages: int, total_items: int = 0, items_per_page: int = 5
) -> str:
    """Создать информационную строку о пагинации"""
    if total_items > 0:
        start_item = current_page * items_per_page + 1
        end_item = min((current_page + 1) * items_per_page, total_items)
        return f"Показано {start_item}-{end_item} из {total_items} (стр. {current_page + 1}/{total_pages})"
    else:
        return f"Страница {current_page + 1} из {total_pages}"
