"""
Детальные тесты для системы меню
"""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from menu_system import Menu, MenuItem, MenuManager, MenuMiddleware


class TestMenuItem:
    """Тесты для элемента меню"""
    
    def test_menu_item_creation(self):
        """Тест создания элемента меню"""
        item = MenuItem(
            id="test_item",
            text="Test Item",
            callback_data="test_callback",
            icon="🔧",
            admin_only=True,
            visible=True
        )
        
        assert item.id == "test_item"
        assert item.text == "Test Item"
        assert item.callback_data == "test_callback"
        assert item.icon == "🔧"
        assert item.admin_only is True
        assert item.visible is True
    
    def test_menu_item_defaults(self):
        """Тест значений по умолчанию"""
        item = MenuItem(
            id="test",
            text="Test",
            callback_data="test"
        )
        
        assert item.icon == ""
        assert item.admin_only is True
        assert item.visible is True
        assert item.action is None
        assert item.submenu is None
        assert item.parent is None
        assert item.row is None


class TestMenu:
    """Тесты для меню"""
    
    def test_menu_creation(self):
        """Тест создания меню"""
        menu = Menu(
            id="test_menu",
            title="Test Menu",
            description="This is a test menu",
            columns=2
        )
        
        assert menu.id == "test_menu"
        assert menu.title == "Test Menu"
        assert menu.description == "This is a test menu"
        assert menu.columns == 2
        assert menu.back_button is True
        assert len(menu.items) == 0
    
    def test_add_item(self):
        """Тест добавления элемента в меню"""
        menu = Menu(id="test", title="Test")
        item = MenuItem(id="item1", text="Item 1", callback_data="cb1")
        
        menu.add_item(item)
        
        assert len(menu.items) == 1
        assert menu.items[0] == item
        assert item.parent == "test"
    
    def test_remove_item(self):
        """Тест удаления элемента из меню"""
        menu = Menu(id="test", title="Test")
        item1 = MenuItem(id="item1", text="Item 1", callback_data="cb1")
        item2 = MenuItem(id="item2", text="Item 2", callback_data="cb2")
        
        menu.add_item(item1)
        menu.add_item(item2)
        assert len(menu.items) == 2
        
        menu.remove_item("item1")
        assert len(menu.items) == 1
        assert menu.items[0].id == "item2"
    
    def test_method_chaining(self):
        """Тест цепочки методов"""
        menu = Menu(id="test", title="Test")
        result = menu.add_item(
            MenuItem(id="item1", text="Item 1", callback_data="cb1")
        ).add_item(
            MenuItem(id="item2", text="Item 2", callback_data="cb2")
        )
        
        assert result == menu
        assert len(menu.items) == 2


