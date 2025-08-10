from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .constants import TemplateActions
from .models import TemplateResponse


class TemplateKeyboards:
    """Клавиатуры для шаблонов"""

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Главное меню шаблонов"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Создать", callback_data=TemplateActions.CREATE
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Список", callback_data=TemplateActions.LIST
                    )
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="main")],
            ]
        )

    @staticmethod
    def template_list(templates: List[TemplateResponse]) -> InlineKeyboardMarkup:
        """Список шаблонов"""
        buttons = []

        for template in templates:
            icon = "📎" if template.has_file else "📄"
            name = (
                template.name[:30] + "..." if len(template.name) > 30 else template.name
            )
            buttons.append(
                [
                    InlineKeyboardButton(
                        text=f"{icon} {name}",
                        callback_data=TemplateActions.VIEW.format(template.id),
                    )
                ]
            )

        buttons.extend(
            [
                [
                    InlineKeyboardButton(
                        text="➕ Создать", callback_data=TemplateActions.CREATE
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ Назад", callback_data=TemplateActions.MENU
                    )
                ],
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def template_view(template_id: int) -> InlineKeyboardMarkup:
        """Просмотр шаблона"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑️ Удалить",
                        callback_data=TemplateActions.DELETE.format(template_id),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ К списку", callback_data=TemplateActions.LIST
                    )
                ],
            ]
        )

    @staticmethod
    def create_flow() -> InlineKeyboardMarkup:
        """Клавиатура процесса создания"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="◀️ Назад", callback_data=TemplateActions.MENU
                    )
                ]
            ]
        )

    @staticmethod
    def file_options() -> InlineKeyboardMarkup:
        """Опции для файла"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏭ Пропустить", callback_data=TemplateActions.SKIP_FILE
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data=TemplateActions.MENU
                    )
                ],
            ]
        )

    @staticmethod
    def empty_list() -> InlineKeyboardMarkup:
        """Пустой список шаблонов"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Создать", callback_data=TemplateActions.CREATE
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ Назад", callback_data=TemplateActions.MENU
                    )
                ],
            ]
        )


class TemplateTexts:
    """Тексты для шаблонов"""

    @staticmethod
    def menu_description() -> str:
        """Описание меню шаблонов"""
        return (
            "📄 <b>Управление шаблонами</b>\n\n"
            "Создавайте и управляйте шаблонами сообщений для рассылки.\n"
            "Выберите действие:"
        )

    @staticmethod
    def list_header(count: int) -> str:
        """Заголовок списка шаблонов"""
        return (
            f"📄 <b>Список шаблонов</b>\n\n"
            f"📊 Найдено: {count}\n\n"
            "Выберите шаблон для просмотра:"
        )

    @staticmethod
    def empty_list() -> str:
        """Сообщение о пустом списке"""
        return (
            "📄 <b>Список шаблонов</b>\n\n"
            "❌ Шаблоны не найдены\n\n"
            "Создайте первый шаблон для начала работы."
        )

    @staticmethod
    def create_name_prompt() -> str:
        """Запрос названия при создании"""
        return (
            "➕ <b>Создание шаблона</b>\n\n"
            "Введите название шаблона (3-100 символов):\n\n"
            '<i>Например: "Прайс-лист Декабрь" или "Акция недели"</i>'
        )

    @staticmethod
    def create_text_prompt(name: str) -> str:
        """Запрос текста при создании"""
        return (
            f"✅ <b>Название:</b> {name}\n\n"
            "Теперь введите текст шаблона (10-4000 символов):\n\n"
            "<i>Поддерживается форматирование Telegram</i>"
        )

    @staticmethod
    def create_file_prompt() -> str:
        """Запрос файла при создании"""
        return (
            "✅ <b>Текст принят!</b>\n\n"
            "Хотите прикрепить файл?\n"
            "Отправьте фото или документ, либо пропустите этот шаг:"
        )

    @staticmethod
    def template_created(template: TemplateResponse) -> str:
        """Сообщение о созданном шаблоне"""
        file_info = ""
        if template.has_file:
            file_type_text = "Фото" if template.file_type == "photo" else "Документ"
            file_info = f"\n📎 <b>Файл:</b> {file_type_text}"

        return (
            f"✅ <b>Шаблон создан!</b>\n\n"
            f"🔢 <b>ID:</b> {template.id}\n"
            f"📝 <b>Название:</b> {template.name}{file_info}"
        )

    @staticmethod
    def template_details(template: TemplateResponse) -> str:
        """Детали шаблона"""
        file_info = ""
        if template.has_file:
            file_type_text = "Фото" if template.file_type == "photo" else "Документ"
            file_info = f"\n📎 <b>Файл:</b> {file_type_text}"

        text_preview = (
            template.text[:200] + "..." if len(template.text) > 200 else template.text
        )

        return (
            f"📄 <b>Шаблон #{template.id}</b>\n\n"
            f"📝 <b>Название:</b> {template.name}\n\n"
            f"📄 <b>Текст:</b>\n{text_preview}{file_info}\n\n"
            f"📅 <b>Создан:</b> {template.created_at}"
        )
