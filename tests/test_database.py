"""
Тесты для модуля database.py
Обновлено для новой структуры проекта
"""

import pytest
import asyncio
from datetime import datetime, timedelta

# Импорты обновлены для src/ структуры
from src.database import Database, Template, ChatGroup, Mailing


@pytest.fixture(scope="function")
async def test_db():
    """Фикстура для тестовой базы данных"""
    # Используем in-memory SQLite для тестов
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.init_db()
    yield db
    # Очистка происходит автоматически для in-memory БД


@pytest.fixture(scope="function")
async def populated_db(test_db):
    """Фикстура с предзаполненными данными"""
    # Создаем тестовые шаблоны
    templates = []
    for i in range(5):
        template = await test_db.create_template(
            name=f"Шаблон {i+1}", text=f"Текст шаблона {i+1}\n<b>Жирный текст</b>"
        )
        templates.append(template)

    # Создаем тестовые группы
    groups = []
    for i in range(3):
        group = await test_db.create_chat_group(
            name=f"Группа {i+1}",
            chat_ids=[-(1000000000000 + j + i * 10) for j in range(3)],
        )
        groups.append(group)

    # Создаем тестовые рассылки
    mailings = []
    for i in range(2):
        mailing = await test_db.create_mailing(
            template_id=templates[i].id,
            group_ids=[g.id for g in groups[: i + 1]],
            total_chats=(i + 1) * 3,
        )
        mailings.append(mailing)

    yield test_db, templates, groups, mailings


