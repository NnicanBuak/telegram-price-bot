"""
Тесты для проверки работоспособности рассылки
Включает unit, integration и e2e тесты для всего функционала рассылки
"""

import os
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramUnauthorizedError, TelegramBadRequest
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импорты из src
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.absolute()
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src_depricated.database import Database
from src_depricated.bot.handlers.mailing_handlers import (
    execute_mailing_task,
    estimate_mailing_time,
)


class TestMailingFunctions:
    """Unit тесты функций рассылки"""

    def test_estimate_mailing_time_short(self):
        """Тест оценки времени для коротких рассылок"""
        assert estimate_mailing_time(10) == "~1 сек"
        assert estimate_mailing_time(30) == "~4 сек"
        assert estimate_mailing_time(50) == "~7 сек"

    def test_estimate_mailing_time_medium(self):
        """Тест оценки времени для средних рассылок"""
        assert estimate_mailing_time(500) == "~1 мин"
        assert estimate_mailing_time(1000) == "~2 мин"
        assert estimate_mailing_time(3000) == "~7 мин"

    def test_estimate_mailing_time_long(self):
        """Тест оценки времени для длинных рассылок"""
        assert estimate_mailing_time(30000) == "~1ч 15м"
        assert estimate_mailing_time(60000) == "~2ч 30м"

    def test_estimate_mailing_time_edge_cases(self):
        """Тест граничных случаев"""
        assert estimate_mailing_time(0) == "~0 сек"
        assert estimate_mailing_time(1) == "~0 сек"
        assert estimate_mailing_time(400) == "~1 мин"  # Граница минут


class TestMailingDatabase:
    """Тесты БД для рассылок"""

    @pytest.mark.asyncio
    async def test_create_mailing_basic(self):
        """Базовый тест создания рассылки в БД"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # Создаем тестовые данные
        template = await db.create_template("Тест шаблон", "Тестовое сообщение")
        group = await db.create_chat_group("Тест группа", [-1001, -1002])

        # Создаем рассылку
        mailing = await db.create_mailing(
            template_id=template.id, group_ids=[group.id], total_chats=2
        )

        assert mailing is not None
        assert mailing.template_id == template.id
        assert mailing.total_chats == 2
        assert mailing.status == "pending"
        assert mailing.sent_count == 0
        assert mailing.failed_count == 0
        assert mailing.created_at is not None

    @pytest.mark.asyncio
    async def test_create_mailing_multiple_groups(self):
        """Тест создания рассылки с несколькими группами"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # Создаем данные
        template = await db.create_template("Тест", "Сообщение")
        group1 = await db.create_chat_group("Группа 1", [-1001, -1002])
        group2 = await db.create_chat_group("Группа 2", [-1003, -1004, -1005])

        total_chats = len(group1.chat_ids) + len(group2.chat_ids)

        mailing = await db.create_mailing(
            template_id=template.id,
            group_ids=[group1.id, group2.id],
            total_chats=total_chats,
        )

        assert mailing.total_chats == 5
        # Проверяем что group_ids сохранились правильно
        # (это зависит от реализации БД)

    @pytest.mark.asyncio
    async def test_update_mailing_stats(self):
        """Тест обновления статистики рассылки"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        template = await db.create_template("Тест", "Сообщение")
        group = await db.create_chat_group("Группа", [-1001, -1002])
        mailing = await db.create_mailing(template.id, [group.id], 2)

        # Обновляем статистику
        await db.update_mailing_stats(mailing.id, sent_count=2, failed_count=0)

        # Проверяем обновление
        updated_mailing = await db.get_mailing(mailing.id)
        assert updated_mailing.sent_count == 2
        assert updated_mailing.failed_count == 0
        assert updated_mailing.status == "completed"

    @pytest.mark.asyncio
    async def test_update_mailing_stats_partial_success(self):
        """Тест обновления статистики с частичным успехом"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        template = await db.create_template("Тест", "Сообщение")
        group = await db.create_chat_group("Группа", [-1001, -1002, -1003])
        mailing = await db.create_mailing(template.id, [group.id], 3)

        # Частичный успех
        await db.update_mailing_stats(mailing.id, sent_count=2, failed_count=1)

        updated_mailing = await db.get_mailing(mailing.id)
        assert updated_mailing.sent_count == 2
        assert updated_mailing.failed_count == 1
        assert updated_mailing.status == "completed"

    @pytest.mark.asyncio
    async def test_get_mailings_history(self):
        """Тест получения истории рассылок"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        template = await db.create_template("Тест", "Сообщение")
        group = await db.create_chat_group("Группа", [-1001])

        # Создаем несколько рассылок
        mailings = []
        for i in range(5):
            mailing = await db.create_mailing(template.id, [group.id], 1)
            mailings.append(mailing)
            await asyncio.sleep(0.01)  # Небольшая задержка для разных timestamp

        # Получаем историю
        history = await db.get_mailings_history(limit=3)

        assert len(history) == 3
        # Проверяем сортировку по дате (новые первыми)
        assert history[0].id > history[1].id > history[2].id

    @pytest.mark.asyncio
    async def test_get_mailing_by_id(self):
        """Тест получения рассылки по ID"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        template = await db.create_template("Тест", "Сообщение")
        group = await db.create_chat_group("Группа", [-1001])
        mailing = await db.create_mailing(template.id, [group.id], 1)

        # Получаем по ID
        retrieved_mailing = await db.get_mailing(mailing.id)

        assert retrieved_mailing is not None
        assert retrieved_mailing.id == mailing.id
        assert retrieved_mailing.template_id == template.id
        assert retrieved_mailing.total_chats == 1

        # Проверяем несуществующий ID
        nonexistent = await db.get_mailing(999999)
        assert nonexistent is None


