"""
Интеграционные тесты для всей системы
"""

import pytest
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from config import Config
from database import Database
from menu_system import MenuManager, MenuMiddleware


@pytest.fixture
async def test_environment():
    """Фикстура для полного тестового окружения"""
    # Устанавливаем тестовые переменные окружения
    os.environ["BOT_TOKEN"] = "test:token"
    os.environ["ADMIN_IDS"] = "123456789,987654321"
    os.environ["DB_TYPE"] = "sqlite"
    os.environ["DB_PATH"] = ":memory:"

    config = Config()
    db = Database(config.database_url)
    await db.init_db()

    menu_manager = MenuManager(admin_ids=config.admin_ids)

    yield config, db, menu_manager

    # Очистка не требуется для in-memory БД


class TestFullWorkflow:
    """Тесты полного рабочего процесса"""

    @pytest.mark.asyncio
    async def test_complete_mailing_workflow(self, test_environment):
        """Тест полного цикла создания и отправки рассылки"""
        config, db, menu_manager = test_environment

        # 1. Создание шаблона
        template = await db.create_template(
            name="Прайс-лист Декабрь 2024",
            text="""
            <b>🎄 Новогодние цены!</b>
            
            ✅ Товар А - 1000₽
            ✅ Товар Б - 2000₽
            ✅ Товар В - 3000₽
            
            📞 Заказ: +7 (999) 123-45-67
            """,
            file_id="document_123",
            file_type="document",
        )

        assert template.id is not None

        # 2. Создание групп чатов
        vip_group = await db.create_chat_group(
            name="VIP клиенты",
            chat_ids=[-1001111111111, -1002222222222, -1003333333333],
        )

        regular_group = await db.create_chat_group(
            name="Обычные клиенты", chat_ids=[-1004444444444, -1005555555555]
        )

        # 3. Создание рассылки
        mailing = await db.create_mailing(
            template_id=template.id,
            group_ids=[vip_group.id, regular_group.id],
            total_chats=5,
        )

        assert mailing.status == "in_progress"

        # 4. Симуляция отправки
        sent = 4
        failed = 1

        # 5. Обновление статистики
        updated_mailing = await db.update_mailing_stats(
            mailing_id=mailing.id, sent_count=sent, failed_count=failed
        )

        assert updated_mailing.status == "completed"
        assert updated_mailing.sent_count == 4
        assert updated_mailing.failed_count == 1

        # 6. Проверка истории
        history = await db.get_mailings_history()
        assert len(history) > 0
        assert history[0].id == mailing.id

    @pytest.mark.asyncio
    async def test_menu_navigation_workflow(self, test_environment):
        """Тест навигации по меню"""
        config, db, menu_manager = test_environment

        admin_id = 123456789

        # Начальное меню
        text, keyboard = menu_manager.render_menu("main", admin_id)
        assert "Бот для рассылки прайс-листов" in text
        assert menu_manager.get_current_menu(admin_id) == "main"

        # Переход в шаблоны
        text, keyboard = menu_manager.render_menu("templates", admin_id)
        assert "Шаблоны сообщений" in text
        assert menu_manager.get_current_menu(admin_id) == "templates"

        # Переход в группы
        text, keyboard = menu_manager.render_menu("groups", admin_id)
        assert "Группы чатов" in text
        assert menu_manager.get_current_menu(admin_id) == "groups"

        # Возврат назад
        previous = menu_manager.go_back(admin_id)
        assert previous == "templates"

        # История навигации
        history = menu_manager.menu_history[admin_id]
        assert "main" in history
        assert "templates" in history

    @pytest.mark.asyncio
    async def test_access_control_workflow(self, test_environment):
        """Тест контроля доступа"""
        config, db, menu_manager = test_environment

        admin_id = 123456789
        regular_user_id = 111111111

        # Админ имеет доступ
        admin_menu = menu_manager.get_menu("main", admin_id)
        assert admin_menu is not None

        # Обычный пользователь не имеет доступа
        user_menu = menu_manager.get_menu("main", regular_user_id)
        assert user_menu is None

        # Проверка middleware
        middleware = MenuMiddleware(menu_manager)

        # Мок сообщения от админа
        admin_message = MagicMock(spec=types.Message)
        admin_message.from_user = MagicMock()
        admin_message.from_user.id = admin_id
        admin_message.chat = MagicMock()
        admin_message.chat.type = "private"
        admin_message.answer = AsyncMock()

        handler = AsyncMock()
        data = {}

        # Админ проходит
        await middleware(handler, admin_message, data)
        handler.assert_called_once()

        # Обычный пользователь блокируется
        user_message = MagicMock(spec=types.Message)
        user_message.from_user = MagicMock()
        user_message.from_user.id = regular_user_id
        user_message.chat = MagicMock()
        user_message.chat.type = "private"
        user_message.answer = AsyncMock()

        handler.reset_mock()
        await middleware(handler, user_message, data)
        handler.assert_not_called()
        user_message.answer.assert_called_once()