class TestMenuManager:
    """Тесты для менеджера меню"""
    
    @pytest.fixture
    def manager(self):
        """Фикстура для менеджера меню"""
        return MenuManager(admin_ids=[123, 456, 789])
    
    def test_initialization(self, manager):
        """Тест инициализации менеджера"""
        assert 123 in manager.admin_ids
        assert 456 in manager.admin_ids
        assert 789 in manager.admin_ids
        
        # Проверка стандартных меню
        assert "main" in manager.menus
        assert "templates" in manager.menus
        assert "groups" in manager.menus
        assert "settings" in manager.menus
    
    def test_is_admin(self, manager):
        """Тест проверки администратора"""
        assert manager.is_admin(123) is True
        assert manager.is_admin(456) is True
        assert manager.is_admin(789) is True
        assert manager.is_admin(999) is False
    
    def test_register_menu(self, manager):
        """Тест регистрации меню"""
        custom_menu = Menu(id="custom", title="Custom Menu")
        manager.register_menu(custom_menu)
        
        assert "custom" in manager.menus
        assert manager.menus["custom"] == custom_menu
    
    def test_get_menu_access_control(self, manager):
        """Тест контроля доступа к меню"""
        # Админ получает меню
        menu = manager.get_menu("main", 123)
        assert menu is not None
        assert menu.id == "main"
        
        # Не админ не получает меню
        menu = manager.get_menu("main", 999)
        assert menu is None
    
    def test_current_menu_tracking(self, manager):
        """Тест отслеживания текущего меню"""
        user_id = 123
        
        # Изначально нет текущего меню
        assert manager.get_current_menu(user_id) is None
        
        # Устанавливаем меню
        manager.set_current_menu(user_id, "main")
        assert manager.get_current_menu(user_id) == "main"
        
        # Меняем меню
        manager.set_current_menu(user_id, "templates")
        assert manager.get_current_menu(user_id) == "templates"
    
    def test_menu_history(self, manager):
        """Тест истории навигации"""
        user_id = 123
        
        # Навигация по меню
        manager.set_current_menu(user_id, "main")
        manager.set_current_menu(user_id, "templates")
        manager.set_current_menu(user_id, "new_template")
        
        # Проверка истории
        history = manager.menu_history[user_id]
        assert len(history) == 3
        assert history == ["main", "templates", "new_template"]
        
        # Возврат назад
        previous = manager.go_back(user_id)
        assert previous == "templates"
        assert manager.get_current_menu(user_id) == "templates"
        
        # История обновилась
        assert len(manager.menu_history[user_id]) == 2
    
    def test_history_limit(self, manager):
        """Тест ограничения истории"""
        user_id = 123
        
        # Добавляем больше 10 элементов
        for i in range(15):
            manager.set_current_menu(user_id, f"menu_{i}")
        
        # История ограничена 10 элементами
        history = manager.menu_history[user_id]
        assert len(history) == 10
        assert history[0] == "menu_5"
        assert history[-1] == "menu_14"
    
    def test_build_keyboard_simple(self, manager):
        """Тест построения простой клавиатуры"""
        menu = Menu(id="test", title="Test")
        menu.add_item(MenuItem(id="1", text="Button 1", callback_data="cb1"))
        menu.add_item(MenuItem(id="2", text="Button 2", callback_data="cb2"))
        
        keyboard = manager.build_keyboard(menu, 123)
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 2  # 2 ряда (по одной кнопке)
        assert keyboard.inline_keyboard[0][0].text == "Button 1"
        assert keyboard.inline_keyboard[1][0].text == "Button 2"
    
    def test_build_keyboard_with_icons(self, manager):
        """Тест клавиатуры с иконками"""
        menu = Menu(id="test", title="Test")
        menu.add_item(MenuItem(
            id="1", 
            text="Settings", 
            icon="⚙️",
            callback_data="settings"
        ))
        
        keyboard = manager.build_keyboard(menu, 123)
        button_text = keyboard.inline_keyboard[0][0].text
        
        assert "⚙️" in button_text
        assert "Settings" in button_text
    
    def test_build_keyboard_columns(self, manager):
        """Тест клавиатуры с несколькими колонками"""
        menu = Menu(id="test", title="Test", columns=2)
        menu.add_item(MenuItem(id="1", text="Btn1", callback_data="cb1"))
        menu.add_item(MenuItem(id="2", text="Btn2", callback_data="cb2"))
        menu.add_item(MenuItem(id="3", text="Btn3", callback_data="cb3"))
        
        keyboard = manager.build_keyboard(menu, 123)
        
        # Первый ряд должен содержать 2 кнопки
        assert len(keyboard.inline_keyboard[0]) == 2
        # Второй ряд - 1 кнопка
        assert len(keyboard.inline_keyboard[1]) == 1
    
    def test_build_keyboard_with_back_button(self, manager):
        """Тест клавиатуры с кнопкой назад"""
        menu = Menu(
            id="test", 
            title="Test",
            back_button=True,
            back_to="main"
        )
        menu.add_item(MenuItem(id="1", text="Item", callback_data="cb"))
        
        keyboard = manager.build_keyboard(menu, 123)
        
        # Последняя кнопка должна быть "Назад"
        last_button = keyboard.inline_keyboard[-1][0]
        assert "Назад" in last_button.text
        assert last_button.callback_data == "menu_main"
    
    def test_visibility_control(self, manager):
        """Тест контроля видимости элементов"""
        menu = Menu(id="test", title="Test")
        menu.add_item(MenuItem(
            id="1", 
            text="Visible", 
            callback_data="cb1",
            visible=True
        ))
        menu.add_item(MenuItem(
            id="2", 
            text="Hidden", 
            callback_data="cb2",
            visible=False
        ))
        
        keyboard = manager.build_keyboard(menu, 123)
        
        # Только видимая кнопка должна быть в клавиатуре
        assert len(keyboard.inline_keyboard) == 1
        assert keyboard.inline_keyboard[0][0].text == "Visible"
    
    def test_admin_only_items(self, manager):
        """Тест элементов только для админов"""
        menu = Menu(id="test", title="Test")
        menu.add_item(MenuItem(
            id="1",
            text="Admin Only",
            callback_data="cb1",
            admin_only=True
        ))
        menu.add_item(MenuItem(
            id="2",
            text="Public",
            callback_data="cb2",
            admin_only=False
        ))
        
        # Клавиатура для админа
        admin_keyboard = manager.build_keyboard(menu, 123)
        assert len(admin_keyboard.inline_keyboard) == 2
        
        # Клавиатура для обычного пользователя
        user_keyboard = manager.build_keyboard(menu, 999)
        assert len(user_keyboard.inline_keyboard) == 1
        assert user_keyboard.inline_keyboard[0][0].text == "Public"
    
    def test_render_menu(self, manager):
        """Тест рендеринга меню"""
        text, keyboard = manager.render_menu("main", 123)
        
        assert "Бот для рассылки прайс-листов" in text
        assert keyboard is not None
        assert isinstance(keyboard, InlineKeyboardMarkup)
        
        # Проверка, что меню установлено как текущее
        assert manager.get_current_menu(123) == "main"
    
    def test_render_nonexistent_menu(self, manager):
        """Тест рендеринга несуществующего меню"""
        text, keyboard = manager.render_menu("nonexistent", 123)
        
        assert "не найдено" in text
        assert keyboard is None
    
    @pytest.mark.asyncio
    async def test_navigate_to(self, manager):
        """Тест навигации к меню"""
        # Мок callback query
        callback = MagicMock(spec=types.CallbackQuery)
        callback.from_user = MagicMock()
        callback.from_user.id = 123
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        # Навигация к существующему меню
        success = await manager.navigate_to("templates", callback)
        
        assert success is True
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()
        
        # Проверка аргументов edit_text
        call_args = callback.message.edit_text.call_args
        assert "Шаблоны сообщений" in call_args[0][0]
        assert call_args[1]['parse_mode'] == 'HTML'
        assert call_args[1]['reply_markup'] is not None
    
    @pytest.mark.asyncio
    async def test_navigate_to_access_denied(self, manager):
        """Тест навигации без доступа"""
        callback = MagicMock(spec=types.CallbackQuery)
        callback.from_user = MagicMock()
        callback.from_user.id = 999  # Не админ
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        success = await manager.navigate_to("templates", callback)
        
        assert success is False
        callback.message.edit_text.assert_not_called()
        callback.answer.assert_called_with(
            "Нет доступа к этому меню", 
            show_alert=True
        )
    
    def test_add_dynamic_menu(self, manager):
        """Тест добавления динамического меню"""
        items = [
            {'id': 'item1', 'text': 'Dynamic 1', 'icon': '1️⃣', 'callback_data': 'dyn1'},
            {'id': 'item2', 'text': 'Dynamic 2', 'icon': '2️⃣', 'callback_data': 'dyn2'},
            {'id': 'item3', 'text': 'Dynamic 3', 'icon': '3️⃣', 'callback_data': 'dyn3'},
        ]
        
        menu = manager.add_dynamic_menu(
            menu_id="dynamic_test",
            title="Dynamic Menu",
            items=items,
            back_to="main"
        )
        
        assert menu.id == "dynamic_test"
        assert menu.title == "Dynamic Menu"
        assert len(menu.items) == 3
        assert menu.items[0].text == "Dynamic 1"
        assert menu.items[1].icon == "2️⃣"
        assert menu.back_to == "main"
        
        # Меню должно быть зарегистрировано
        assert "dynamic_test" in manager.menus
    
    def test_export_menu_config(self, manager):
        """Тест экспорта конфигурации меню"""
        config_json = manager.export_menu_config()
        config = json.loads(config_json)
        
        assert "main" in config
        assert "templates" in config
        assert "groups" in config
        assert "settings" in config
        
        main_config = config["main"]
        assert main_config['title'] == manager.menus["main"].title
        assert len(main_config['items']) > 0
        
        # Проверка структуры элемента
        first_item = main_config['items'][0]
        assert 'id' in first_item
        assert 'text' in first_item
        assert 'callback_data' in first_item
    
    def test_import_menu_config(self):
        """Тест импорта конфигурации меню"""
        # Создаем конфигурацию
        config = {
            "imported_menu": {
                "title": "Imported Menu",
                "description": "This is imported",
                "back_to": "main",
                "columns": 2,
                "items": [
                    {
                        "id": "imp1",
                        "text": "Imported Item 1",
                        "icon": "📥",
                        "callback_data": "imported_1",
                        "admin_only": True,
                        "visible": True
                    },
                    {
                        "id": "imp2",
                        "text": "Imported Item 2",
                        "icon": "📤",
                        "callback_data": "imported_2",
                        "admin_only": False,
                        "visible": True
                    }
                ]
            }
        }
        
        config_json = json.dumps(config)
        
        # Импортируем в новый менеджер
        manager = MenuManager(admin_ids=[123])
        manager.import_menu_config(config_json)
        
        assert "imported_menu" in manager.menus
        imported = manager.menus["imported_menu"]
        assert imported.title == "Imported Menu"
        assert imported.columns == 2
        assert len(imported.items) == 2
        assert imported.items[0].icon == "📥"
    
    def test_register_callback(self, manager):
        """Тест регистрации обработчика callback"""
        def handler():
            return "handled"
        
        manager.register_callback("test_callback", handler)
        
        assert "test_callback" in manager._callbacks
        assert manager.get_callback_handler("test_callback") == handler
        assert manager.get_callback_handler("nonexistent") is None


