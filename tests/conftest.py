"""
Общие фикстуры и конфигурация для тестов
Исправленная версия с фикстурами для корректной работы тестов
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
from typing import List

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
from src_depricated.config import Config
from src_depricated.database import Database
from src_depricated.menu_system import MenuManager, Menu, MenuItem
from src_depricated.bot.menus import setup_bot_menus

# Конфигурация pytest
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function")
async def test_config():
    """Тестовая конфигурация"""
    config = Config()
    config.force_testing_mode()  # Принудительно включаем тестовый режим
    return config


@pytest.fixture(scope="function")
async def test_db():
    """Тестовая база данных"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db
    await db.close()


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
        ("Новинки", "🆕 Новые товары в каталоге"),
        ("Распродажа", "🔥 Распродажа остатков"),
    ]

    for name, text in template_data:
        template = await db.create_template(name=name, text=text)
        templates.append(template)

    # Группы чатов
    group_data = [
        ("VIP клиенты", [-1001234567890, -1001234567891, -1001234567892]),
        ("Обычные клиенты", [-1001111111111, -1001111111112]),
        ("Партнеры", [-1002222222222, -1002222222223, -1002222222224, -1002222222225]),
    ]

    for name, chat_ids in group_data:
        group = await db.create_chat_group(name=name, chat_ids=chat_ids)
        groups.append(group)

    # Рассылки
    mailing_data = [
        (templates[0].id, [groups[0].id], 3, "completed"),
        (templates[1].id, [groups[1].id, groups[2].id], 6, "pending"),
    ]

    for template_id, group_ids, total_chats, status in mailing_data:
        mailing = await db.create_mailing(
            template_id=template_id, group_ids=group_ids, total_chats=total_chats
        )
        # Обновляем статус
        await db.update_mailing_status(mailing.id, status)
        mailings.append(mailing)

    yield db, templates, groups, mailings
    await db.close()


@pytest.fixture(scope="function")
async def test_menu_manager(test_config):
    """Тестовый менеджер меню"""
    menu_manager = MenuManager(test_config.admin_ids)

    # Создаем основные меню для тестов
    main_menu = Menu(
        id="main",
        title="🤖 <b>Бот для рассылки прайс-листов</b>",
        description="Главное меню бота",
        back_button=False,
    )

    main_menu.add_item(
        MenuItem(
            id="templates",
            text="Шаблоны",
            icon="📋",
            callback_data="menu_templates",
        )
    )

    main_menu.add_item(
        MenuItem(
            id="groups",
            text="Группы",
            icon="👥",
            callback_data="menu_groups",
        )
    )

    menu_manager.register_menu(main_menu)

    return menu_manager


@pytest.fixture(scope="function")
async def bot_menus(test_menu_manager):
    """Фикстура для меню бота"""
    return setup_bot_menus(test_menu_manager)


@pytest.fixture(scope="function")
def mock_bot():
    """Мок для aiogram Bot"""
    bot = MagicMock()
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    bot.get_me = AsyncMock()
    bot.get_me.return_value = MagicMock(username="test_bot")
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    return bot


@pytest.fixture(scope="function")
def mock_message():
    """Мок для aiogram Message"""
    message = MagicMock()
    message.from_user.id = 123456789
    message.chat.id = 123456789
    message.chat.type = "private"
    message.text = "/start"
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message


@pytest.fixture(scope="function")
def mock_callback():
    """Мок для aiogram CallbackQuery"""
    callback = MagicMock()
    callback.from_user.id = 123456789
    callback.data = "test_callback"
    callback.message = mock_message()
    callback.answer = AsyncMock()
    callback.message.edit_text = AsyncMock()
    return callback


@pytest.fixture(scope="function")
def admin_user_id():
    """ID администратора для тестов"""
    return 123456789


@pytest.fixture(scope="function")
def regular_user_id():
    """ID обычного пользователя для тестов"""
    return 999999999


@pytest.fixture(scope="function", autouse=True)
def reset_environment():
    """Автоматически сбрасываем переменные окружения перед каждым тестом"""
    # Сохраняем оригинальные значения
    original_env = os.environ.copy()

    # Устанавливаем тестовые значения
    os.environ["ENVIRONMENT"] = "testing"

    yield

    # Восстанавливаем оригинальные значения
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def temp_env_vars():
    """Фикстура для временного изменения переменных окружения"""
    original_env = os.environ.copy()

    def _set_env(**kwargs):
        # Сначала очищаем релевантные переменные
        env_keys_to_clear = [
            "BOT_TOKEN",
            "TEST_BOT_TOKEN",
            "ADMIN_IDS",
            "TEST_ADMIN_IDS",
            "ENVIRONMENT",
            "DATABASE_URL",
            "MAILING_DELAY",
            "MAILING_BATCH_SIZE",
        ]
        for key in env_keys_to_clear:
            os.environ.pop(key, None)

        # Затем устанавливаем новые значения
        for key, value in kwargs.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = str(value)

    yield _set_env

    # Восстанавливаем оригинальные значения
    os.environ.clear()
    os.environ.update(original_env)


