"""
Управление сессиями SQLite базы данных
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)

from .models import Base


class Database:
    """Класс для управления SQLite базой данных"""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """
        Инициализация SQLite базы данных

        Args:
            database_url: URL для подключения к SQLite БД
            echo: Логирование SQL запросов
        """
        # Настройки для SQLite
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )

        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

    async def init_db(self) -> None:
        """Создание таблиц в базе данных"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_db(self) -> None:
        """Удаление всех таблиц"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        """Закрытие соединения с БД"""
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
                await session.execute("SELECT 1")
                return True
        except Exception:
            return False


# Глобальный экземпляр базы данных
_database: Database = None


def get_database() -> Database:
    """Получение экземпляра базы данных"""
    global _database
    if _database is None:
        raise RuntimeError("База данных не инициализирована")
    return _database


def init_database(database_url: str, echo: bool = False) -> Database:
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
