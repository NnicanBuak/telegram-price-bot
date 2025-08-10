from typing import List, Optional, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .base import BaseKeyboard
from .confirmation import ConfirmationKeyboard


class CrudKeyboard(BaseKeyboard):
    """Клавиатуры для CRUD операций"""

    @staticmethod
    def create_main_menu(
        entity_name: str,
        create_callback: str = "create",
        list_callback: str = "list",
        search_callback: str = "search",
        back_callback: str = "back",
        show_search: bool = True,
    ) -> tuple[str, InlineKeyboardMarkup]:
        """
        Создать главное CRUD меню

        Returns:
            tuple: (menu_text, keyboard)
        """
        text = f"📋 <b>Управление {entity_name}</b>\n\nВыберите действие:"

        buttons = [
            [InlineKeyboardButton(text="➕ Создать", callback_data=create_callback)],
            [InlineKeyboardButton(text="📋 Список", callback_data=list_callback)],
        ]

        if show_search:
            buttons.append(
                [InlineKeyboardButton(text="🔍 Поиск", callback_data=search_callback)]
            )

        buttons.append(
            [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return text, keyboard

    @staticmethod
    def create_item_actions(
        item_name: str,
        view_callback: str = "view",
        edit_callback: str = "edit",
        copy_callback: str = "copy",
        delete_callback: str = "delete",
        back_callback: str = "back",
        additional_actions: Optional[Dict[str, str]] = None,
    ) -> tuple[str, InlineKeyboardMarkup]:
        """
        Создать меню действий для элемента

        Returns:
            tuple: (menu_text, keyboard)
        """
        text = f"📄 <b>{item_name}</b>\n\nДоступные действия:"

        buttons = [
            [
                InlineKeyboardButton(text="👁️ Просмотр", callback_data=view_callback),
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data=edit_callback
                ),
            ],
            [
                InlineKeyboardButton(text="📋 Копировать", callback_data=copy_callback),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=delete_callback),
            ],
        ]

        # Дополнительные действия
        if additional_actions:
            for text_btn, callback in additional_actions.items():
                buttons.append(
                    [InlineKeyboardButton(text=text_btn, callback_data=callback)]
                )

        buttons.append(
            [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return text, keyboard

    @staticmethod
    def create_edit_menu(
        item_name: str,
        edit_fields: Dict[str, str],
        save_callback: str = "save",
        preview_callback: str = "preview",
        cancel_callback: str = "cancel",
    ) -> tuple[str, InlineKeyboardMarkup]:
        """
        Создать меню редактирования

        Args:
            item_name: Название элемента
            edit_fields: Словарь {название_поля: callback_data}

        Returns:
            tuple: (menu_text, keyboard)
        """
        text = f"✏️ <b>Редактирование: {item_name}</b>\n\nВыберите поле для изменения:"

        buttons = []

        # Поля для редактирования
        for field_name, callback_data in edit_fields.items():
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"📝 {field_name}", callback_data=callback_data
                    )
                ]
            )

        # Действия
        buttons.extend(
            [
                [
                    InlineKeyboardButton(
                        text="💾 Сохранить", callback_data=save_callback
                    ),
                    InlineKeyboardButton(
                        text="👁️ Предварительный просмотр",
                        callback_data=preview_callback,
                    ),
                ],
                [InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)],
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return text, keyboard

    @staticmethod
    def create_list_toolbar(
        sort_callback: str = "sort",
        filter_callback: str = "filter",
        export_callback: str = "export",
        refresh_callback: str = "refresh",
        show_export: bool = True,
    ) -> List[InlineKeyboardButton]:
        """Создать панель инструментов для списка"""
        toolbar = [
            InlineKeyboardButton(text="🔄 Обновить", callback_data=refresh_callback),
            InlineKeyboardButton(text="📊 Сортировка", callback_data=sort_callback),
            InlineKeyboardButton(text="🔍 Фильтр", callback_data=filter_callback),
        ]

        if show_export:
            toolbar.append(
                InlineKeyboardButton(text="📤 Экспорт", callback_data=export_callback)
            )

        return toolbar


class FormKeyboard:
    """Клавиатуры для работы с формами"""

    @staticmethod
    def create_form_navigation(
        current_step: int,
        total_steps: int,
        next_callback: str = "form_next",
        prev_callback: str = "form_prev",
        save_callback: str = "form_save",
        cancel_callback: str = "form_cancel",
    ) -> InlineKeyboardMarkup:
        """Создать навигацию по форме"""
        buttons = []

        # Навигация между шагами
        nav_row = []
        if current_step > 1:
            nav_row.append(
                InlineKeyboardButton(text="◀️ Назад", callback_data=prev_callback)
            )

        # Информация о шаге
        nav_row.append(
            InlineKeyboardButton(
                text=f"Шаг {current_step}/{total_steps}", callback_data="noop"
            )
        )

        if current_step < total_steps:
            nav_row.append(
                InlineKeyboardButton(text="Далее ▶️", callback_data=next_callback)
            )

        buttons.append(nav_row)

        # Действия
        action_row = []
        if current_step == total_steps:
            action_row.append(
                InlineKeyboardButton(text="💾 Сохранить", callback_data=save_callback)
            )

        action_row.append(
            InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)
        )

        buttons.append(action_row)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_field_input(
        field_name: str,
        field_type: str,
        skip_callback: str = "field_skip",
        clear_callback: str = "field_clear",
        help_callback: str = "field_help",
        allow_skip: bool = False,
    ) -> tuple[str, InlineKeyboardMarkup]:
        """
        Создать интерфейс для ввода поля

        Returns:
            tuple: (prompt_text, keyboard)
        """
        text = f"📝 <b>Введите {field_name}</b>\n\n"

        if field_type == "text":
            text += "Отправьте текстовое сообщение"
        elif field_type == "number":
            text += "Отправьте число"
        elif field_type == "file":
            text += "Отправьте файл"
        elif field_type == "photo":
            text += "Отправьте фотографию"
        else:
            text += "Отправьте данные"

        buttons = []

        # Дополнительные действия
        action_row = [
            InlineKeyboardButton(text="🔄 Очистить", callback_data=clear_callback),
            InlineKeyboardButton(text="❓ Справка", callback_data=help_callback),
        ]

        if allow_skip:
            action_row.append(
                InlineKeyboardButton(text="⏭️ Пропустить", callback_data=skip_callback)
            )

        buttons.append(action_row)

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return text, keyboard


