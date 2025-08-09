"""
Инициализация модуля database
Экспортирует основные классы для упрощения импортов
"""

from .database import Database, Template, ChatGroup, Mailing

__all__ = ["Database", "Template", "ChatGroup", "Mailing"]
