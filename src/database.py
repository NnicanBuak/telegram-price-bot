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

    # Templates
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

    async def delete_template(self, template_id: int) -> bool:
        async with self.session() as session:
            template = await session.get(Template, template_id)
            if template:
                await session.delete(template)
                return True
            return False

    # Groups
    async def create_group(self, name: str, chat_ids: List[int]) -> ChatGroup:
        async with self.session() as session:
            group = ChatGroup(name=name, chat_ids=chat_ids)
            session.add(group)
            await session.flush()
            await session.refresh(group)
            return group

    async def get_groups(self) -> List[ChatGroup]:
        async with self.session() as session:
            result = await session.execute(select(ChatGroup).order_by(ChatGroup.id))
            return list(result.scalars().all())

    async def get_group(self, group_id: int) -> Optional[ChatGroup]:
        async with self.session() as session:
            return await session.get(ChatGroup, group_id)

    async def delete_group(self, group_id: int) -> bool:
        async with self.session() as session:
            group = await session.get(ChatGroup, group_id)
            if group:
                await session.delete(group)
                return True
            return False

    # Mailings
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

    async def update_mailing_status(
        self,
        mailing_id: int,
        status: str,
        sent_count: int = None,
        failed_count: int = None,
    ):
        async with self.session() as session:
            stmt = update(Mailing).where(Mailing.id == mailing_id).values(status=status)
            if sent_count is not None:
                stmt = stmt.values(sent_count=sent_count)
            if failed_count is not None:
                stmt = stmt.values(failed_count=failed_count)
            if status == "completed":
                stmt = stmt.values(completed_at=datetime.utcnow())
            await session.execute(stmt)

    async def get_mailings(self, limit: int = 10) -> List[Mailing]:
        async with self.session() as session:
            result = await session.execute(
                select(Mailing).order_by(desc(Mailing.id)).limit(limit)
            )
            return list(result.scalars().all())
