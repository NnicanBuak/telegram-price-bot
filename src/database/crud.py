"""
CRUD операции для работы с SQLite базой данных
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Template, ChatGroup, Mailing, MailingLog, BotSettings


class TemplateCRUD:
    """CRUD операции для шаблонов"""

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        text: str,
        file_id: Optional[str] = None,
        file_type: Optional[str] = None,
    ) -> Template:
        """Создание нового шаблона"""
        template = Template(name=name, text=text, file_id=file_id, file_type=file_type)
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template

    @staticmethod
    async def get_by_id(session: AsyncSession, template_id: int) -> Optional[Template]:
        """Получение шаблона по ID"""
        result = await session.execute(
            select(Template).where(Template.id == template_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        session: AsyncSession,
        limit: Optional[int] = None,
        offset: int = 0,
        active_only: bool = True,
    ) -> List[Template]:
        """Получение всех шаблонов"""
        query = select(Template)

        if active_only:
            query = query.where(Template.is_active.is_(True))

        query = query.order_by(desc(Template.created_at))

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(
        session: AsyncSession, template_id: int, **kwargs
    ) -> Optional[Template]:
        """Обновление шаблона"""
        # Убираем None значения
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        if not update_data:
            return await TemplateCRUD.get_by_id(session, template_id)

        await session.execute(
            update(Template).where(Template.id == template_id).values(**update_data)
        )
        await session.commit()

        return await TemplateCRUD.get_by_id(session, template_id)

    @staticmethod
    async def delete(session: AsyncSession, template_id: int) -> bool:
        """Удаление шаблона"""
        result = await session.execute(
            delete(Template).where(Template.id == template_id)
        )
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def soft_delete(session: AsyncSession, template_id: int) -> bool:
        """Мягкое удаление шаблона (деактивация)"""
        result = await session.execute(
            update(Template).where(Template.id == template_id).values(is_active=False)
        )
        await session.commit()
        return result.rowcount > 0


class ChatGroupCRUD:
    """CRUD операции для групп чатов"""

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        chat_ids: List[int],
        description: Optional[str] = None,
    ) -> ChatGroup:
        """Создание новой группы чатов"""
        group = ChatGroup(name=name, chat_ids=chat_ids, description=description)
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return group

    @staticmethod
    async def get_by_id(session: AsyncSession, group_id: int) -> Optional[ChatGroup]:
        """Получение группы по ID"""
        result = await session.execute(
            select(ChatGroup).where(ChatGroup.id == group_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        session: AsyncSession,
        limit: Optional[int] = None,
        offset: int = 0,
        active_only: bool = True,
    ) -> List[ChatGroup]:
        """Получение всех групп"""
        query = select(ChatGroup)

        if active_only:
            query = query.where(ChatGroup.is_active.is_(True))

        query = query.order_by(desc(ChatGroup.created_at))

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_ids(
        session: AsyncSession, group_ids: List[int]
    ) -> List[ChatGroup]:
        """Получение групп по списку ID"""
        result = await session.execute(
            select(ChatGroup).where(ChatGroup.id.in_(group_ids))
        )
        return result.scalars().all()

    @staticmethod
    async def update(
        session: AsyncSession, group_id: int, **kwargs
    ) -> Optional[ChatGroup]:
        """Обновление группы"""
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        if not update_data:
            return await ChatGroupCRUD.get_by_id(session, group_id)

        await session.execute(
            update(ChatGroup).where(ChatGroup.id == group_id).values(**update_data)
        )
        await session.commit()

        return await ChatGroupCRUD.get_by_id(session, group_id)

    @staticmethod
    async def delete(session: AsyncSession, group_id: int) -> bool:
        """Удаление группы"""
        result = await session.execute(
            delete(ChatGroup).where(ChatGroup.id == group_id)
        )
        await session.commit()
        return result.rowcount > 0


class MailingCRUD:
    """CRUD операции для рассылок"""

    @staticmethod
    async def create(
        session: AsyncSession,
        template_id: int,
        group_ids: List[int],
        total_chats: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Mailing:
        """Создание новой рассылки"""
        mailing = Mailing(
            template_id=template_id,
            group_ids=group_ids,
            total_chats=total_chats,
            status="pending",
            metadata=metadata,
        )
        session.add(mailing)
        await session.commit()
        await session.refresh(mailing)
        return mailing

    @staticmethod
    async def get_by_id(session: AsyncSession, mailing_id: int) -> Optional[Mailing]:
        """Получение рассылки по ID"""
        result = await session.execute(select(Mailing).where(Mailing.id == mailing_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_history(
        session: AsyncSession, limit: int = 50, offset: int = 0
    ) -> List[Mailing]:
        """Получение истории рассылок"""
        result = await session.execute(
            select(Mailing)
            .order_by(desc(Mailing.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def update_status(
        session: AsyncSession,
        mailing_id: int,
        status: str,
        sent_count: Optional[int] = None,
        failed_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Mailing]:
        """Обновление статуса рассылки"""
        update_data = {"status": status}

        if sent_count is not None:
            update_data["sent_count"] = sent_count
        if failed_count is not None:
            update_data["failed_count"] = failed_count
        if error_message is not None:
            update_data["error_message"] = error_message

        # Установка временных меток
        if status == "in_progress" and not update_data.get("started_at"):
            update_data["started_at"] = datetime.utcnow()
        elif status in ["completed", "failed", "cancelled"]:
            update_data["completed_at"] = datetime.utcnow()

        await session.execute(
            update(Mailing).where(Mailing.id == mailing_id).values(**update_data)
        )
        await session.commit()

        return await MailingCRUD.get_by_id(session, mailing_id)

    @staticmethod
    async def get_statistics(session: AsyncSession) -> Dict[str, Any]:
        """Получение статистики рассылок"""
        # Общее количество рассылок
        total_result = await session.execute(select(func.count(Mailing.id)))
        total_mailings = total_result.scalar()

        # Статистика по статусам
        status_result = await session.execute(
            select(Mailing.status, func.count(Mailing.id)).group_by(Mailing.status)
        )
        status_stats = dict(status_result.fetchall())

        # Общая статистика отправок
        stats_result = await session.execute(
            select(
                func.sum(Mailing.total_chats),
                func.sum(Mailing.sent_count),
                func.sum(Mailing.failed_count),
            )
        )
        total_chats, total_sent, total_failed = stats_result.fetchone()

        return {
            "total_mailings": total_mailings,
            "status_distribution": status_stats,
            "total_chats": total_chats or 0,
            "total_sent": total_sent or 0,
            "total_failed": total_failed or 0,
            "success_rate": (total_sent / total_chats * 100) if total_chats else 0,
        }


class BotSettingsCRUD:
    """CRUD операции для настроек бота"""

    @staticmethod
    async def get(session: AsyncSession, key: str) -> Optional[Any]:
        """Получение настройки по ключу"""
        result = await session.execute(
            select(BotSettings).where(BotSettings.key == key)
        )
        setting = result.scalar_one_or_none()
        return setting.value if setting else None

    @staticmethod
    async def set(
        session: AsyncSession,
        key: str,
        value: Any,
        description: Optional[str] = None,
        is_system: bool = False,
    ) -> BotSettings:
        """Установка настройки"""
        # Проверяем, существует ли настройка
        existing = await session.execute(
            select(BotSettings).where(BotSettings.key == key)
        )
        setting = existing.scalar_one_or_none()

        if setting:
            # Обновляем существующую
            setting.value = value
            if description is not None:
                setting.description = description
        else:
            # Создаем новую
            setting = BotSettings(
                key=key, value=value, description=description, is_system=is_system
            )
            session.add(setting)

        await session.commit()
        await session.refresh(setting)
        return setting

    @staticmethod
    async def delete(session: AsyncSession, key: str) -> bool:
        """Удаление настройки"""
        result = await session.execute(
            delete(BotSettings).where(BotSettings.key == key)
        )
        await session.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_all(session: AsyncSession) -> List[BotSettings]:
        """Получение всех настроек"""
        result = await session.execute(select(BotSettings).order_by(BotSettings.key))
        return result.scalars().all()
