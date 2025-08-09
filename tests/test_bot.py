"""
Тесты для Telegram Price Bot
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import os

# Настройка окружения для тестов
os.environ["BOT_TOKEN"] = "1234567890:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPP-FAKE"
os.environ["ADMIN_IDS"] = "123456789,987654321"
os.environ["DB_PATH"] = ":memory:"

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from database import Database, Template, ChatGroup, Mailing
from menu_system import MenuManager, MenuItem, Menu
from bot.menus import BotMenus, setup_bot_menus


class TestConfig:
    """Тесты конфигурации"""

    def test_config_loading(self):
        """Тест загрузки конфигурации"""
        config = Config()
        assert config.bot_token == "1234567890:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPP-FAKE"
        assert 123456789 in config.admin_ids
        assert 987654321 in config.admin_ids
        assert "sqlite" in config.database_url

    def test_config_validation(self):
        """Тест валидации конфигурации"""
        with patch.dict(os.environ, {"BOT_TOKEN": ""}):
            with pytest.raises(ValueError, match="BOT_TOKEN"):
                Config()

        with patch.dict(os.environ, {"ADMIN_IDS": ""}):
            with pytest.raises(ValueError, match="ADMIN_IDS"):
                Config()


class TestDatabase:
    """Тесты базы данных"""

    @pytest.fixture
    async def db(self):
        """Фикстура для базы данных"""
        database = Database("sqlite+aiosqlite:///:memory:")
        await database.init_db()
        yield database

    @pytest.mark.asyncio
    async def test_create_template(self, db):
        """Тест создания шаблона"""
        template = await db.create_template(
            name="Тестовый шаблон", text="Тестовое сообщение"
        )

        assert template.id is not None
        assert template.name == "Тестовый шаблон"
        assert template.text == "Тестовое сообщение"
        assert template.file_id is None

    @pytest.mark.asyncio
    async def test_create_template_with_file(self, db):
        """Тест создания шаблона с файлом"""
        template = await db.create_template(
            name="Шаблон с файлом",
            text="Сообщение",
            file_id="file_123",
            file_type="document",
        )

        assert template.file_id == "file_123"
        assert template.file_type == "document"

    @pytest.mark.asyncio
    async def test_get_templates(self, db):
        """Тест получения списка шаблонов"""
        await db.create_template("Шаблон 1", "Текст 1")
        await db.create_template("Шаблон 2", "Текст 2")
        await db.create_template("Шаблон 3", "Текст 3")

        templates = await db.get_templates()
        assert len(templates) == 3
        assert templates[0].name == "Шаблон 3"  # Сортировка по дате (desc)

    @pytest.mark.asyncio
    async def test_create_chat_group(self, db):
        """Тест создания группы чатов"""
        group = await db.create_chat_group(
            name="Тестовая группа", chat_ids=[-1001234567890, -1009876543210]
        )

        assert group.id is not None
        assert group.name == "Тестовая группа"
        assert len(group.chat_ids) == 2
        assert -1001234567890 in group.chat_ids

    @pytest.mark.asyncio
    async def test_create_mailing(self, db):
        """Тест создания рассылки"""
        template = await db.create_template("Шаблон", "Текст")
        group = await db.create_chat_group("Группа", [111, 222])

        mailing = await db.create_mailing(
            template_id=template.id, group_ids=[group.id], total_chats=2
        )

        assert mailing.id is not None
        assert mailing.template_id == template.id
        assert mailing.total_chats == 2
        assert mailing.status == "in_progress"


class TestMenuSystem:
    """Тесты абстрактной системы меню"""

    @pytest.fixture
    def menu_manager(self):
        """Фикстура для менеджера меню"""
        return MenuManager(admin_ids=[123456789, 987654321])

    def test_menu_manager_initialization(self, menu_manager):
        """Тест инициализации менеджера меню"""
        assert 123456789 in menu_manager.admin_ids
        assert 987654321 in menu_manager.admin_ids
        assert isinstance(menu_manager.menus, dict)

    def test_is_admin(self, menu_manager):
        """Тест проверки администратора"""
        assert menu_manager.is_admin(123456789) is True
        assert menu_manager.is_admin(987654321) is True
        assert menu_manager.is_admin(111111111) is False

    def test_register_menu(self, menu_manager):
        """Тест регистрации меню"""
        menu = Menu(id="test", title="Test Menu")
        menu_manager.register_menu(menu)

        assert "test" in menu_manager.menus
        assert menu_manager.menus["test"] == menu

    def test_menu_navigation(self, menu_manager):
        """Тест навигации по меню"""
        user_id = 123456789

        menu_manager.set_current_menu(user_id, "main")
        assert menu_manager.get_current_menu(user_id) == "main"

        menu_manager.set_current_menu(user_id, "templates")
        assert menu_manager.get_current_menu(user_id) == "templates"

        previous = menu_manager.go_back(user_id)
        assert previous == "main"
        assert menu_manager.get_current_menu(user_id) == "main"

    def test_build_keyboard(self, menu_manager):
        """Тест построения клавиатуры"""
        menu = Menu(id="test", title="Test")
        menu.add_item(MenuItem(id="1", text="Button 1", callback_data="cb1"))
        menu.add_item(MenuItem(id="2", text="Button 2", callback_data="cb2"))

        keyboard = menu_manager.build_keyboard(menu, 123456789)

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 2


class TestBotMenus:
    """Тесты конкретных меню бота"""

    @pytest.fixture
    def menu_manager(self):
        return MenuManager(admin_ids=[123456789])

    @pytest.fixture
    def bot_menus(self, menu_manager):
        return setup_bot_menus(menu_manager)

    @pytest.fixture
    async def db_with_data(self):
        """БД с тестовыми данными"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # Создаем тестовые шаблоны
        await db.create_template("Шаблон 1", "Текст 1")
        await db.create_template("Шаблон 2", "Текст 2")

        # Создаем тестовые группы
        await db.create_chat_group("Группа 1", [111, 222])
        await db.create_chat_group("Группа 2", [333, 444])

        yield db

    def test_bot_menus_initialization(self, bot_menus, menu_manager):
        """Тест инициализации меню бота"""
        # Проверяем, что созданы основные меню
        assert "main" in menu_manager.menus
        assert "templates" in menu_manager.menus
        assert "groups" in menu_manager.menus
        assert "mailing" in menu_manager.menus
        assert "history" in menu_manager.menus
        assert "settings" in menu_manager.menus

    def test_main_menu_structure(self, menu_manager):
        """Тест структуры главного меню"""
        main_menu = menu_manager.menus["main"]

        assert main_menu.title == "🤖 <b>Telegram Price Bot</b>"
        assert not main_menu.back_button
        assert (
            len(main_menu.items) == 5
        )  # templates, groups, mailing, history, settings

    @pytest.mark.asyncio
    async def test_templates_list_menu_creation(self, bot_menus, db_with_data):
        """Тест создания меню списка шаблонов"""
        menu = await bot_menus.create_templates_list_menu(db_with_data)

        assert menu.id == "templates_list"
        assert "templates_list" in bot_menus.menu_manager.menus
        assert len(menu.items) == 3  # 2 шаблона + кнопка "Создать новый"

    @pytest.mark.asyncio
    async def test_groups_list_menu_creation(self, bot_menus, db_with_data):
        """Тест создания меню списка групп"""
        menu = await bot_menus.create_groups_list_menu(db_with_data)

        assert menu.id == "groups_list"
        assert "groups_list" in bot_menus.menu_manager.menus
        assert len(menu.items) == 3  # 2 группы + кнопка "Создать новую"

    @pytest.mark.asyncio
    async def test_mailing_template_selection_menu(self, bot_menus, db_with_data):
        """Тест создания меню выбора шаблона для рассылки"""
        menu = await bot_menus.create_mailing_template_selection_menu(db_with_data)

        assert menu.id == "mailing_template_selection"
        assert len(menu.items) == 2  # 2 шаблона

    @pytest.mark.asyncio
    async def test_empty_templates_menu(self, bot_menus):
        """Тест меню шаблонов когда нет шаблонов"""
        empty_db = Database("sqlite+aiosqlite:///:memory:")
        await empty_db.init_db()

        menu = await bot_menus.create_templates_list_menu(empty_db)

        # Должна быть кнопка "Нет шаблонов" + "Создать новый"
        assert len(menu.items) == 2


