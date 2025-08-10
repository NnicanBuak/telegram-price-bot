from typing import List, Optional, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .base import BaseKeyboard


class ConfirmationKeyboard(BaseKeyboard):
    """Клавиатуры для подтверждения действий"""

    @staticmethod
    def create_yes_no(
        yes_text: str = "✅ Да",
        no_text: str = "❌ Нет",
        yes_callback: str = "confirm_yes",
        no_callback: str = "confirm_no",
        additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None,
    ) -> InlineKeyboardMarkup:
        """Создать стандартную клавиатуру подтверждения Да/Нет"""
        buttons = [
            [
                InlineKeyboardButton(text=yes_text, callback_data=yes_callback),
                InlineKeyboardButton(text=no_text, callback_data=no_callback),
            ]
        ]

        if additional_buttons:
            buttons.extend(additional_buttons)

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_confirmation_with_back(
        confirm_text: str = "✅ Подтвердить",
        cancel_text: str = "❌ Отмена",
        back_text: str = "◀️ Назад",
        confirm_callback: str = "confirm",
        cancel_callback: str = "cancel",
        back_callback: str = "back",
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру подтверждения с кнопкой назад"""
        buttons = [
            [
                InlineKeyboardButton(text=confirm_text, callback_data=confirm_callback),
                InlineKeyboardButton(text=cancel_text, callback_data=cancel_callback),
            ],
            [InlineKeyboardButton(text=back_text, callback_data=back_callback)],
        ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_delete_confirmation(
        item_name: str = "",
        delete_callback: str = "delete_confirm",
        cancel_callback: str = "delete_cancel",
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру подтверждения удаления"""
        if item_name:
            delete_text = f"🗑️ Удалить '{item_name}'"
        else:
            delete_text = "🗑️ Удалить"

        buttons = [
            [
                InlineKeyboardButton(text=delete_text, callback_data=delete_callback),
                InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback),
            ]
        ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_multi_choice(
        choices: Dict[str, str],
        cancel_text: str = "❌ Отмена",
        cancel_callback: str = "cancel",
        columns: int = 1,
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру выбора из нескольких вариантов"""
        choice_items = [
            {"text": text, "callback_data": callback}
            for text, callback in choices.items()
        ]

        def item_to_button(item):
            return InlineKeyboardButton(
                text=item["text"], callback_data=item["callback_data"]
            )

        button_rows = BaseKeyboard.create_columns_layout(
            choice_items, columns, item_to_button
        )

        # Добавляем кнопку отмены
        button_rows.append(
            [InlineKeyboardButton(text=cancel_text, callback_data=cancel_callback)]
        )

        return InlineKeyboardMarkup(inline_keyboard=button_rows)


class ActionConfirmation:
    """Специализированные подтверждения для различных действий"""

    @staticmethod
    def create_save_confirmation(
        save_callback: str = "save_confirm",
        discard_callback: str = "save_discard",
        continue_callback: str = "save_continue",
    ) -> InlineKeyboardMarkup:
        """Подтверждение сохранения изменений"""
        buttons = [
            [
                InlineKeyboardButton(text="💾 Сохранить", callback_data=save_callback),
                InlineKeyboardButton(text="🗑️ Отменить", callback_data=discard_callback),
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Продолжить редактирование", callback_data=continue_callback
                )
            ],
        ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_overwrite_confirmation(
        overwrite_callback: str = "overwrite_confirm",
        rename_callback: str = "overwrite_rename",
        cancel_callback: str = "overwrite_cancel",
    ) -> InlineKeyboardMarkup:
        """Подтверждение перезаписи файла/элемента"""
        buttons = [
            [
                InlineKeyboardButton(
                    text="🔄 Перезаписать", callback_data=overwrite_callback
                ),
                InlineKeyboardButton(
                    text="📝 Переименовать", callback_data=rename_callback
                ),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)],
        ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_publish_confirmation(
        publish_callback: str = "publish_confirm",
        draft_callback: str = "publish_draft",
        cancel_callback: str = "publish_cancel",
    ) -> InlineKeyboardMarkup:
        """Подтверждение публикации"""
        buttons = [
            [
                InlineKeyboardButton(
                    text="📢 Опубликовать", callback_data=publish_callback
                ),
                InlineKeyboardButton(
                    text="📝 Сохранить как черновик", callback_data=draft_callback
                ),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)],
        ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_reset_confirmation(
        reset_callback: str = "reset_confirm",
        backup_callback: str = "reset_backup",
        cancel_callback: str = "reset_cancel",
    ) -> InlineKeyboardMarkup:
        """Подтверждение сброса настроек"""
        buttons = [
            [
                InlineKeyboardButton(text="🔄 Сбросить", callback_data=reset_callback),
                InlineKeyboardButton(
                    text="💾 Создать резервную копию", callback_data=backup_callback
                ),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)],
        ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)


class ConditionalConfirmation:
    """Условные подтверждения с дополнительной логикой"""

    @staticmethod
    def create_conditional_delete(
        has_dependencies: bool = False,
        force_delete_callback: str = "force_delete",
        safe_delete_callback: str = "safe_delete",
        cancel_callback: str = "delete_cancel",
    ) -> InlineKeyboardMarkup:
        """Условное подтверждение удаления с зависимостями"""
        if has_dependencies:
            buttons = [
                [
                    InlineKeyboardButton(
                        text="⚠️ Принудительно удалить",
                        callback_data=force_delete_callback,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔗 Удалить связи и удалить",
                        callback_data=safe_delete_callback,
                    )
                ],
                [InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)],
            ]
        else:
            buttons = [
                [
                    InlineKeyboardButton(
                        text="🗑️ Удалить", callback_data=safe_delete_callback
                    ),
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data=cancel_callback
                    ),
                ]
            ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_permission_request(
        request_callback: str = "permission_request",
        skip_callback: str = "permission_skip",
        cancel_callback: str = "permission_cancel",
    ) -> InlineKeyboardMarkup:
        """Запрос разрешения на действие"""
        buttons = [
            [
                InlineKeyboardButton(
                    text="🔑 Запросить доступ", callback_data=request_callback
                ),
                InlineKeyboardButton(text="⏭️ Пропустить", callback_data=skip_callback),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)],
        ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)


class TimedConfirmation:
    """Подтверждения с временными ограничениями"""

    @staticmethod
    def create_timed_action(
        action_text: str,
        action_callback: str,
        time_left: int,
        cancel_callback: str = "timed_cancel",
    ) -> InlineKeyboardMarkup:
        """Создать подтверждение с оставшимся временем"""
        time_text = f"⏱️ {action_text} ({time_left}с)"

        buttons = [
            [
                InlineKeyboardButton(text=time_text, callback_data=action_callback),
                InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback),
            ]
        ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_countdown_warning(
        warning_text: str,
        proceed_callback: str = "countdown_proceed",
        abort_callback: str = "countdown_abort",
    ) -> InlineKeyboardMarkup:
        """Предупреждение с обратным отсчётом"""
        buttons = [
            [InlineKeyboardButton(text=f"⚠️ {warning_text}", callback_data="noop")],
            [
                InlineKeyboardButton(
                    text="✅ Продолжить", callback_data=proceed_callback
                ),
                InlineKeyboardButton(text="🛑 Прервать", callback_data=abort_callback),
            ],
        ]

        return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_simple_confirmation(
    message: str, confirm_callback: str = "confirm", cancel_callback: str = "cancel"
) -> tuple[str, InlineKeyboardMarkup]:
    """
    Удобная функция для создания простого подтверждения

    Returns:
        tuple: (message, keyboard)
    """
    keyboard = ConfirmationKeyboard.create_yes_no(
        yes_callback=confirm_callback, no_callback=cancel_callback
    )
    return message, keyboard


def create_deletion_warning(
    item_name: str,
    delete_callback: str = "delete_confirm",
    cancel_callback: str = "delete_cancel",
) -> tuple[str, InlineKeyboardMarkup]:
    """
    Создать предупреждение об удалении

    Returns:
        tuple: (warning_message, keyboard)
    """
    message = (
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"Вы действительно хотите удалить: <b>{item_name}</b>?\n\n"
        f"<i>Это действие нельзя отменить!</i>"
    )

    keyboard = ConfirmationKeyboard.create_delete_confirmation(
        item_name=item_name,
        delete_callback=delete_callback,
        cancel_callback=cancel_callback,
    )

    return message, keyboard
