"""
Модуль для работы с базой данных
"""

import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    Boolean,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

Base = declarative_base()


class Template(Base):
    """Модель шаблона сообщения"""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    file_id = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)  # 'photo' или 'document'
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


class Database:
    """Класс для работы с базой данных"""

    def __init__(self, database_url: str):
        # Преобразуем URL для asyncpg
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
        elif database_url.startswith("sqlite://"):
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Инициализация таблиц БД"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Методы для работы с шаблонами
    async def create_template(
        self,
        name: str,
        text: str,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Template:
        """Создание нового шаблона"""
        async with self.async_session() as session:
            template = Template(
                name=name, text=text, file_id=file_id, file_type=file_type
            )
            session.add(template)
            await session.commit()
            await session.refresh(template)
            return template

    async def get_template(self, template_id: int) -> Optional[Template]:
        """Получение шаблона по ID"""
        async with self.async_session() as session:
            result = await session.get(Template, template_id)
            return result

    async def get_templates(self) -> List[Template]:
        """Получение всех шаблонов"""
        async with self.async_session() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Template).order_by(Template.created_at.desc())
            )
            return result.scalars().all()

    async def update_template(self, template_id: int, **kwargs) -> Optional[Template]:
        """Обновление шаблона"""
        async with self.async_session() as session:
            template = await session.get(Template, template_id)
            if template:
                for key, value in kwargs.items():
                    if hasattr(template, key):
                        setattr(template, key, value)
                template.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(template)
            return template

    async def delete_template(self, template_id: int) -> bool:
        """Удаление шаблона"""
        async with self.async_session() as session:
            template = await session.get(Template, template_id)
            if template:
                await session.delete(template)
                await session.commit()
                return True
            return False

    # Методы для работы с группами чатов
    async def create_chat_group(self, name: str, chat_ids: List[int]) -> ChatGroup:
        """Создание новой группы чатов"""
        async with self.async_session() as session:
            group = ChatGroup(name=name, chat_ids=chat_ids)
            session.add(group)
            await session.commit()
            await session.refresh(group)
            return group

    async def get_chat_group(self, group_id: int) -> Optional[ChatGroup]:
        """Получение группы по ID"""
        async with self.async_session() as session:
            result = await session.get(ChatGroup, group_id)
            return result

    async def get_chat_groups(self) -> List[ChatGroup]:
        """Получение всех групп"""
        async with self.async_session() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(ChatGroup).order_by(ChatGroup.created_at.desc())
            )
            return result.scalars().all()

    async def get_chat_groups_by_ids(self, group_ids: List[int]) -> List[ChatGroup]:
        """Получение групп по списку ID"""
        async with self.async_session() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(ChatGroup).where(ChatGroup.id.in_(group_ids))
            )
            return result.scalars().all()

    async def update_chat_group(self, group_id: int, **kwargs) -> Optional[ChatGroup]:
        """Обновление группы"""
        async with self.async_session() as session:
            group = await session.get(ChatGroup, group_id)
            if group:
                for key, value in kwargs.items():
                    if hasattr(group, key):
                        setattr(group, key, value)
                group.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(group)
            return group

    async def delete_chat_group(self, group_id: int) -> bool:
        """Удаление группы"""
        async with self.async_session() as session:
            group = await session.get(ChatGroup, group_id)
            if group:
                await session.delete(group)
                await session.commit()
                return True
            return False

    # Методы для работы с рассылками
    async def create_mailing(
        self, template_id: int, group_ids: List[int], total_chats: int
    ) -> Mailing:
        """Создание новой рассылки"""
        async with self.async_session() as session:
            mailing = Mailing(
                template_id=template_id,
                group_ids=group_ids,
                total_chats=total_chats,
                status="in_progress",
            )
            session.add(mailing)
            await session.commit()
            await session.refresh(mailing)
            return mailing

    async def update_mailing_stats(
        self, mailing_id: int, sent_count: int, failed_count: int
    ) -> Optional[Mailing]:
        """Обновление статистики рассылки"""
        async with self.async_session() as session:
            mailing = await session.get(Mailing, mailing_id)
            if mailing:
                mailing.sent_count = sent_count
                mailing.failed_count = failed_count
                mailing.status = "completed"
                mailing.completed_at = datetime.utcnow()
                await session.commit()
                await session.refresh(mailing)
            return mailing

    async def get_mailings_history(self, limit: int = 50) -> List[Mailing]:
        """Получение истории рассылок"""
        async with self.async_session() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(Mailing).order_by(Mailing.created_at.desc()).limit(limit)
            )
            return result.scalars().all()
