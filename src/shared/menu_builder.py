from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional, Dict, Any


class MenuBuilder:
    """Строитель меню для устранения дублирования кода"""

    @staticmethod
    def crud_menu(
        title: str,
        create_callback: str,
        list_callback: str,
        back_callback: str = "main",
    ) -> dict:
        """Стандартное CRUD меню (Создать/Список/Назад)"""
        return {
            "text": f"📋 <b>{title}</b>\n\nВыберите действие:",
            "keyboard": InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ Создать", callback_data=create_callback
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="📋 Список", callback_data=list_callback
                        )
                    ],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)],
                ]
            ),
        }

    @staticmethod
    def confirmation_menu(
        text: str, confirm_callback: str, cancel_callback: str
    ) -> dict:
        """Меню подтверждения действия"""
        return {
            "text": text,
            "keyboard": InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Да", callback_data=confirm_callback
                        ),
                        InlineKeyboardButton(
                            text="❌ Нет", callback_data=cancel_callback
                        ),
                    ]
                ]
            ),
        }

    @staticmethod
    def back_menu(text: str, back_callback: str) -> dict:
        """Простое меню только с кнопкой Назад"""
        return {
            "text": text,
            "keyboard": InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)]
                ]
            ),
        }
