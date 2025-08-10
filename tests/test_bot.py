"""
Тесты для Telegram Price Bot
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Настройка окружения для тестов
os.environ["DB_PATH"] = ":memory:"

# Исправление пути для импорта
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Импорты из модулей
from src.config import Config
from src.database import Database, Template, ChatGroup, Mailing
from src.menu_system import MenuManager, MenuItem, Menu
from src.bot.menus import BotMenus, setup_bot_menus
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class TestConfig:
    """Тесты конфигурации"""

    def test_config_loading(self):
        """Тест загрузки конфигурации"""
        config = Config()
        assert config.bot_token is not None
        assert len(config.admin_ids) > 0
        assert "sqlite" in config.database_url

    def test_config_validation(self):
        """Тест валидации конфигурации"""
        with patch.dict(os.environ, {"TEST_BOT_TOKEN": "", "BOT_TOKEN": ""}):
            with pytest.raises(ValueError, match="BOT_TOKEN"):
                Config()

        with patch.dict(os.environ, {"TEST_ADMIN_IDS": "", "ADMIN_IDS": ""}):
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
    async def test_update_template(self, db):
        """Тест обновления шаблона"""
        template = await db.create_template("Старый", "Старый текст")

        # Небольшая задержка для различия updated_at
        await asyncio.sleep(0.01)

        updated = await db.update_template(
            template.id, name="Новый", text="Новый текст"
        )

        assert updated is not None
        assert updated.name == "Новый"
        assert updated.text == "Новый текст"

    @pytest.mark.asyncio
    async def test_delete_template(self, db):
        """Тест удаления шаблона"""
        template = await db.create_template("Удаляемый", "Текст")

        result = await db.delete_template(template.id)
        assert result is True

        deleted = await db.get_template(template.id)
        assert deleted is None

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
    async def test_get_chat_groups(self, db):
        """Тест получения списка групп"""
        await db.create_chat_group("Группа 1", [111, 222])
        await db.create_chat_group("Группа 2", [333, 444])

        groups = await db.get_chat_groups()

        assert len(groups) == 2
        assert groups[0].name == "Группа 2"  # Сортировка по дате (desc)

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

    @pytest.mark.asyncio
    async def test_update_mailing_stats(self, db):
        """Тест обновления статистики рассылки"""
        template = await db.create_template("Шаблон", "Текст")
        group = await db.create_chat_group("Группа", [111, 222])

        mailing = await db.create_mailing(
            template_id=template.id, group_ids=[group.id], total_chats=2
        )

        updated = await db.update_mailing_stats(
            mailing_id=mailing.id, sent_count=1, failed_count=1
        )

        assert updated is not None
        assert updated.sent_count == 1
        assert updated.failed_count == 1
        assert updated.status == "completed"
        assert updated.completed_at is not None


class TestMenuSystem:
    """Тесты абстрактной системы меню"""

    @pytest.fixture
    def menu_manager(self):
        """Фикстура для менеджера меню"""
        return MenuManager(admin_ids=[123456789, 987654321])

    def test_menu_initialization(self, menu_manager):
        """Тест инициализации менеджера меню"""
        assert 123456789 in menu_manager.admin_ids
        assert 987654321 in menu_manager.admin_ids
        assert isinstance(menu_manager.menus, dict)

    def test_is_admin(self, menu_manager):
        """Тест проверки администратора"""
        assert menu_manager.is_admin(123456789) is True
        assert menu_manager.is_admin(987654321) is True
        assert menu_manager.is_admin(111111111) is False

    def test_get_menu_access(self, menu_manager):
        """Тест доступа к меню"""
        # Создаем тестовое меню
        menu = Menu(id="test", title="Test Menu")
        menu_manager.register_menu(menu)

        # Админ должен получить меню
        admin_menu = menu_manager.get_menu("test", 123456789)
        assert admin_menu is not None

        # Не админ не должен получить меню
        user_menu = menu_manager.get_menu("test", 111111111)
        assert user_menu is None

    def test_menu_navigation(self, menu_manager):
        """Тест навигации по меню"""
        user_id = 123456789

        # Создаем меню для теста
        main_menu = Menu(id="main", title="Main Menu")
        submenu = Menu(id="submenu", title="Submenu")
        menu_manager.register_menu(main_menu)
        menu_manager.register_menu(submenu)

        # Переходим в главное меню
        menu_manager.set_current_menu(user_id, "main")
        assert menu_manager.get_current_menu(user_id) == "main"

        # Переходим в подменю
        menu_manager.set_current_menu(user_id, "submenu")
        assert menu_manager.get_current_menu(user_id) == "submenu"

        # Возвращаемся назад
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


@pytest.mark.integration
class TestMenuMiddleware:
    """Тесты middleware для меню"""

    @pytest.mark.asyncio
    async def test_middleware_passes_admin(self, menu_manager):
        """Тест пропуска админа через middleware"""
        from src.menu_system import MenuMiddleware

        middleware = MenuMiddleware(menu_manager)
        handler = AsyncMock()

        # Создаем мок сообщения от админа
        message = MagicMock()
        message.from_user = MagicMock()
        message.from_user.id = 123456789  # Админ
        message.chat = MagicMock()
        message.chat.type = "private"

        data = {}

        # Вызываем middleware
        await middleware(handler, message, data)

        # Проверяем, что handler был вызван
        handler.assert_called_once()

        # Проверяем, что menu_manager добавлен в data
        assert "menu_manager" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