class TestTemplateOperations:
    """Тесты операций с шаблонами"""

    @pytest.mark.asyncio
    async def test_create_template_minimal(self, test_db):
        """Тест создания шаблона с минимальными данными"""
        template = await test_db.create_template(
            name="Минимальный шаблон", text="Простой текст"
        )

        assert template.id is not None
        assert template.name == "Минимальный шаблон"
        assert template.text == "Простой текст"
        assert template.file_id is None
        assert template.file_type is None
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_template_with_file(self, test_db):
        """Тест создания шаблона с файлом"""
        template = await test_db.create_template(
            name="Шаблон с файлом",
            text="Текст с прикрепленным документом",
            file_id="AgACAgIAAxkBAAICVGKj3...",
            file_type="document",
        )

        assert template.file_id == "AgACAgIAAxkBAAICVGKj3..."
        assert template.file_type == "document"

    @pytest.mark.asyncio
    async def test_create_template_with_photo(self, test_db):
        """Тест создания шаблона с фото"""
        template = await test_db.create_template(
            name="Шаблон с фото",
            text="Текст с изображением",
            file_id="photo_file_id_123",
            file_type="photo",
        )

        assert template.file_type == "photo"

    @pytest.mark.asyncio
    async def test_get_template_by_id(self, test_db):
        """Тест получения шаблона по ID"""
        created = await test_db.create_template("Тест", "Текст")

        retrieved = await test_db.get_template(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
        assert retrieved.text == created.text

    @pytest.mark.asyncio
    async def test_get_nonexistent_template(self, test_db):
        """Тест получения несуществующего шаблона"""
        template = await test_db.get_template(99999)
        assert template is None

    @pytest.mark.asyncio
    async def test_get_all_templates(self, populated_db):
        """Тест получения всех шаблонов"""
        db, templates, _, _ = populated_db

        all_templates = await db.get_templates()

        assert len(all_templates) == 5
        # Проверка сортировки по дате создания (desc)
        for i in range(len(all_templates) - 1):
            assert all_templates[i].created_at >= all_templates[i + 1].created_at

    @pytest.mark.asyncio
    async def test_update_template(self, test_db):
        """Тест обновления шаблона"""
        template = await test_db.create_template("Старый", "Старый текст")
        original_created = template.created_at

        # Небольшая задержка для различия updated_at
        await asyncio.sleep(0.01)

        updated = await test_db.update_template(
            template.id, name="Новый", text="Новый текст", file_id="new_file_id"
        )

        assert updated.name == "Новый"
        assert updated.text == "Новый текст"
        assert updated.file_id == "new_file_id"
        assert updated.created_at == original_created
        assert updated.updated_at > original_created

    @pytest.mark.asyncio
    async def test_update_nonexistent_template(self, test_db):
        """Тест обновления несуществующего шаблона"""
        updated = await test_db.update_template(99999, name="Новый")
        assert updated is None

    @pytest.mark.asyncio
    async def test_delete_template(self, test_db):
        """Тест удаления шаблона"""
        template = await test_db.create_template("Удаляемый", "Текст")
        template_id = template.id

        # Удаляем
        result = await test_db.delete_template(template_id)
        assert result is True

        # Проверяем, что удален
        deleted = await test_db.get_template(template_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_template(self, test_db):
        """Тест удаления несуществующего шаблона"""
        result = await test_db.delete_template(99999)
        assert result is False


class TestChatGroupOperations:
    """Тесты операций с группами чатов"""

    @pytest.mark.asyncio
    async def test_create_chat_group(self, test_db):
        """Тест создания группы чатов"""
        chat_ids = [-1001234567890, -1009876543210, -1005555555555]

        group = await test_db.create_chat_group(
            name="Тестовая группа", chat_ids=chat_ids
        )

        assert group.id is not None
        assert group.name == "Тестовая группа"
        assert group.chat_ids == chat_ids
        assert len(group.chat_ids) == 3
        assert isinstance(group.created_at, datetime)

    @pytest.mark.asyncio
    async def test_create_empty_chat_group(self, test_db):
        """Тест создания пустой группы"""
        group = await test_db.create_chat_group(name="Пустая группа", chat_ids=[])

        assert group.chat_ids == []

    @pytest.mark.asyncio
    async def test_get_chat_group_by_id(self, test_db):
        """Тест получения группы по ID"""
        created = await test_db.create_chat_group("Группа", [111, 222, 333])

        retrieved = await test_db.get_chat_group(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
        assert retrieved.chat_ids == created.chat_ids

    @pytest.mark.asyncio
    async def test_get_all_chat_groups(self, populated_db):
        """Тест получения всех групп"""
        db, _, groups, _ = populated_db

        all_groups = await db.get_chat_groups()

        assert len(all_groups) == 3
        # Проверка сортировки
        for i in range(len(all_groups) - 1):
            assert all_groups[i].created_at >= all_groups[i + 1].created_at

    @pytest.mark.asyncio
    async def test_get_chat_groups_by_ids(self, populated_db):
        """Тест получения групп по списку ID"""
        db, _, groups, _ = populated_db

        # Берем ID первых двух групп
        ids_to_get = [groups[0].id, groups[1].id]

        retrieved_groups = await db.get_chat_groups_by_ids(ids_to_get)

        assert len(retrieved_groups) == 2
        retrieved_ids = [g.id for g in retrieved_groups]
        assert groups[0].id in retrieved_ids
        assert groups[1].id in retrieved_ids

    @pytest.mark.asyncio
    async def test_update_chat_group(self, test_db):
        """Тест обновления группы"""
        group = await test_db.create_chat_group("Старая группа", [111, 222])

        updated = await test_db.update_chat_group(
            group.id, name="Новая группа", chat_ids=[333, 444, 555]
        )

        assert updated.name == "Новая группа"
        assert updated.chat_ids == [333, 444, 555]
        assert len(updated.chat_ids) == 3

    @pytest.mark.asyncio
    async def test_delete_chat_group(self, test_db):
        """Тест удаления группы"""
        group = await test_db.create_chat_group("Удаляемая", [111])
        group_id = group.id

        result = await test_db.delete_chat_group(group_id)
        assert result is True

        deleted = await test_db.get_chat_group(group_id)
        assert deleted is None


class TestMailingOperations:
    """Тесты операций с рассылками"""

    @pytest.mark.asyncio
    async def test_create_mailing(self, populated_db):
        """Тест создания рассылки"""
        db, templates, groups, _ = populated_db

        mailing = await db.create_mailing(
            template_id=templates[0].id,
            group_ids=[groups[0].id, groups[1].id],
            total_chats=6,
        )

        assert mailing.id is not None
        assert mailing.template_id == templates[0].id
        assert mailing.group_ids == [groups[0].id, groups[1].id]
        assert mailing.total_chats == 6
        assert mailing.sent_count == 0
        assert mailing.failed_count == 0
        assert mailing.status == "in_progress"
        assert mailing.completed_at is None

    @pytest.mark.asyncio
    async def test_update_mailing_stats(self, populated_db):
        """Тест обновления статистики рассылки"""
        db, templates, groups, _ = populated_db

        mailing = await db.create_mailing(
            template_id=templates[0].id, group_ids=[groups[0].id], total_chats=3
        )

        # Обновляем статистику
        updated = await db.update_mailing_stats(
            mailing_id=mailing.id, sent_count=2, failed_count=1
        )

        assert updated.sent_count == 2
        assert updated.failed_count == 1
        assert updated.status == "completed"
        assert updated.completed_at is not None
        assert isinstance(updated.completed_at, datetime)

    @pytest.mark.asyncio
    async def test_get_mailings_history(self, populated_db):
        """Тест получения истории рассылок"""
        db, templates, groups, existing_mailings = populated_db

        # Создаем дополнительные рассылки
        for i in range(3):
            await db.create_mailing(
                template_id=templates[0].id, group_ids=[groups[0].id], total_chats=3
            )

        # Получаем историю
        history = await db.get_mailings_history(limit=4)

        assert len(history) == 4
        # Проверка сортировки по дате (новые первые)
        for i in range(len(history) - 1):
            assert history[i].created_at >= history[i + 1].created_at

    @pytest.mark.asyncio
    async def test_get_mailings_history_with_limit(self, populated_db):
        """Тест ограничения истории рассылок"""
        db, templates, groups, _ = populated_db

        # Создаем много рассылок
        for i in range(10):
            await db.create_mailing(
                template_id=templates[0].id, group_ids=[groups[0].id], total_chats=3
            )

        # Получаем с ограничением
        history = await db.get_mailings_history(limit=5)
        assert len(history) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
