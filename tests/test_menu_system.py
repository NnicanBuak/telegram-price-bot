"""
Тесты системы меню
Исправленная версия для полного API
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src_depricated.menu_system import MenuManager, Menu, MenuItem, MenuMiddleware


class TestMenuItem:
    """Тесты элемента меню"""

    def test_menu_item_creation(self):
        """Тест создания элемента меню"""
        item = MenuItem(
            id="test_item",
            text="Тестовый элемент",
            icon="🔧",
            callback_data="test_callback",
            admin_only=True,
            order=5,
        )

        assert item.id == "test_item"
        assert item.text == "Тестовый элемент"
        assert item.icon == "🔧"
        assert item.callback_data == "test_callback"
        assert item.admin_only is True
        assert item.visible is True  # Исправлено: по умолчанию True
        assert item.order == 5

    def test_menu_item_defaults(self):
        """Тест значений по умолчанию"""
        item = MenuItem(id="test", text="Test")

        assert item.icon == ""
        assert item.callback_data == ""
        assert item.url == ""
        assert item.admin_only is False
        assert item.visible is True  # Исправлено: по умолчанию True
        assert item.order == 0


class TestMenu:
    """Тесты меню"""

    def test_menu_creation(self):
        """Тест создания меню"""
        menu = Menu(
            id="test_menu",
            title="Тестовое меню",
            description="Описание",
            back_to="main",
            columns=2,
            admin_only=True,
        )

        assert menu.id == "test_menu"
        assert menu.title == "Тестовое меню"
        assert menu.description == "Описание"
        assert menu.back_to == "main"
        assert menu.columns == 2
        assert menu.admin_only is True
        assert len(menu.items) == 0

    def test_add_item(self):
        """Тест добавления элемента"""
        menu = Menu(id="test", title="Test")
        item = MenuItem(id="item1", text="Item 1", order=1)

        result = menu.add_item(item)

        assert result == menu  # Метод возвращает menu для chaining
        assert len(menu.items) == 1
        assert menu.items[0] == item
        assert item.parent == menu  # Исправлено: устанавливается parent

    def test_add_multiple_items_sorting(self):
        """Тест сортировки элементов по order"""
        menu = Menu(id="test", title="Test")

        item3 = MenuItem(id="item3", text="Item 3", order=3)
        item1 = MenuItem(id="item1", text="Item 1", order=1)
        item2 = MenuItem(id="item2", text="Item 2", order=2)

        menu.add_item(item3)
        menu.add_item(item1)
        menu.add_item(item2)

        assert menu.items[0] == item1
        assert menu.items[1] == item2
        assert menu.items[2] == item3

    def test_method_chaining(self):
        """Тест цепочки методов"""
        menu = Menu(id="test", title="Test")
        item1 = MenuItem(id="item1", text="Item 1")
        item2 = MenuItem(id="item2", text="Item 2")