class TestBotIntegration:
    """Интеграционные тесты бота"""

    @pytest.mark.asyncio
    async def test_bot_initialization(self, test_environment):
        """Тест инициализации бота"""
        config, db, menu_manager = test_environment

        with patch("aiogram.Bot") as MockBot:
            mock_bot = MockBot.return_value
            mock_bot.get_me = AsyncMock(
                return_value=MagicMock(
                    id=123456789, username="test_bot", first_name="Test Bot"
                )
            )

            # Импортируем после патча
            from bot import bot, dp

            # Проверяем, что бот создан
            assert bot is not None
            assert dp is not None

    @pytest.mark.asyncio
    async def test_command_handlers(self, test_environment):
        """Тест обработчиков команд"""
        config, db, menu_manager = test_environment

        # Создаем мок сообщения
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456789  # Admin
        message.chat = MagicMock()
        message.chat.id = 123456789
        message.chat.type = "private"
        message.answer = AsyncMock()

        # Тест команды /start
        from bot import cmd_start

        await cmd_start(message, menu_manager)

        message.answer.assert_called_once()
        call_args = message.answer.call_args
        assert "Бот для рассылки прайс-листов" in call_args[0][0]

        # Тест команды /help
        message.answer.reset_mock()
        from bot import cmd_help

        await cmd_help(message, menu_manager)

        message.answer.assert_called_once()
        call_args = message.answer.call_args
        assert "Доступные команды" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_callback_query_handling(self, test_environment):
        """Тест обработки callback query"""
        config, db, menu_manager = test_environment

        # Создаем мок callback query
        callback = MagicMock(spec=types.CallbackQuery)
        callback.from_user = MagicMock()
        callback.from_user.id = 123456789  # Admin
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.message.edit_reply_markup = AsyncMock()
        callback.answer = AsyncMock()
        callback.data = "menu_templates"

        # Навигация в меню шаблонов
        success = await menu_manager.navigate_to("templates", callback)

        assert success is True
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()


