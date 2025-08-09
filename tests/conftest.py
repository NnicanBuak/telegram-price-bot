"""
Общие фикстуры и конфигурация для тестов
Исправленная версия с фикстурами для корректной работы тестов
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

# Добавляем корень проекта и src в path для корректных импортов
project_root = Path(__file__).parent.parent.absolute()
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Минимальная настройка для тестов
os.environ["ENVIRONMENT"] = "testing"

# Если нет TEST_ переменных, создаем их для тестов
if not os.getenv("TEST_BOT_TOKEN") and not os.getenv("BOT_TOKEN"):
    os.environ["TEST_BOT_TOKEN"] = "1234567890:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPP-TEST"

if not os.getenv("TEST_ADMIN_IDS") and not os.getenv("ADMIN_IDS"):
    os.environ["TEST_ADMIN_IDS"] = "123456789,987654321"

# Импорты из src
from src.config import Config
from src.database import Database
from src.menu_system import MenuManager, Menu, MenuItem
from src.bot.menus import setup_bot_menus

# Конфигурация pytest
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Event loop для тестов"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_config():
    """Тестовая конфигурация"""
    config = Config()
    return config


@pytest.fixture(scope="function")
async def test_db():
    """Тестовая база данных"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db


@pytest.fixture(scope="function")
async def populated_db():
    """БД с тестовыми данными"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()

    # Создаем тестовые данные
    templates = []
    groups = []
    mailings = []

    # Шаблоны
    template_data = [
        ("Основной прайс", "📋 Стандартный прайс-лист"),
        ("VIP предложение", "⭐ Специальные условия для VIP"),
        ("Акция месяца", "🎉 Скидки до 50%!"),
    ]

    for name, text in template_data:
        template = await db.create_template(name=name, text=text)
        templates.append(template)

    # Группы чатов
    group_data = [
        ("Москва", 5),
        ("Регионы", 10),
        ("VIP клиенты", 3),
    ]

    for name, chat_count in group_data:
        chat_ids = [-(1000000000000 + i + hash(name)) for i in range(chat_count)]
        group = await db.create_chat_group(name=name, chat_ids=chat_ids)
        groups.append(group)

    # Рассылки
    for i in range(2):
        mailing = await db.create_mailing(
            template_id=templates[i].id,
            group_ids=[groups[i].id],
            total_chats=len(groups[i].chat_ids),
        )
        mailings.append(mailing)

    yield db, templates, groups, mailings


@pytest.fixture(scope="function")
def menu_manager():
    """Менеджер меню для тестов"""
    config = Config()
    return MenuManager(admin_ids=config.admin_ids)


@pytest.fixture(scope="function")
def mock_bot():
    """Мок Telegram бота"""
    from aiogram import Bot

    bot = MagicMock(spec=Bot)
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.send_document = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    bot.get_me = AsyncMock(
        return_value=MagicMock(
            id=123456789, is_bot=True, first_name="Test Bot", username="test_bot"
        )
    )
    return bot


@pytest.fixture(scope="function")
def mock_message():
    """Мок сообщения от администратора"""
    from aiogram import types

    config = Config()
    admin_id = config.admin_ids[0] if config.admin_ids else 123456789

    message = MagicMock(spec=types.Message)
    message.message_id = 1
    message.date = datetime.now()
    message.chat = MagicMock()
    message.chat.id = admin_id
    message.chat.type = "private"
    message.from_user = MagicMock()
    message.from_user.id = admin_id
    message.from_user.is_bot = False
    message.from_user.first_name = "Test"
    message.from_user.username = "test_user"
    message.text = "/start"
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    message.delete = AsyncMock()
    return message


@pytest.fixture(scope="function")
def mock_callback_query():
    """Мок callback query от администратора"""
    from aiogram import types

    config = Config()
    admin_id = config.admin_ids[0] if config.admin_ids else 123456789

    callback = MagicMock(spec=types.CallbackQuery)
    callback.id = "test_callback_id"
    callback.from_user = MagicMock()
    callback.from_user.id = admin_id
    callback.from_user.is_bot = False
    callback.from_user.first_name = "Test"
    callback.message = MagicMock()
    callback.message.message_id = 1
    callback.message.chat = MagicMock()
    callback.message.chat.id = admin_id
    callback.message.edit_text = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()
    callback.message.delete = AsyncMock()
    callback.data = "test_callback"
    callback.answer = AsyncMock()
    return callback


# Маркеры для pytest
def pytest_configure(config):
    """Регистрация маркеров"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "database: mark test as requiring database")


def pytest_collection_modifyitems(config, items):
    """Автоматическое добавление маркеров"""
    for item in items:
        # Автоматически добавляем маркер asyncio для async тестов
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # Добавляем маркеры на основе имени файла
        if "test_database" in str(item.fspath):
            item.add_marker(pytest.mark.database)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


# Вспомогательные функции для тестов
class TestHelpers:
    """Вспомогательные методы для тестов"""

    @staticmethod
    def assert_menu_contains(keyboard, expected_text):
        """Проверить, что клавиатура содержит кнопку с текстом"""
        for row in keyboard.inline_keyboard:
            for button in row:
                if expected_text in button.text:
                    return True
        return False

    @staticmethod
    async def create_test_mailing(db, template_id, group_ids, total_chats=10):
        """Создать тестовую рассылку"""
        mailing = await db.create_mailing(
            template_id=template_id, group_ids=group_ids, total_chats=total_chats
        )
        return mailing


# Экспортируем helpers
helpers = TestHelpers()