# ========== ДОПОЛНИТЕЛЬНЫЕ ФИКСТУРЫ ДЛЯ СПЕЦИФИЧНЫХ ТЕСТОВ ==========


@pytest.fixture(scope="function")
async def large_dataset_db():
    """БД с большим набором данных для тестов производительности"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()

    # Создаем большое количество шаблонов
    templates = []
    for i in range(100):
        template = await db.create_template(
            name=f"Шаблон {i+1}",
            text=f"Текст шаблона номер {i+1}\nС дополнительной информацией",
        )
        templates.append(template)

    # Создаем много групп
    groups = []
    for i in range(50):
        chat_ids = [-(1000000000000 + j + i * 100) for j in range(10)]
        group = await db.create_chat_group(name=f"Группа {i+1}", chat_ids=chat_ids)
        groups.append(group)

    yield db, templates, groups
    await db.close()


@pytest.fixture(scope="function")
def mock_telegram_api():
    """Мок для Telegram API с различными ответами"""
    api = MagicMock()

    # Успешные ответы
    api.send_message = AsyncMock(
        return_value={"ok": True, "result": {"message_id": 123}}
    )
    api.get_me = AsyncMock(
        return_value={
            "ok": True,
            "result": {
                "id": 123456789,
                "is_bot": True,
                "first_name": "Test Bot",
                "username": "test_bot",
            },
        }
    )

    # Методы для симуляции ошибок
    def simulate_error(error_code=400, description="Bad Request"):
        from aiogram.exceptions import TelegramAPIError

        api.send_message = AsyncMock(
            side_effect=TelegramAPIError(method="sendMessage", message=description)
        )

    def simulate_unauthorized():
        from aiogram.exceptions import TelegramUnauthorizedError

        api.get_me = AsyncMock(
            side_effect=TelegramUnauthorizedError(
                method="getMe", message="Unauthorized"
            )
        )

    api.simulate_error = simulate_error
    api.simulate_unauthorized = simulate_unauthorized

    return api


# ========== МАРКЕРЫ PYTEST ==========


def pytest_configure(config):
    """Конфигурация pytest с маркерами"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "menu: Menu system tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "api: API tests")


# ========== АВТОМАТИЧЕСКИЕ ФИКСТУРЫ ==========


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Автоматическая настройка логирования для тестов"""
    import logging

    # Устанавливаем уровень WARNING для тестов
    logging.getLogger().setLevel(logging.WARNING)

    # Отключаем логи aiogram во время тестов
    logging.getLogger("aiogram").setLevel(logging.ERROR)
    logging.getLogger("aiohttp").setLevel(logging.ERROR)


@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Автоматическая очистка после каждого теста"""
    yield

    # Очищаем кэши и состояния
    import gc

    gc.collect()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========


def create_test_template_data():
    """Создать тестовые данные для шаблонов"""
    return [
        {
            "name": "Основной прайс",
            "text": "📋 Стандартный прайс-лист\n\n<b>Актуальные цены:</b>\nТовар 1 - 100₽\nТовар 2 - 200₽",
        },
        {
            "name": "VIP предложение",
            "text": "⭐ <b>Специальные условия для VIP</b>\n\n🎁 Эксклюзивные скидки до 30%",
            "file_id": "BAADBAADrwADBREAAYag2DP_RNf0Ag",
            "file_type": "document",
        },
        {
            "name": "Акция месяца",
            "text": "🎉 <b>МЕГА СКИДКИ!</b>\n\n🔥 Скидки до 50% на все товары\n⏰ Только до конца месяца!",
        },
    ]


def create_test_group_data():
    """Создать тестовые данные для групп"""
    return [
        {
            "name": "VIP клиенты",
            "chat_ids": [-1001234567890, -1001234567891],
        },
        {
            "name": "Обычные клиенты",
            "chat_ids": [-1001111111111, -1001111111112, -1001111111113],
        },
        {
            "name": "Партнеры",
            "chat_ids": [-1002222222222],
        },
    ]


async def create_test_mailings(db: Database, templates: List, groups: List):
    """Создать тестовые рассылки"""
    mailings = []

    # Завершенная рассылка
    mailing1 = await db.create_mailing(
        template_id=templates[0].id, group_ids=[groups[0].id], total_chats=2
    )
    await db.update_mailing_status(
        mailing1.id, "completed", sent_count=2, failed_count=0
    )
    mailings.append(mailing1)

    # Активная рассылка
    mailing2 = await db.create_mailing(
        template_id=templates[1].id,
        group_ids=[groups[1].id, groups[2].id],
        total_chats=4,
    )
    await db.update_mailing_status(
        mailing2.id, "in_progress", sent_count=1, failed_count=0
    )
    mailings.append(mailing2)

    return mailings