class BulkActionKeyboard:
    """Клавиатуры для массовых операций"""

    @staticmethod
    def create_bulk_selection(
        total_items: int,
        selected_count: int,
        select_all_callback: str = "select_all",
        deselect_all_callback: str = "deselect_all",
        invert_selection_callback: str = "invert_selection",
    ) -> List[InlineKeyboardButton]:
        """Создать кнопки для массового выбора"""
        return [
            InlineKeyboardButton(
                text=f"☑️ Выбрать все ({total_items})", callback_data=select_all_callback
            ),
            InlineKeyboardButton(
                text=f"☐ Снять выбор", callback_data=deselect_all_callback
            ),
            InlineKeyboardButton(
                text="🔄 Инвертировать", callback_data=invert_selection_callback
            ),
        ]

    @staticmethod
    def create_bulk_actions(
        selected_count: int,
        actions: Dict[str, str],
        cancel_callback: str = "bulk_cancel",
    ) -> InlineKeyboardMarkup:
        """Создать меню массовых действий"""
        if selected_count == 0:
            text_button = "Выберите элементы для действий"
            buttons = [[InlineKeyboardButton(text=text_button, callback_data="noop")]]
        else:
            buttons = []
            for action_text, callback_data in actions.items():
                action_with_count = f"{action_text} ({selected_count})"
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=action_with_count, callback_data=callback_data
                        )
                    ]
                )

        buttons.append(
            [InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)]
        )

        return InlineKeyboardMarkup(inline_keyboard=buttons)


class StatusKeyboard:
    """Клавиатуры для управления статусами"""

    @staticmethod
    def create_status_change(
        current_status: str,
        available_statuses: Dict[str, str],
        status_callback_prefix: str = "status",
        back_callback: str = "back",
    ) -> tuple[str, InlineKeyboardMarkup]:
        """
        Создать меню изменения статуса

        Returns:
            tuple: (status_text, keyboard)
        """
        text = f"📊 <b>Текущий статус:</b> {current_status}\n\nВыберите новый статус:"

        buttons = []
        for status_name, status_value in available_statuses.items():
            if status_value != current_status:  # Не показываем текущий статус
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"📌 {status_name}",
                            callback_data=f"{status_callback_prefix}_{status_value}",
                        )
                    ]
                )

        buttons.append(
            [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        return text, keyboard


def create_entity_menu(
    entity_name: str, entity_name_plural: str = None
) -> tuple[str, InlineKeyboardMarkup]:
    """
    Удобная функция для создания стандартного CRUD меню

    Returns:
        tuple: (menu_text, keyboard)
    """
    if entity_name_plural is None:
        entity_name_plural = entity_name + "ы"

    return CrudKeyboard.create_main_menu(
        entity_name=entity_name_plural,
        create_callback=f"create_{entity_name}",
        list_callback=f"list_{entity_name}",
        search_callback=f"search_{entity_name}",
        back_callback="main",
    )


def create_item_menu(
    entity_name: str, item_id: int, item_name: str = None
) -> tuple[str, InlineKeyboardMarkup]:
    """
    Удобная функция для создания меню действий с элементом

    Returns:
        tuple: (menu_text, keyboard)
    """
    display_name = item_name or f"{entity_name} #{item_id}"

    return CrudKeyboard.create_item_actions(
        item_name=display_name,
        view_callback=f"view_{entity_name}_{item_id}",
        edit_callback=f"edit_{entity_name}_{item_id}",
        copy_callback=f"copy_{entity_name}_{item_id}",
        delete_callback=f"delete_{entity_name}_{item_id}",
        back_callback=f"list_{entity_name}",
    )