class TestMailingExecution:
    """Тесты выполнения рассылки"""

    @pytest.mark.asyncio
    async def test_execute_mailing_task_success(self):
        """Тест успешного выполнения рассылки"""
        # Мокаем бота
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock()

        # Мокаем БД
        mock_db = AsyncMock()
        mock_template = MagicMock()
        mock_template.text = "Тестовое сообщение"
        mock_template.file_path = None
        mock_db.get_template.return_value = mock_template
        mock_db.update_mailing_stats = AsyncMock()

        # Создаем тестовые группы
        mock_group = MagicMock()
        mock_group.chat_ids = [-1001, -1002, -1003]
        groups = [mock_group]

        # Выполняем рассылку
        await execute_mailing_task(
            bot=mock_bot,
            admin_chat_id=123456789,
            mailing_id=1,
            template_id=1,
            groups=groups,
            database=mock_db,
        )

        # Проверяем вызовы
        assert mock_bot.send_message.call_count >= 3  # 3 сообщения + прогресс
        mock_db.update_mailing_stats.assert_called_once()

        # Проверяем параметры последнего вызова
        call_args = mock_db.update_mailing_stats.call_args[0]
        assert call_args[0] == 1  # mailing_id
        assert call_args[1] == 3  # sent_count
        assert call_args[2] == 0  # failed_count

    @pytest.mark.asyncio
    async def test_execute_mailing_task_with_file(self):
        """Тест выполнения рассылки с файлом"""
        # Создаем тестовый файл
        test_file_path = "test_file.txt"
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("Тестовый контент файла")

        try:
            mock_bot = AsyncMock()
            mock_bot.send_document = AsyncMock()

            mock_db = AsyncMock()
            mock_template = MagicMock()
            mock_template.text = "Сообщение с файлом"
            mock_template.file_path = test_file_path
            mock_db.get_template.return_value = mock_template
            mock_db.update_mailing_stats = AsyncMock()

            mock_group = MagicMock()
            mock_group.chat_ids = [-1001, -1002]

            await execute_mailing_task(
                bot=mock_bot,
                admin_chat_id=123456789,
                mailing_id=1,
                template_id=1,
                groups=[mock_group],
                database=mock_db,
            )

            # Проверяем что отправлялся документ, а не обычное сообщение
            assert mock_bot.send_document.call_count >= 2
            mock_db.update_mailing_stats.assert_called_once()

        finally:
            # Удаляем тестовый файл
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

    @pytest.mark.asyncio
    async def test_execute_mailing_task_with_errors(self):
        """Тест выполнения рассылки с ошибками"""
        mock_bot = AsyncMock()

        # Настраиваем ошибки для определенных чатов
        def mock_send_message(chat_id, text):
            if chat_id == -1002:
                raise TelegramUnauthorizedError("Bot was blocked")
            elif chat_id == -1003:
                raise TelegramBadRequest("Chat not found")
            return AsyncMock()

        mock_bot.send_message = AsyncMock(side_effect=mock_send_message)

        mock_db = AsyncMock()
        mock_template = MagicMock()
        mock_template.text = "Тестовое сообщение"
        mock_template.file_path = None
        mock_db.get_template.return_value = mock_template
        mock_db.update_mailing_stats = AsyncMock()

        mock_group = MagicMock()
        mock_group.chat_ids = [-1001, -1002, -1003, -1004]

        await execute_mailing_task(
            bot=mock_bot,
            admin_chat_id=123456789,
            mailing_id=1,
            template_id=1,
            groups=[mock_group],
            database=mock_db,
        )

        # Проверяем статистику (2 успешно, 2 ошибки)
        call_args = mock_db.update_mailing_stats.call_args[0]
        assert call_args[1] == 2  # sent_count
        assert call_args[2] == 2  # failed_count

    @pytest.mark.asyncio
    async def test_execute_mailing_task_missing_template(self):
        """Тест обработки отсутствующего шаблона"""
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock()

        mock_db = AsyncMock()
        mock_db.get_template.return_value = None

        await execute_mailing_task(
            bot=mock_bot,
            admin_chat_id=123456789,
            mailing_id=1,
            template_id=999,
            groups=[],
            database=mock_db,
        )

        # Проверяем что отправлено сообщение об ошибке
        mock_bot.send_message.assert_called()
        call_args = mock_bot.send_message.call_args[0]
        assert "не найден" in call_args[1].lower()

    @pytest.mark.asyncio
    async def test_execute_mailing_task_empty_groups(self):
        """Тест обработки пустых групп"""
        mock_bot = AsyncMock()

        mock_db = AsyncMock()
        mock_template = MagicMock()
        mock_template.text = "Тест"
        mock_template.file_path = None
        mock_db.get_template.return_value = mock_template
        mock_db.update_mailing_stats = AsyncMock()

        # Пустая группа
        empty_group = MagicMock()
        empty_group.chat_ids = []

        await execute_mailing_task(
            bot=mock_bot,
            admin_chat_id=123456789,
            mailing_id=1,
            template_id=1,
            groups=[empty_group],
            database=mock_db,
        )

        # Проверяем нулевую статистику
        mock_db.update_mailing_stats.assert_called_once()
        call_args = mock_db.update_mailing_stats.call_args[0]
        assert call_args[1] == 0  # sent_count
        assert call_args[2] == 0  # failed_count