class TestMenuMiddleware:
    """Тесты для middleware меню"""
    
    @pytest.fixture
    def middleware(self):
        """Фикстура для middleware"""
        manager = MenuManager(admin_ids=[123, 456])
        return MenuMiddleware(manager)
    
    @pytest.mark.asyncio
    async def test_middleware_adds_manager(self, middleware):
        """Тест добавления менеджера в data"""
        handler = AsyncMock()
        event = MagicMock()
        event.chat = MagicMock()
        event.chat.type = 'group'  # Не личное сообщение
        data = {}
        
        await middleware(handler, event, data)
        
        assert 'menu_manager' in data
        assert isinstance(data['menu_manager'], MenuManager)
        handler.assert_called_once_with(event, data)
    
    @pytest.mark.asyncio
    async def test_middleware_blocks_non_admin(self, middleware):
        """Тест блокировки не-админов в личных сообщениях"""
        handler = AsyncMock()
        
        # Создаем мок личного сообщения от не-админа
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 999  # Не админ
        message.chat = MagicMock()
        message.chat.type = 'private'
        message.answer = AsyncMock()
        
        data = {}
        
        await middleware(handler, message, data)
        
        # Handler не должен быть вызван
        handler.assert_not_called()
        
        # Должно быть отправлено сообщение об отказе
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "нет доступа" in call_args
    
    @pytest.mark.asyncio
    async def test_middleware_allows_admin(self, middleware):
        """Тест пропуска админов"""
        handler = AsyncMock()
        
        # Создаем мок личного сообщения от админа
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123  # Админ
        message.chat = MagicMock()
        message.chat.type = 'private'
        message.answer = AsyncMock()
        
        data = {}
        
        await middleware(handler, message, data)
        
        # Handler должен быть вызван
        handler.assert_called_once_with(message, data)
        
        # Сообщение об отказе не должно быть отправлено
        message.answer.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_middleware_allows_group_messages(self, middleware):
        """Тест пропуска сообщений из групп"""
        handler = AsyncMock()
        
        # Создаем мок сообщения из группы
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 999  # Не админ
        message.chat = MagicMock()
        message.chat.type = 'group'  # Групповой чат
        message.answer = AsyncMock()
        
        data = {}
        
        await middleware(handler, message, data)
        
        # Handler должен быть вызван (группы не блокируются)
        handler.assert_called_once_with(message, data)
        
        # Сообщение об отказе не должно быть отправлено
        message.answer.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])