class TestIntegration:
    """Интеграционные тесты"""

    @pytest.mark.asyncio
    async def test_full_menu_workflow(self):
        """Тест полного рабочего процесса с меню"""
        # Инициализация
        menu_manager = MenuManager(admin_ids=[123456789])
        bot_menus = setup_bot_menus(menu_manager)

        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # Создаем данные
        template = await db.create_template("Тест", "Текст")
        group = await db.create_chat_group("Тест группа", [111])

        # Тестируем создание динамических меню
        templates_menu = await bot_menus.create_templates_list_menu(db)
        groups_menu = await bot_menus.create_groups_list_menu(db)

        assert templates_menu is not None
        assert groups_menu is not None
        assert len(templates_menu.items) == 2  # 1 шаблон + создать новый
        assert len(groups_menu.items) == 2  # 1 группа + создать новую

    @pytest.mark.asyncio
    async def test_menu_rendering(self):
        """Тест рендеринга меню"""
        menu_manager = MenuManager(admin_ids=[123456789])
        setup_bot_menus(menu_manager)

        user_id = 123456789
        text, keyboard = menu_manager.render_menu("main", user_id)

        assert "Telegram Price Bot" in text
        assert keyboard is not None
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0

    @pytest.mark.asyncio
    async def test_access_control(self):
        """Тест контроля доступа"""
        menu_manager = MenuManager(admin_ids=[123456789])
        setup_bot_menus(menu_manager)

        # Админ получает меню
        admin_text, admin_keyboard = menu_manager.render_menu("main", 123456789)
        assert "Telegram Price Bot" in admin_text
        assert admin_keyboard is not None

        # Не админ не получает меню
        user_text, user_keyboard = menu_manager.render_menu("main", 999999999)
        assert "не найдено" in user_text
        assert user_keyboard is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