@pytest.mark.e2e
class TestMailingE2E:
    """E2E тесты рассылки"""

    @pytest.mark.asyncio
    async def test_e2e_bot_connection(self):
        """E2E тест подключения к Telegram API"""
        token = os.getenv("TEST_BOT_TOKEN") or os.getenv("BOT_TOKEN")

        if not token:
            pytest.skip("BOT_TOKEN not set")

        bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        try:
            bot_info = await bot.get_me()

            assert bot_info.id is not None
            assert bot_info.username is not None
            assert bot_info.is_bot is True

            print(f"[OK] Подключение к боту @{bot_info.username} (ID: {bot_info.id})")

        except Exception as e:
            pytest.fail(f"Ошибка подключения к Telegram API: {e}")

        finally:
            await bot.session.close()

    @pytest.mark.asyncio
    async def test_e2e_simple_broadcast(self):
        """E2E тест простой рассылки"""
        token = os.getenv("TEST_BOT_TOKEN") or os.getenv("BOT_TOKEN")
        group_ids_str = os.getenv("TEST_GROUP_IDS", "")

        if not token or not group_ids_str.strip():
            pytest.skip("TEST_GROUP_IDS or BOT_TOKEN not set")

        group_ids = [g.strip() for g in group_ids_str.split(",") if g.strip()]
        if not group_ids:
            pytest.skip("No group IDs provided")

        bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        available_groups = []

        # Проверяем доступность групп
        for gid in group_ids:
            try:
                chat = await bot.get_chat(gid)
                print(f"[OK] Доступ к чату {gid}: {chat.title}")
                available_groups.append(gid)
            except (TelegramUnauthorizedError, TelegramBadRequest) as e:
                print(f"[SKIP] Недоступен чат {gid}: {e}")
            except Exception as e:
                print(f"[ERR] Ошибка при проверке чата {gid}: {e}")

            await asyncio.sleep(0.5)

        if not available_groups:
            pytest.skip("Нет доступных групп для теста")

        try:
            # Отправляем тестовые сообщения
            for gid in available_groups:
                message = f"""🧪 <b>E2E ТЕСТ РАССЫЛКИ</b>

<i>Время теста:</i> {datetime.now().strftime('%H:%M:%S')}

✅ Тест простой рассылки прошел успешно!
📤 Бот корректно отправляет сообщения в группы."""

                await bot.send_message(gid, message)
                print(f"[SEND] Сообщение отправлено в {gid}")
                await asyncio.sleep(1.0)

        finally:
            await bot.session.close()

    @pytest.mark.asyncio
    async def test_e2e_file_broadcast(self):
        """E2E тест рассылки с файлом"""
        token = os.getenv("TEST_BOT_TOKEN") or os.getenv("BOT_TOKEN")
        group_ids_str = os.getenv("TEST_GROUP_IDS", "")

        if not token or not group_ids_str.strip():
            pytest.skip("TEST_GROUP_IDS or BOT_TOKEN not set")

        group_ids = [g.strip() for g in group_ids_str.split(",") if g.strip()]
        if not group_ids:
            pytest.skip("No group IDs provided")

        bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        # Создаем тестовый файл
        test_file_content = f"""ТЕСТОВЫЙ ПРАЙС-ЛИСТ E2E

📅 Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M')}

🔸 Категория 1:
- Товар 1: 1000₽
- Товар 2: 1500₽

🔸 Категория 2: 
- Товар 3: 2000₽
- Товар 4: 2500₽

🔸 Категория 3:
- Товар 5: 3000₽
- Товар 6: 3500₽

📞 Контакты: +7 (999) 123-45-67
🌐 Сайт: example.com

Этот файл создан автоматически для E2E тестирования.
"""

        test_file_path = "test_price_list_e2e.txt"
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_file_content)

        try:
            # Отправляем файл в первую доступную группу
            for gid in group_ids:
                try:
                    await bot.get_chat(gid)

                    with open(test_file_path, "rb") as f:
                        await bot.send_document(
                            chat_id=gid,
                            document=f,
                            caption=f"""📎 <b>E2E Тест файловой рассылки</b>

⏰ <i>Время:</i> {datetime.now().strftime('%H:%M:%S')}

✅ Файл успешно отправлен через бота!""",
                        )
                    print(f"[FILE] Файл отправлен в {gid}")
                    break

                except (TelegramUnauthorizedError, TelegramBadRequest):
                    continue
                except Exception as e:
                    pytest.fail(f"Ошибка при отправке файла в {gid}: {e}")

        finally:
            # Удаляем тестовый файл
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

            await bot.session.close()

    @pytest.mark.asyncio
    async def test_e2e_full_workflow(self):
        """E2E тест полного рабочего процесса"""
        token = os.getenv("TEST_BOT_TOKEN") or os.getenv("BOT_TOKEN")
        admin_ids = os.getenv("TEST_ADMIN_IDS") or os.getenv("ADMIN_IDS")
        group_ids_str = os.getenv("TEST_GROUP_IDS", "")

        if not token or not admin_ids or not group_ids_str.strip():
            pytest.skip("Missing required environment variables")

        # Инициализируем БД
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # Создаем тестовые данные
        template = await db.create_template(
            name="E2E Полный тест",
            text=f"""🔄 <b>E2E ПОЛНЫЙ ТЕСТ РАССЫЛКИ</b>

Это комплексный тест всего процесса рассылки:

✅ Шаблон создан в БД
👥 Группы настроены
📤 Рассылка выполняется через execute_mailing_task
📊 Статистика обновляется

🕐 <i>Время теста:</i> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

🤖 <b>Все компоненты работают корректно!</b>""",
        )

        # Парсим группы чатов
        group_ids = [g.strip() for g in group_ids_str.split(",") if g.strip()]
        chat_group = await db.create_chat_group(
            name="E2E Тест группа", chat_ids=group_ids
        )

        # Создаем рассылку
        mailing = await db.create_mailing(
            template_id=template.id,
            group_ids=[chat_group.id],
            total_chats=len(group_ids),
        )

        # Создаем бота
        bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        try:
            # Выполняем рассылку
            admin_id = int(admin_ids.split(",")[0].strip())

            await execute_mailing_task(
                bot=bot,
                admin_chat_id=admin_id,
                mailing_id=mailing.id,
                template_id=template.id,
                groups=[chat_group],
                database=db,
            )

            # Проверяем результаты
            updated_mailing = await db.get_mailing(mailing.id)

            assert updated_mailing.status == "completed"
            assert updated_mailing.sent_count + updated_mailing.failed_count == len(
                group_ids
            )

            # Проверяем успешность
            success_rate = updated_mailing.sent_count / len(group_ids) * 100
            assert success_rate >= 50, f"Низкий процент успеха: {success_rate}%"

            print(
                f"[E2E] Полный тест завершен: {updated_mailing.sent_count}/{len(group_ids)} успешно"
            )

        finally:
            await bot.session.close()