class TestDatabaseIntegration:
    """Интеграционные тесты базы данных"""

    @pytest.mark.asyncio
    async def test_database_with_real_data(self, test_environment):
        """Тест БД с реалистичными данными"""
        config, db, menu_manager = test_environment

        # Создаем реалистичные шаблоны
        templates = []
        template_names = [
            "Прайс-лист основной",
            "Акция недели",
            "VIP предложение",
            "Новинки месяца",
            "Распродажа",
        ]

        for name in template_names:
            template = await db.create_template(
                name=name, text=f"<b>{name}</b>\n\nТекст шаблона с HTML разметкой"
            )
            templates.append(template)

        # Создаем реалистичные группы
        groups = []
        group_configs = [
            ("Москва - Опт", 5),
            ("Регионы - Розница", 10),
            ("VIP клиенты", 3),
            ("Новые клиенты", 7),
        ]

        for group_name, chat_count in group_configs:
            chat_ids = [
                -(1000000000000 + i + hash(group_name)) for i in range(chat_count)
            ]
            group = await db.create_chat_group(group_name, chat_ids)
            groups.append(group)

        # Создаем несколько рассылок
        for i in range(3):
            mailing = await db.create_mailing(
                template_id=templates[i].id,
                group_ids=[g.id for g in groups[: i + 2]],
                total_chats=sum(len(g.chat_ids) for g in groups[: i + 2]),
            )

            # Симулируем результаты
            sent = mailing.total_chats - i
            failed = i

            await db.update_mailing_stats(
                mailing.id, sent_count=sent, failed_count=failed
            )

        # Проверяем результаты
        all_templates = await db.get_templates()
        assert len(all_templates) == 5

        all_groups = await db.get_chat_groups()
        assert len(all_groups) == 4

        history = await db.get_mailings_history()
        assert len(history) == 3
        assert all(m.status == "completed" for m in history)


class TestErrorHandling:
    """Тесты обработки ошибок"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Тест ошибки подключения к БД"""
        with pytest.raises(Exception):
            db = Database("invalid://connection/string")
            await db.init_db()

    @pytest.mark.asyncio
    async def test_invalid_bot_token(self):
        """Тест неверного токена бота"""
        os.environ["BOT_TOKEN"] = "invalid:token:format"

        with patch("aiogram.Bot") as MockBot:
            mock_bot = MockBot.return_value
            mock_bot.get_me = AsyncMock(side_effect=Exception("Invalid token"))

            try:
                from bot import bot

                bot_info = await bot.get_me()
                assert False, "Should raise exception"
            except Exception as e:
                assert "Invalid token" in str(e)

    @pytest.mark.asyncio
    async def test_missing_admin_ids(self):
        """Тест отсутствия админских ID"""
        os.environ["BOT_TOKEN"] = "test:token"
        os.environ["ADMIN_IDS"] = ""

        with pytest.raises(ValueError, match="ADMIN_IDS"):
            Config()

    @pytest.mark.asyncio
    async def test_menu_error_handling(self, test_environment):
        """Тест обработки ошибок в меню"""
        config, db, menu_manager = test_environment

        # Попытка навигации к несуществующему меню
        callback = MagicMock(spec=types.CallbackQuery)
        callback.from_user = MagicMock()
        callback.from_user.id = 123456789
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()

        # Несуществующее меню
        text, keyboard = menu_manager.render_menu("nonexistent", 123456789)
        assert "не найдено" in text
        assert keyboard is None


class TestPerformance:
    """Тесты производительности"""

    @pytest.mark.asyncio
    async def test_large_scale_operation(self, test_environment):
        """Тест работы с большим объемом данных"""
        config, db, menu_manager = test_environment

        start_time = datetime.now()

        # Создаем много шаблонов
        templates = []
        for i in range(50):
            template = await db.create_template(
                name=f"Template {i}", text=f"Text {i}" * 100
            )
            templates.append(template)

        # Создаем много групп
        groups = []
        for i in range(20):
            group = await db.create_chat_group(
                name=f"Group {i}",
                chat_ids=[-(1000000000000 + j + i * 100) for j in range(50)],
            )
            groups.append(group)

        # Создаем рассылки
        for i in range(10):
            mailing = await db.create_mailing(
                template_id=templates[i].id,
                group_ids=[g.id for g in groups[:5]],
                total_chats=250,
            )

            await db.update_mailing_stats(mailing.id, sent_count=240, failed_count=10)

        elapsed = (datetime.now() - start_time).total_seconds()

        # Проверяем, что все операции выполнились быстро
        assert elapsed < 10  # Должно выполниться менее чем за 10 секунд

        # Проверяем результаты
        all_templates = await db.get_templates()
        assert len(all_templates) == 50

        all_groups = await db.get_chat_groups()
        assert len(all_groups) == 20

        history = await db.get_mailings_history()
        assert len(history) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
