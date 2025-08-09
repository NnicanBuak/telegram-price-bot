"""
Тесты для Telegram Price Bot
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import tempfile
import os

# Настройка окружения для тестов
os.environ["BOT_TOKEN"] = "test:token"
os.environ["ADMIN_IDS"] = "123456789,987654321"
os.environ["DB_TYPE"] = "sqlite"
os.environ["DB_PATH"] = ":memory:"

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from config import Config
from database import Database, Template, ChatGroup, Mailing
from menu_system import MenuManager, MenuItem, Menu


class TestConfig:
    """Тесты конфигурации"""

    def test_config_loading(self):
        """Тест загрузки конфигурации"""
        config = Config()
        assert config.bot_token == "test:token"
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
        # Очистка не требуется для in-memory БД

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
        # Создаем несколько шаблонов
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

        updated = await db.update_template(
            template.id, name="Новый", text="Новый текст"
        )

        assert updated.name == "Новый"
        assert updated.text == "Новый текст"

    @pytest.mark.asyncio
    async def test_delete_template(self, db):
        """Тест удаления шаблона"""
        template = await db.create_template("Удаляемый", "Текст")
        template_id = template.id

        result = await db.delete_template(template_id)
        assert result is True

        deleted = await db.get_template(template_id)
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
        await db.create_chat_group("Группа 1", [111])
        await db.create_chat_group("Группа 2", [222, 333])
        await db.create_chat_group("Группа 3", [444, 555, 666])

        groups = await db.get_chat_groups()
        assert len(groups) == 3
        assert groups[0].name == "Группа 3"  # Сортировка по дате (desc)

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
        mailing = await db.create_mailing(template.id, [1], 10)

        updated = await db.update_mailing_stats(
            mailing_id=mailing.id, sent_count=8, failed_count=2
        )

        assert updated.sent_count == 8
        assert updated.failed_count == 2
        assert updated.status == "completed"
        assert updated.completed_at is not None


class TestMenuSystem:
    """Тесты системы меню"""

    @pytest.fixture
    def menu_manager(self):
        """Фикстура для менеджера меню"""
        return MenuManager(admin_ids=[123456789, 987654321])

    def test_menu_initialization(self, menu_manager):
        """Тест инициализации меню"""
        assert "main" in menu_manager.menus
        assert "templates" in menu_manager.menus
        assert "groups" in menu_manager.menus
        assert "settings" in menu_manager.menus

    def test_is_admin(self, menu_manager):
        """Тест проверки администратора"""
        assert menu_manager.is_admin(123456789) is True
        assert menu_manager.is_admin(987654321) is True
        assert menu_manager.is_admin(111111111) is False

    def test_get_menu_access(self, menu_manager):
        """Тест доступа к меню"""
        # Администратор получает меню
        menu = menu_manager.get_menu("main", 123456789)
        assert menu is not None
        assert menu.id == "main"

        # Не администратор не получает меню
        menu = menu_manager.get_menu("main", 111111111)
        assert menu is None

    def test_menu_navigation(self, menu_manager):
        """Тест навигации по меню"""
        user_id = 123456789

        # Устанавливаем главное меню
        menu_manager.set_current_menu(user_id, "main")
        assert menu_manager.get_current_menu(user_id) == "main"

        # Переходим в подменю
        menu_manager.set_current_menu(user_id, "templates")
        assert menu_manager.get_current_menu(user_id) == "templates"

        # История навигации
        assert len(menu_manager.menu_history[user_id]) == 2
        assert menu_manager.menu_history[user_id] == ["main", "templates"]

        # Возврат назад
        previous = menu_manager.go_back(user_id)
        assert previous == "main"
        assert menu_manager.get_current_menu(user_id) == "main"

    def test_build_keyboard(self, menu_manager):
        """Тест построения клавиатуры"""
        menu = menu_manager.menus["main"]
        keyboard = menu_manager.build_keyboard(menu, 123456789)

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0

        # Проверяем наличие кнопок
        buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_text.append(button.text)

        assert "📋 Шаблоны" in buttons_text
        assert "👥 Группы чатов" in buttons_text

    def test_add_dynamic_menu(self, menu_manager):
        """Тест добавления динамического меню"""
        items = [
            {"id": "item1", "text": "Пункт 1", "icon": "1️⃣", "callback_data": "cb1"},
            {"id": "item2", "text": "Пункт 2", "icon": "2️⃣", "callback_data": "cb2"},
        ]

        menu = menu_manager.add_dynamic_menu(
            menu_id="dynamic", title="Динамическое меню", items=items, back_to="main"
        )

        assert menu.id == "dynamic"
        assert len(menu.items) == 2
        assert menu.items[0].text == "Пункт 1"

    def test_menu_export_import(self, menu_manager):
        """Тест экспорта и импорта конфигурации меню"""
        # Экспортируем конфигурацию
        config_json = menu_manager.export_menu_config()
        assert config_json is not None
        assert "main" in config_json

        # Создаем новый менеджер и импортируем конфигурацию
        new_manager = MenuManager(admin_ids=[123456789])
        new_manager.menus = {}  # Очищаем стандартные меню
        new_manager.import_menu_config(config_json)

        assert "main" in new_manager.menus
        assert "templates" in new_manager.menus
        assert len(new_manager.menus["main"].items) > 0


class TestBotHandlers:
    """Тесты обработчиков бота"""

    @pytest.fixture
    def mock_message(self):
        """Мок сообщения"""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456789
        message.chat = MagicMock()
        message.chat.id = 123456789
        message.chat.type = "private"
        message.answer = AsyncMock()
        message.text = "/start"
        return message

    @pytest.fixture
    def mock_callback(self):
        """Мок callback query"""
        callback = MagicMock(spec=types.CallbackQuery)
        callback.from_user = MagicMock()
        callback.from_user.id = 123456789
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.message.edit_reply_markup = AsyncMock()
        callback.answer = AsyncMock()
        callback.data = "test_callback"
        return callback

    @pytest.mark.asyncio
    async def test_start_command_admin(self, mock_message):
        """Тест команды /start для администратора"""
        menu_manager = MenuManager(admin_ids=[123456789])

        # Симулируем вызов команды /start
        from src.main import cmd_start

        await cmd_start(mock_message, menu_manager)

        # Проверяем, что сообщение отправлено
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args

        assert "Бот для рассылки прайс-листов" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "HTML"
        assert call_args[1]["reply_markup"] is not None

    @pytest.mark.asyncio
    async def test_menu_middleware_access_denied(self):
        """Тест middleware для неавторизованного пользователя"""
        from menu_system import MenuMiddleware

        menu_manager = MenuManager(admin_ids=[123456789])
        middleware = MenuMiddleware(menu_manager)

        # Создаем мок сообщения от неавторизованного пользователя
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 999999999  # Не админ
        message.chat = MagicMock()
        message.chat.type = "private"
        message.answer = AsyncMock()

        # Мок handler
        handler = AsyncMock()
        data = {}

        # Вызываем middleware
        await middleware(handler, message, data)

        # Проверяем, что отправлено сообщение об отказе в доступе
        message.answer.assert_called_once()
        assert "нет доступа" in message.answer.call_args[0][0]

        # Handler не должен быть вызван
        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_menu_navigation_callback(self, mock_callback):
        """Тест навигации по меню через callback"""
        menu_manager = MenuManager(admin_ids=[123456789])

        # Тестируем переход в меню шаблонов
        mock_callback.data = "menu_templates"

        success = await menu_manager.navigate_to("templates", mock_callback)
        assert success is True

        # Проверяем, что сообщение обновлено
        mock_callback.message.edit_text.assert_called_once()
        call_args = mock_callback.message.edit_text.call_args

        assert "Шаблоны сообщений" in call_args[0][0]
        assert call_args[1]["parse_mode"] == "HTML"
        assert call_args[1]["reply_markup"] is not None


class TestIntegration:
    """Интеграционные тесты"""

    @pytest.fixture
    async def test_bot(self):
        """Фикстура для тестового бота"""
        config = Config()
        test_bot = Bot(token=config.bot_token)
        yield test_bot
        await test_bot.session.close()

    @pytest.fixture
    async def test_db(self):
        """Фикстура для тестовой БД"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()
        yield db

    @pytest.mark.asyncio
    async def test_full_mailing_flow(self, test_db):
        """Тест полного цикла создания и отправки рассылки"""
        # 1. Создаем шаблон
        template = await test_db.create_template(
            name="Прайс-лист",
            text="<b>Новые цены:</b>\n\nТовар 1 - 1000₽\nТовар 2 - 2000₽",
        )

        # 2. Создаем группу чатов
        group = await test_db.create_chat_group(
            name="Клиенты", chat_ids=[-1001234567890, -1009876543210, -1005555555555]
        )

        # 3. Создаем рассылку
        mailing = await test_db.create_mailing(
            template_id=template.id, group_ids=[group.id], total_chats=3
        )

        assert mailing.status == "in_progress"

        # 4. Симулируем отправку
        sent = 2
        failed = 1

        # 5. Обновляем статистику
        updated = await test_db.update_mailing_stats(
            mailing_id=mailing.id, sent_count=sent, failed_count=failed
        )

        assert updated.status == "completed"
        assert updated.sent_count == 2
        assert updated.failed_count == 1

        # 6. Проверяем историю
        history = await test_db.get_mailings_history(limit=10)
        assert len(history) > 0
        assert history[0].id == mailing.id

    @pytest.mark.asyncio
    async def test_menu_with_database_data(self, test_db):
        """Тест меню с данными из БД"""
        # Создаем тестовые данные
        templates = []
        for i in range(3):
            t = await test_db.create_template(f"Шаблон {i+1}", f"Текст {i+1}")
            templates.append(t)

        groups = []
        for i in range(2):
            g = await test_db.create_chat_group(f"Группа {i+1}", [111 * (i + 1)])
            groups.append(g)

        # Создаем динамическое меню с шаблонами
        menu_manager = MenuManager(admin_ids=[123456789])

        template_items = [
            {
                "id": f"template_{t.id}",
                "text": t.name,
                "icon": "📄",
                "callback_data": f"select_template_{t.id}",
            }
            for t in templates
        ]

        menu = menu_manager.add_dynamic_menu(
            menu_id="template_list",
            title="📋 Выберите шаблон:",
            items=template_items,
            back_to="templates",
        )

        assert len(menu.items) == 3
        assert menu.items[0].text == "Шаблон 1"


@pytest.mark.asyncio
async def test_bot_lifecycle():
    """Тест жизненного цикла бота"""
    from src.main import bot, dp, db

    # Инициализация БД
    await db.init_db()

    # Проверяем, что бот создан
    assert bot is not None
    assert dp is not None

    # Получаем информацию о боте
    try:
        bot_info = await bot.get_me()
        assert bot_info is not None
    except Exception:
        # В тестовом окружении может не быть реального токена
        pass

    # Закрываем сессию
    await bot.session.close()


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v", "--tb=short"])