class TestMailingIntegration:
    """Интеграционные тесты рассылки"""

    @pytest.mark.asyncio
    async def test_complete_mailing_workflow(self):
        """Тест полного процесса создания и выполнения рассылки"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # 1. Создаем шаблон
        template = await db.create_template(
            name="Интеграционный тест",
            text="Сообщение для интеграционного тестирования",
        )
        assert template is not None

        # 2. Создаем группы
        group1 = await db.create_chat_group(name="Группа 1", chat_ids=[-1001, -1002])
        group2 = await db.create_chat_group(
            name="Группа 2", chat_ids=[-1003, -1004, -1005]
        )

        # 3. Создаем рассылку
        total_chats = len(group1.chat_ids) + len(group2.chat_ids)
        mailing = await db.create_mailing(
            template_id=template.id,
            group_ids=[group1.id, group2.id],
            total_chats=total_chats,
        )

        # Проверяем начальное состояние
        assert mailing.status == "pending"
        assert mailing.total_chats == 5

        # 4. Симулируем выполнение
        await db.update_mailing_stats(mailing.id, sent_count=4, failed_count=1)

        # 5. Проверяем финальное состояние
        final_mailing = await db.get_mailing(mailing.id)
        assert final_mailing.status == "completed"
        assert final_mailing.sent_count == 4
        assert final_mailing.failed_count == 1

        # 6. Проверяем историю
        history = await db.get_mailings_history(limit=5)
        assert len(history) == 1
        assert history[0].id == mailing.id

    @pytest.mark.asyncio
    async def test_multiple_mailings_management(self):
        """Тест управления несколькими рассылками"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # Создаем несколько шаблонов
        templates = []
        for i in range(3):
            template = await db.create_template(
                name=f"Шаблон {i+1}", text=f"Текст шаблона номер {i+1}"
            )
            templates.append(template)

        # Создаем группы
        groups = []
        for i in range(2):
            group = await db.create_chat_group(
                name=f"Группа {i+1}",
                chat_ids=[-(1000 + j) for j in range(i * 3, (i + 1) * 3)],
            )
            groups.append(group)

        # Создаем рассылки с разными статусами
        mailings = []
        for i, template in enumerate(templates):
            mailing = await db.create_mailing(
                template_id=template.id, group_ids=[groups[i % 2].id], total_chats=3
            )
            mailings.append(mailing)

            # Разные результаты
            if i == 0:
                # Полностью успешная
                await db.update_mailing_stats(mailing.id, 3, 0)
            elif i == 1:
                # Частично успешная
                await db.update_mailing_stats(mailing.id, 2, 1)
            # Третью оставляем pending

        # Проверяем историю
        history = await db.get_mailings_history(limit=10)
        assert len(history) == 3

        # Проверяем статусы
        statuses = [m.status for m in history]
        assert "completed" in statuses
        assert "pending" in statuses

        # Проверяем общую статистику
        total_sent = sum(m.sent_count for m in history)
        total_failed = sum(m.failed_count for m in history)

        assert total_sent == 5  # 3 + 2 + 0
        assert total_failed == 1  # 0 + 1 + 0

    @pytest.mark.asyncio
    async def test_mailing_with_file_template(self):
        """Тест рассылки с файловым шаблоном"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # Создаем тестовый файл
        test_file = "integration_test_file.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Интеграционный тест с файлом")

        try:
            # Создаем шаблон с файлом
            template = await db.create_template(
                name="Шаблон с файлом",
                text="Сообщение с прикрепленным файлом",
                file_path=test_file,
            )

            group = await db.create_chat_group(
                name="Тест группа", chat_ids=[-1001, -1002]
            )

            mailing = await db.create_mailing(
                template_id=template.id, group_ids=[group.id], total_chats=2
            )

            # Проверяем что шаблон содержит файл
            assert template.file_path == test_file
            assert os.path.exists(template.file_path)

            # Симулируем успешную отправку
            await db.update_mailing_stats(mailing.id, 2, 0)

            final_mailing = await db.get_mailing(mailing.id)
            assert final_mailing.sent_count == 2
            assert final_mailing.status == "completed"

        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


class TestMailingPerformance:
    """Тесты производительности и масштабируемости"""

    @pytest.mark.asyncio
    async def test_large_group_performance(self):
        """Тест производительности с большой группой"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # Создаем большую группу (1000 чатов)
        large_chat_ids = [-(10000 + i) for i in range(1000)]

        template = await db.create_template(
            name="Большая рассылка", text="Тест производительности для 1000 чатов"
        )

        start_time = datetime.now()

        large_group = await db.create_chat_group(
            name="Большая группа", chat_ids=large_chat_ids
        )

        creation_time = (datetime.now() - start_time).total_seconds()
        assert creation_time < 5.0  # Создание группы должно быть быстрым

        # Создаем рассылку
        mailing = await db.create_mailing(
            template_id=template.id, group_ids=[large_group.id], total_chats=1000
        )

        assert mailing.total_chats == 1000

        # Симулируем пакетное обновление статистики
        batch_size = 100
        for i in range(0, 1000, batch_size):
            current_sent = min(i + batch_size, 1000)
            await db.update_mailing_stats(
                mailing.id, sent_count=current_sent, failed_count=0
            )

        processing_time = (datetime.now() - start_time).total_seconds()
        assert processing_time < 10.0  # Полная обработка за разумное время

        final_mailing = await db.get_mailing(mailing.id)
        assert final_mailing.sent_count == 1000
        assert final_mailing.status == "completed"

    @pytest.mark.asyncio
    async def test_concurrent_mailings_performance(self):
        """Тест производительности параллельных рассылок"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        # Создаем множество шаблонов и групп
        templates = []
        groups = []

        for i in range(10):
            template = await db.create_template(
                name=f"Параллельный шаблон {i+1}",
                text=f"Текст для параллельной рассылки {i+1}",
            )
            templates.append(template)

            group = await db.create_chat_group(
                name=f"Параллельная группа {i+1}",
                chat_ids=[-(20000 + i * 10 + j) for j in range(10)],
            )
            groups.append(group)

        start_time = datetime.now()

        # Создаем рассылки параллельно
        tasks = []
        for template, group in zip(templates, groups):
            task = db.create_mailing(
                template_id=template.id, group_ids=[group.id], total_chats=10
            )
            tasks.append(task)

        mailings = await asyncio.gather(*tasks)

        creation_time = (datetime.now() - start_time).total_seconds()
        assert creation_time < 5.0  # Параллельное создание должно быть быстрым

        # Проверяем результаты
        assert len(mailings) == 10
        assert all(m.status == "pending" for m in mailings)
        assert all(m.total_chats == 10 for m in mailings)

        # Параллельно обновляем статистику
        update_tasks = []
        for mailing in mailings:
            task = db.update_mailing_stats(mailing.id, sent_count=10, failed_count=0)
            update_tasks.append(task)

        await asyncio.gather(*update_tasks)

        total_time = (datetime.now() - start_time).total_seconds()
        assert total_time < 10.0

        # Проверяем финальные результаты
        history = await db.get_mailings_history(limit=20)
        assert len(history) == 10
        assert all(m.status == "completed" for m in history)

        total_sent = sum(m.sent_count for m in history)
        assert total_sent == 100  # 10 рассылок × 10 чатов


class TestMailingErrorHandling:
    """Тесты обработки ошибок и граничных случаев"""

    @pytest.mark.asyncio
    async def test_invalid_template_handling(self):
        """Тест обработки некорректных шаблонов"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        group = await db.create_chat_group("Тест", [-1001])

        # Попытка создать рассылку с несуществующим шаблоном
        with pytest.raises(Exception):
            await db.create_mailing(
                template_id=999999,  # Несуществующий ID
                group_ids=[group.id],
                total_chats=1,
            )

    @pytest.mark.asyncio
    async def test_invalid_group_handling(self):
        """Тест обработки некорректных групп"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        template = await db.create_template("Тест", "Сообщение")

        # Попытка создать рассылку с несуществующей группой
        with pytest.raises(Exception):
            await db.create_mailing(
                template_id=template.id,
                group_ids=[999999],  # Несуществующий ID группы
                total_chats=1,
            )

    @pytest.mark.asyncio
    async def test_empty_groups_handling(self):
        """Тест обработки пустых групп"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        template = await db.create_template("Тест", "Сообщение")
        empty_group = await db.create_chat_group("Пустая группа", [])

        # Создание рассылки с пустой группой
        mailing = await db.create_mailing(
            template_id=template.id, group_ids=[empty_group.id], total_chats=0
        )

        assert mailing.total_chats == 0

        # Обновление статистики для пустой рассылки
        await db.update_mailing_stats(mailing.id, 0, 0)

        updated = await db.get_mailing(mailing.id)
        assert updated.status == "completed"
        assert updated.sent_count == 0

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self):
        """Тест отката транзакций при ошибках"""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.init_db()

        template = await db.create_template("Тест", "Сообщение")
        group = await db.create_chat_group("Группа", [-1001])

        # Попытка обновить статистику несуществующей рассылки
        try:
            await db.update_mailing_stats(999999, 1, 0)
        except Exception:
            pass  # Ожидаем ошибку

        # Проверяем что БД осталась в консистентном состоянии
        mailings = await db.get_mailings_history()
        assert len(mailings) == 0  # Не должно быть артефактов


if __name__ == "__main__":
    # Запуск конкретных категорий тестов
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "unit":
            pytest.main([__file__ + "::TestMailingFunctions", "-v"])
        elif sys.argv[1] == "integration":
            pytest.main([__file__ + "::TestMailingIntegration", "-v"])
        elif sys.argv[1] == "e2e":
            pytest.main([__file__ + "::TestMailingE2E", "-v"])
        elif sys.argv[1] == "performance":
            pytest.main([__file__ + "::TestMailingPerformance", "-v"])
        elif sys.argv[1] == "errors":
            pytest.main([__file__ + "::TestMailingErrorHandling", "-v"])
        else:
            pytest.main([__file__, "-v"])
    else:
        # Запуск всех тестов
        pytest.main([__file__, "-v", "--tb=short"])
