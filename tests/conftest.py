"""
Общие фикстуры и конфигурация для тестов
Обновлено для новой структуры проекта
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

# Добавляем src в path для импортов
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Устанавливаем тестовые переменные окружения до импорта модулей
os.environ["BOT_TOKEN"] = "test:token:for:testing"
os.environ["ADMIN_IDS"] = "123456789,987654321"
os.environ["DB_PATH"] = ":memory:"
os.environ["LOG_LEVEL"] = "DEBUG"

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database import Database
from menu_system import MenuManager


# Конфигурация pytest
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_config():
    """Фикстура для тестовой конфигурации"""
    return Config()


@pytest.fixture(scope="function")
async def test_db():
    """Фикстура для тестовой базы данных"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db
    # Очистка происходит автоматически для in-memory БД


@pytest.fixture(scope="function")
async def populated_db():
    """Фикстура с предзаполненной базой данных"""
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
    """Фикстура для менеджера меню"""
    return MenuManager(admin_ids=[123456789, 987654321])


@pytest.fixture(scope="function")
def mock_bot():
    """Мок Telegram бота"""
    bot = MagicMock(spec=Bot)
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
def mock_dispatcher():
    """Мок диспетчера"""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    return dp


@pytest.fixture(scope="function")
def mock_message():
    """Мок сообщения от администратора"""
    message = MagicMock(spec=types.Message)
    message.message_id = 1
    message.date = datetime.now()
    message.chat = MagicMock()
    message.chat.id = 123456789
    message.chat.type = "private"
    message.from_user = MagicMock()
    message.from_user.id = 123456789
    message.from_user.is_bot = False
    message.from_user.first_name = "Test"
    message.from_user.username = "test_user"
    message.text = "/start"
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    message.delete = AsyncMock()
    return message


@pytest.fixture(scope="function")
def mock_message_user():
    """Мок сообщения от обычного пользователя"""
    message = MagicMock(spec=types.Message)
    message.message_id = 2
    message.date = datetime.now()
    message.chat = MagicMock()
    message.chat.id = 111111111
    message.chat.type = "private"
    message.from_user = MagicMock()
    message.from_user.id = 111111111  # Не админ
    message.from_user.is_bot = False
    message.from_user.first_name = "User"
    message.from_user.username = "regular_user"
    message.text = "/start"
    message.answer = AsyncMock()
    message.reply = AsyncMock()
    message.delete = AsyncMock()
    return message


@pytest.fixture(scope="function")
def mock_callback_query():
    """Мок callback query от администратора"""
    callback = MagicMock(spec=types.CallbackQuery)
    callback.id = "test_callback_id"
    callback.from_user = MagicMock()
    callback.from_user.id = 123456789
    callback.from_user.is_bot = False
    callback.from_user.first_name = "Test"
    callback.message = MagicMock()
    callback.message.message_id = 1
    callback.message.chat = MagicMock()
    callback.message.chat.id = 123456789
    callback.message.edit_text = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()
    callback.message.delete = AsyncMock()
    callback.data = "test_callback"
    callback.answer = AsyncMock()
    return callback


@pytest.fixture(scope="function")
def mock_state():
    """Мок FSM состояния"""
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey

    storage = MemoryStorage()
    state = FSMContext(
        storage=storage,
        key=StorageKey(bot_id=123456789, chat_id=123456789, user_id=123456789),
    )
    return state


@pytest.fixture(scope="function")
def sample_templates():
    """Примеры шаблонов для тестов"""
    return [
        {
            "name": "Прайс-лист основной",
            "text": "<b>📋 Основной прайс-лист</b>\n\n✅ Товар 1 - 1000₽\n✅ Товар 2 - 2000₽",
            "file_id": None,
            "file_type": None,
        },
        {
            "name": "Акция недели",
            "text": "<b>🎉 Акция недели!</b>\n\nСкидки до 50% на все товары!",
            "file_id": "document_123",
            "file_type": "document",
        },
        {
            "name": "VIP предложение",
            "text": "<b>⭐ VIP предложение</b>\n\nЭксклюзивные условия для постоянных клиентов",
            "file_id": "photo_456",
            "file_type": "photo",
        },
    ]


@pytest.fixture(scope="function")
def sample_chat_groups():
    """Примеры групп чатов для тестов"""
    return [
        {
            "name": "Москва - Опт",
            "chat_ids": [-1001111111111, -1002222222222, -1003333333333],
        },
        {"name": "Регионы - Розница", "chat_ids": [-1004444444444, -1005555555555]},
        {"name": "VIP клиенты", "chat_ids": [-1006666666666]},
    ]


@pytest.fixture(autouse=True)
def reset_singletons():
    """Сброс синглтонов между тестами"""
    # Если есть синглтоны, сбрасываем их здесь
    yield


@pytest.fixture
def capture_logs(caplog):
    """Фикстура для захвата логов"""
    import logging

    caplog.set_level(logging.DEBUG)
    return caplog


# Маркеры для параметризованных тестов
def pytest_configure(config):
    """Регистрация маркеров"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "database: mark test as requiring database")
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "api: mark test as requiring API")
    config.addinivalue_line("markers", "menu: mark test as menu system test")


# Хуки pytest
def pytest_collection_modifyitems(config, items):
    """Модификация собранных тестов"""
    for item in items:
        # Автоматически добавляем маркер asyncio для async тестов
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

        # Добавляем маркеры based на имени файла
        if "test_database" in str(item.fspath):
            item.add_marker(pytest.mark.database)
        elif "test_menu" in str(item.fspath):
            item.add_marker(pytest.mark.menu)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)


def pytest_runtest_setup(item):
    """Настройка перед запуском теста"""
    # Можно добавить логику настройки
    pass


def pytest_runtest_teardown(item):
    """Очистка после теста"""
    # Можно добавить логику очистки
    pass


# Вспомогательные функции для тестов
class TestHelpers:
    """Вспомогательные методы для тестов"""

    @staticmethod
    async def create_test_mailing(db, template_id, group_ids, total_chats=10):
        """Создать тестовую рассылку"""
        mailing = await db.create_mailing(
            template_id=template_id, group_ids=group_ids, total_chats=total_chats
        )
        return mailing

    @staticmethod
    def assert_menu_contains(keyboard, expected_text):
        """Проверить, что клавиатура содержит кнопку с текстом"""
        for row in keyboard.inline_keyboard:
            for button in row:
                if expected_text in button.text:
                    return True
        return False

    @staticmethod
    async def simulate_mailing(db, mailing_id, success_rate=0.9):
        """Симулировать отправку рассылки"""
        import random

        mailing = await db.get_mailing(mailing_id)
        total = mailing.total_chats
        sent = int(total * success_rate)
        failed = total - sent

        await db.update_mailing_stats(
            mailing_id=mailing_id, sent_count=sent, failed_count=failed
        )

        return sent, failed


# Экспортируем helpers
helpers = TestHelpers()
