from datetime import datetime, timedelta
from typing import List, Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    Boolean,
    select,
    update,
    delete,
    desc,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)

Base = declarative_base()


# ========== МОДЕЛИ ==========


class Template(Base):
    """Модель шаблона сообщения"""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    file_id = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)  # 'photo' или 'document'
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatGroup(Base):
    """Модель группы чатов"""

    __tablename__ = "chat_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    chat_ids = Column(JSON, nullable=False)  # Список ID чатов
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Mailing(Base):
    """Модель рассылки"""

    __tablename__ = "mailings"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, nullable=False)
    group_ids = Column(JSON, nullable=False)  # Список ID групп
    total_chats = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(
        String(50), default="pending"
    )  # pending, in_progress, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# ========== ОСНОВНОЙ КЛАСС БАЗЫ ДАННЫХ ==========


class Database:
    """Класс для работы с SQLite базой данных"""

    def __init__(
        self,
        database_url: str = "sqlite+aiosqlite:///bot_database.db",
        echo: bool = False,
    ):
        """
        Инициализация SQLite базы данных

        Args:
            database_url: URL для подключения к SQLite БД
            echo: Логирование SQL запросов
        """
        self.database_url = database_url

        # Настройки для SQLite
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            future=True,
        )

        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

    async def init_database(self) -> None:
        """Инициализация базы данных - создание таблиц"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_database(self) -> None:
        """Удаление всех таблиц"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        """Закрытие соединения с БД"""
        if self.engine:
            await self.engine.dispose()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Контекстный менеджер для получения сессии БД

        Yields:
            AsyncSession: Сессия базы данных
        """
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def health_check(self) -> bool:
        """
        Проверка состояния базы данных

        Returns:
            bool: True если БД доступна
        """
        try:
            async with self.get_session() as session:
                await session.execute(select(1))
                return True
        except Exception:
            return False

    # ========== МЕТОДЫ ДЛЯ ШАБЛОНОВ ==========

    async def create_template(
        self,
        name: str,
        text: str,
        file_id: str = None,
        file_type: str = None,
        file_path: str = None,
    ) -> Template:
        """Создать новый шаблон"""
        async with self.get_session() as session:
            template = Template(
                name=name,
                text=text,
                file_id=file_id,
                file_type=file_type,
                file_path=file_path,
            )
            session.add(template)
            await session.flush()  # Получаем ID до коммита
            await session.refresh(template)
            return template

    async def get_templates(self) -> List[Template]:
        """Получить все шаблоны"""
        async with self.get_session() as session:
            result = await session.execute(select(Template).order_by(Template.id))
            return list(result.scalars().all())

    async def get_template(self, template_id: int) -> Optional[Template]:
        """Получить шаблон по ID"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Template).where(Template.id == template_id)
            )
            return result.scalar_one_or_none()

    async def update_template(
        self,
        template_id: int,
        name: str = None,
        text: str = None,
        file_id: str = None,
        file_type: str = None,
    ) -> Optional[Template]:
        """Обновить шаблон"""
        async with self.get_session() as session:
            template = await session.get(Template, template_id)
            if not template:
                return None

            if name is not None:
                template.name = name
            if text is not None:
                template.text = text
            if file_id is not None:
                template.file_id = file_id
            if file_type is not None:
                template.file_type = file_type

            template.updated_at = datetime.utcnow()
            await session.flush()
            await session.refresh(template)
            return template

    async def delete_template(self, template_id: int) -> bool:
        """Удалить шаблон"""
        async with self.get_session() as session:
            template = await session.get(Template, template_id)
            if not template:
                return False

            await session.delete(template)
            return True

    # ========== МЕТОДЫ ДЛЯ ГРУПП ЧАТОВ ==========

    async def create_chat_group(self, name: str, chat_ids: List[int]) -> ChatGroup:
        """Создать новую группу чатов"""
        async with self.get_session() as session:
            group = ChatGroup(
                name=name,
                chat_ids=chat_ids,
            )
            session.add(group)
            await session.flush()
            await session.refresh(group)
            return group

    async def get_chat_groups(self) -> List[ChatGroup]:
        """Получить все группы чатов"""
        async with self.get_session() as session:
            result = await session.execute(select(ChatGroup).order_by(ChatGroup.id))
            return list(result.scalars().all())

    async def get_chat_group(self, group_id: int) -> Optional[ChatGroup]:
        """Получить группу чатов по ID"""
        async with self.get_session() as session:
            result = await session.execute(
                select(ChatGroup).where(ChatGroup.id == group_id)
            )
            return result.scalar_one_or_none()

    async def update_chat_group(
        self, group_id: int, name: str = None, chat_ids: List[int] = None
    ) -> Optional[ChatGroup]:
        """Обновить группу чатов"""
        async with self.get_session() as session:
            group = await session.get(ChatGroup, group_id)
            if not group:
                return None

            if name is not None:
                group.name = name
            if chat_ids is not None:
                group.chat_ids = chat_ids

            group.updated_at = datetime.utcnow()
            await session.flush()
            await session.refresh(group)
            return group

    async def delete_chat_group(self, group_id: int) -> bool:
        """Удалить группу чатов"""
        async with self.get_session() as session:
            group = await session.get(ChatGroup, group_id)
            if not group:
                return False

            await session.delete(group)
            return True

    # ========== МЕТОДЫ ДЛЯ РАССЫЛОК ==========

    async def create_mailing(
        self, template_id: int, group_ids: List[int], total_chats: int = 0
    ) -> Mailing:
        """Создать новую рассылку"""
        async with self.get_session() as session:
            mailing = Mailing(
                template_id=template_id,
                group_ids=group_ids,
                total_chats=total_chats,
                status="pending",
            )
            session.add(mailing)
            await session.flush()
            await session.refresh(mailing)
            return mailing

    async def get_mailings(self, limit: int = None) -> List[Mailing]:
        """Получить все рассылки"""
        async with self.get_session() as session:
            query = select(Mailing).order_by(desc(Mailing.id))
            if limit:
                query = query.limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_mailing(self, mailing_id: int) -> Optional[Mailing]:
        """Получить рассылку по ID"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Mailing).where(Mailing.id == mailing_id)
            )
            return result.scalar_one_or_none()

    async def update_mailing_status(
        self,
        mailing_id: int,
        status: str,
        sent_count: int = None,
        failed_count: int = None,
    ) -> Optional[Mailing]:
        """Обновить статус рассылки"""
        async with self.get_session() as session:
            mailing = await session.get(Mailing, mailing_id)
            if not mailing:
                return None

            mailing.status = status
            if sent_count is not None:
                mailing.sent_count = sent_count
            if failed_count is not None:
                mailing.failed_count = failed_count

            if status == "completed":
                mailing.completed_at = datetime.utcnow()

            await session.flush()
            await session.refresh(mailing)
            return mailing

    async def update_mailing_stats(
        self,
        mailing_id: int,
        sent_count: int = None,
        failed_count: int = None,
        status: str = None,
    ) -> Optional[Mailing]:
        """Обновить статистику рассылки"""
        return await self.update_mailing_status(
            mailing_id, status or "in_progress", sent_count, failed_count
        )

    async def delete_mailing(self, mailing_id: int) -> bool:
        """Удалить рассылку"""
        async with self.get_session() as session:
            mailing = await session.get(Mailing, mailing_id)
            if not mailing:
                return False

            await session.delete(mailing)
            return True

    # ========== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ==========

    async def get_recent_mailings(self, limit: int = 10) -> List[Mailing]:
        """Получить последние рассылки"""
        return await self.get_mailings(limit=limit)

    async def get_mailing_stats(self) -> dict:
        """Получить статистику рассылок"""
        async with self.get_session() as session:
            # Подсчет по статусам
            stats = {
                "total": 0,
                "pending": 0,
                "in_progress": 0,
                "completed": 0,
                "failed": 0,
            }

            result = await session.execute(select(Mailing))
            mailings = result.scalars().all()

            for mailing in mailings:
                stats["total"] += 1
                stats[mailing.status] = stats.get(mailing.status, 0) + 1

            return stats

    async def cleanup_old_mailings(self, days: int = 30) -> int:
        """Очистить старые рассылки"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with self.get_session() as session:
            result = await session.execute(
                delete(Mailing).where(Mailing.created_at < cutoff_date)
            )
            return result.rowcount

    async def clear_all_data(self):
        """Очистить все данные (для тестов)"""
        async with self.get_session() as session:
            await session.execute(delete(Mailing))
            await session.execute(delete(ChatGroup))
            await session.execute(delete(Template))

    async def export_data(self) -> dict:
        """Экспорт всех данных"""
        templates = await self.get_templates()
        groups = await self.get_chat_groups()
        mailings = await self.get_mailings()

        return {
            "templates": [
                {
                    "id": t.id,
                    "name": t.name,
                    "text": t.text,
                    "file_id": t.file_id,
                    "file_type": t.file_type,
                    "created_at": t.created_at.isoformat(),
                }
                for t in templates
            ],
            "groups": [
                {
                    "id": g.id,
                    "name": g.name,
                    "chat_ids": g.chat_ids,
                    "created_at": g.created_at.isoformat(),
                }
                for g in groups
            ],
            "mailings": [
                {
                    "id": m.id,
                    "template_id": m.template_id,
                    "group_ids": m.group_ids,
                    "total_chats": m.total_chats,
                    "sent_count": m.sent_count,
                    "failed_count": m.failed_count,
                    "status": m.status,
                    "created_at": m.created_at.isoformat(),
                    "completed_at": (
                        m.completed_at.isoformat() if m.completed_at else None
                    ),
                }
                for m in mailings
            ],
        }


# ========== ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР И ФУНКЦИИ ==========

_database: Optional[Database] = None


def get_database() -> Database:
    """Получение экземпляра базы данных"""
    global _database
    if _database is None:
        raise RuntimeError(
            "База данных не инициализирована. Вызовите init_database() сначала."
        )
    return _database


def init_database(
    database_url: str = "sqlite+aiosqlite:///bot_database.db", echo: bool = False
) -> Database:
    """
    Инициализация базы данных

    Args:
        database_url: URL для подключения к БД
        echo: Логирование SQL запросов

    Returns:
        Database: Экземпляр базы данных
    """
    global _database
    _database = Database(database_url, echo)
    return _database


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Получение сессии базы данных

    Yields:
        AsyncSession: Сессия базы данных
    """
    db = get_database()
    async with db.get_session() as session:
        yield session
