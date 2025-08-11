"""
Модуль клавиатур для системы меню
"""

from .base import BaseKeyboard, MenuKeyboard, UtilityKeyboards, NavigationKeyboards
from .paginated import (
    PaginatedKeyboard,
    ListKeyboard,
    SearchKeyboard,
    create_paginated_list,
)
from .confirmation import (
    ConfirmationKeyboard,
    ActionConfirmation,
    ConditionalConfirmation,
    TimedConfirmation,
    create_simple_confirmation,
    create_deletion_warning,
)
from .crud import (
    CrudKeyboard,
    FormKeyboard,
    BulkActionKeyboard,
    StatusKeyboard,
    create_entity_menu,
    create_item_menu,
)

__all__ = [
    # Базовые клавиатуры
    "BaseKeyboard",
    "MenuKeyboard",
    "UtilityKeyboards",
    "NavigationKeyboards",
    # Пагинированные клавиатуры
    "PaginatedKeyboard",
    "ListKeyboard",
    "SearchKeyboard",
    "create_paginated_list",
    # Клавиатуры подтверждения
    "ConfirmationKeyboard",
    "ActionConfirmation",
    "ConditionalConfirmation",
    "TimedConfirmation",
    "create_simple_confirmation",
    "create_deletion_warning",
    # CRUD клавиатуры
    "CrudKeyboard",
    "FormKeyboard",
    "BulkActionKeyboard",
    "StatusKeyboard",
    "create_entity_menu",
    "create_item_menu",
]
