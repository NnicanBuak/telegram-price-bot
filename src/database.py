from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    select,
    update,
    delete,
    desc,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

Base = declarative_base()


class Template(Base):
    """Модель шаблона сообщения"""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    file_id = Column(String(255), nullable=True)  # Telegram file_id
    file_type = Column(String(50), nullable=True)  # photo, document
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatGroup(Base):
    """Модель группы чатов"""

    __tablename__ = "chat_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    chat_ids = Column(JSON, nullable=False)  # List[int]
    created_at = Column(DateTime, default=datetime.utcnow)


class Mailing(Base):
    """Модель рассылки"""

    __tablename__ = "mailings"

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, nullable=False)
    group_ids = Column(JSON, nullable=False)  # List[int]
    total_chats = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(
        String(50), default="pending"
    )  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Database:
    """Упрощенная работа с БД"""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init(self):
        """Создание таблиц"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """Закрытие соединения"""
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self):
        """Получение сессии БД"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # ========== TEMPLATES ==========
    async def create_template(
        self, name: str, text: str, file_id: str = None, file_type: str = None
    ) -> Template:
        async with self.session() as session:
            template = Template(
                name=name, text=text, file_id=file_id, file_type=file_type
            )
            session.add(template)
            await session.flush()
            await session.refresh(template)
            return template

    async def get_templates(self) -> List[Template]:
        async with self.session() as session:
            result = await session.execute(select(Template).order_by(Template.id))
            return list(result.scalars().all())

    async def get_template(self, template_id: int) -> Optional[Template]:
        async with self.session() as session:
            return await session.get(Template, template_id)

    async def update_template(
        self,
        template_id: int,
        name: str = None,
        text: str = None,
        file_id: str = None,
        file_type: str = None,
    ) -> bool:
        async with self.session() as session:
            template = await session.get(Template, template_id)
            if not template:
                return False

            if name is not None:
                template.name = name
            if text is not None:
                template.text = text
            if file_id is not None:
                template.file_id = file_id
            if file_type is not None:
                template.file_type = file_type

            return True

    async def delete_template(self, template_id: int) -> bool:
        async with self.session() as session:
            template = await session.get(Template, template_id)
            if template:
                await session.delete(template)
                return True
            return False

    # ========== GROUPS ==========
    async def create_group(self, name: str, chat_ids: List[int]) -> ChatGroup:
        """Создать группу чатов (старое API)"""
        return await self.create_chat_group(name, chat_ids)

    async def create_chat_group(self, name: str, chat_ids: List[int]) -> ChatGroup:
        """Создать группу чатов"""
        async with self.session() as session:
            group = ChatGroup(name=name, chat_ids=chat_ids)
            session.add(group)
            await session.flush()
            await session.refresh(group)
            return group

    async def get_groups(self) -> List[ChatGroup]:
        """Получить все группы (старое API)"""
        return await self.get_chat_groups()

    async def get_chat_groups(self) -> List[ChatGroup]:
        """Получить все группы чатов"""
        async with self.session() as session:
            result = await session.execute(select(ChatGroup).order_by(ChatGroup.id))
            return list(result.scalars().all())

    async def get_group(self, group_id: int) -> Optional[ChatGroup]:
        """Получить группу по ID (старое API)"""
        return await self.get_chat_group(group_id)

    async def get_chat_group(self, group_id: int) -> Optional[ChatGroup]:
        """Получить группу чатов по ID"""
        async with self.session() as session:
            return await session.get(ChatGroup, group_id)

    async def update_chat_group_name(self, group_id: int, name: str) -> bool:
        """Обновить название группы"""
        async with self.session() as session:
            group = await session.get(ChatGroup, group_id)
            if group:
                group.name = name
                return True
            return False

    async def update_chat_group_chats(self, group_id: int, chat_ids: List[int]) -> bool:
        """Обновить список чатов в группе"""
        async with self.session() as session:
            group = await session.get(ChatGroup, group_id)
            if group:
                group.chat_ids = chat_ids
                return True
            return False

    async def delete_group(self, group_id: int) -> bool:
        """Удалить группу (старое API)"""
        return await self.delete_chat_group(group_id)

    async def delete_chat_group(self, group_id: int) -> bool:
        """Удалить группу чатов"""
        async with self.session() as session:
            group = await session.get(ChatGroup, group_id)
            if group:
                await session.delete(group)
                return True
            return False

    # ========== MAILINGS ==========
    async def create_mailing(
        self, template_id: int, group_ids: List[int], total_chats: int = 0
    ) -> Mailing:
        async with self.session() as session:
            mailing = Mailing(
                template_id=template_id, group_ids=group_ids, total_chats=total_chats
            )
            session.add(mailing)
            await session.flush()
            await session.refresh(mailing)
            return mailing

    async def get_mailing(self, mailing_id: int) -> Optional[Mailing]:
        """Получить рассылку по ID"""
        async with self.session() as session:
            return await session.get(Mailing, mailing_id)

    async def update_mailing_status(
        self,
        mailing_id: int,
        status: str,
        sent_count: int = None,
        failed_count: int = None,
    ):
        """Обновить статус рассылки (старое API)"""
        await self.update_mailing_stats(mailing_id, sent_count, failed_count, status)

    async def update_mailing_stats(
        self,
        mailing_id: int,
        sent_count: int = None,
        failed_count: int = None,
        status: str = None,
    ):
        """Обновить статистику рассылки"""
        async with self.session() as session:
            mailing = await session.get(Mailing, mailing_id)
            if mailing:
                if sent_count is not None:
                    mailing.sent_count = sent_count
                if failed_count is not None:
                    mailing.failed_count = failed_count
                if status is not None:
                    mailing.status = status
                    if status == "completed":
                        mailing.completed_at = datetime.utcnow()

    async def get_mailings(self, limit: int = 10) -> List[Mailing]:
        """Получить рассылки (старое API)"""
        return await self.get_mailings_history(limit)

    async def get_mailings_history(self, limit: int = 10) -> List[Mailing]:
        """Получить историю рассылок"""
        async with self.session() as session:
            result = await session.execute(
                select(Mailing).order_by(desc(Mailing.id)).limit(limit)
            )
            return list(result.scalars().all())
