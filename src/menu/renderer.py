from typing import Dict, Any, List, Optional, Union, Callable
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)
from aiogram import Bot

from .models import (
    MenuConfig,
    MenuStructure,
    MenuButton,
    MenuResponse,
    ButtonType,
    NavigationState,
)


class MenuBuilder:
    """Строитель меню - основной компонент для создания меню"""

    def __init__(self, menu_id: str):
        self._config = MenuConfig(id=menu_id, title="")
        self._buttons: List[MenuButton] = []
        self._button_order = 0

    # === КОНФИГУРАЦИЯ МЕНЮ ===

    def title(self, title: str) -> "MenuBuilder":
        """Установить заголовок меню"""
        self._config.title = title
        return self

    def description(self, description: str) -> "MenuBuilder":
        """Установить описание меню"""
        self._config.description = description
        return self

    def columns(self, columns: int) -> "MenuBuilder":
        """Установить количество колонок"""
        self._config.columns = max(1, min(columns, 3))  # Ограничиваем 1-3
        return self

    def admin_only(self, admin_only: bool = True) -> "MenuBuilder":
        """Ограничить только для админов"""
        self._config.admin_only = admin_only
        return self

    def back_button(self, target_menu: str, text: str = "◀️ Назад") -> "MenuBuilder":
        """Настроить кнопку назад"""
        self._config.show_back_button = True
        self._config.back_target = target_menu
        self._config.back_button_text = text
        return self

    def no_back_button(self) -> "MenuBuilder":
        """Отключить кнопку назад"""
        self._config.show_back_button = False
        return self

    def metadata(self, **metadata) -> "MenuBuilder":
        """Добавить метаданные"""
        self._config.metadata.update(metadata)
        return self

    # === ДОБАВЛЕНИЕ КНОПОК ===

    def add_action(
        self, text: str, callback_data: str, icon: str = "", admin_only: bool = False
    ) -> "MenuBuilder":
        """Добавить кнопку действия"""
        button = MenuButton(
            text=text,
            button_type=ButtonType.ACTION,
            callback_data=callback_data,
            icon=icon,
            admin_only=admin_only,
            order=self._button_order,
        )
        self._buttons.append(button)
        self._button_order += 1
        return self

    def add_menu_link(
        self, text: str, target_menu: str, icon: str = "", admin_only: bool = False
    ) -> "MenuBuilder":
        """Добавить ссылку на другое меню"""
        button = MenuButton(
            text=text,
            button_type=ButtonType.MENU_LINK,
            callback_data=f"menu_{target_menu}",
            target_menu=target_menu,
            icon=icon,
            admin_only=admin_only,
            order=self._button_order,
        )
        self._buttons.append(button)
        self._button_order += 1
        return self

    def add_url(
        self, text: str, url: str, icon: str = "", admin_only: bool = False
    ) -> "MenuBuilder":
        """Добавить URL кнопку"""
        button = MenuButton(
            text=text,
            button_type=ButtonType.URL,
            url=url,
            icon=icon,
            admin_only=admin_only,
            order=self._button_order,
        )
        self._buttons.append(button)
        self._button_order += 1
        return self

    def add_confirm_cancel(
        self,
        confirm_text: str = "✅ Подтвердить",
        cancel_text: str = "❌ Отмена",
        confirm_callback: str = "confirm",
        cancel_callback: str = "cancel",
    ) -> "MenuBuilder":
        """Добавить кнопки подтверждения и отмены"""
        # Подтверждение
        confirm_btn = MenuButton(
            text=confirm_text,
            button_type=ButtonType.CONFIRM,
            callback_data=confirm_callback,
            order=self._button_order,
        )
        self._buttons.append(confirm_btn)
        self._button_order += 1

        # Отмена
        cancel_btn = MenuButton(
            text=cancel_text,
            button_type=ButtonType.CANCEL,
            callback_data=cancel_callback,
            order=self._button_order,
        )
        self._buttons.append(cancel_btn)
        self._button_order += 1

        return self

    def add_separator(self) -> "MenuBuilder":
        """Добавить разделитель (пустая строка)"""
        self._button_order += 10  # Пропускаем позиции для группировки
        return self

    def add_custom_button(self, button: MenuButton) -> "MenuBuilder":
        """Добавить кастомную кнопку"""
        button.order = self._button_order
        self._buttons.append(button)
        self._button_order += 1
        return self

    # === ПОСТРОЕНИЕ ===

    def build(self) -> MenuStructure:
        """Построить структуру меню"""
        if not self._config.title:
            raise ValueError("Меню должно иметь заголовок")

        structure = MenuStructure(config=self._config)

        # Добавляем все кнопки
        for button in self._buttons:
            structure.add_button(button)

        return structure


class MenuRenderer:
    """Рендерер меню в Telegram формат"""

    def __init__(self, admin_user_ids: List[int]):
        self.admin_user_ids = admin_user_ids
        self._custom_renderers: Dict[str, Callable] = {}

    def render(
        self, menu: MenuStructure, user_id: int, context: Dict[str, Any] = None
    ) -> MenuResponse:
        """Отрендерить меню для пользователя"""
        context = context or {}
        is_admin = user_id in self.admin_user_ids

        # Проверяем доступ к меню
        if menu.config.admin_only and not is_admin:
            return self._render_access_denied()

        # Кастомный рендерер
        if menu.config.id in self._custom_renderers:
            return self._custom_renderers[menu.config.id](menu, context)

        # Стандартный рендеринг
        text = self._render_text(menu, context)
        keyboard = self._render_keyboard(menu, is_admin)

        return MenuResponse(
            text=text, keyboard_markup=keyboard, parse_mode=menu.config.parse_mode
        )

    def _render_text(self, menu: MenuStructure, context: Dict[str, Any]) -> str:
        """Рендерить текст меню"""
        text = menu.config.title

        if menu.config.description:
            # Поддержка переменных в описании
            description = menu.config.description
            try:
                description = description.format(**context)
            except (KeyError, ValueError):
                pass  # Игнорируем ошибки форматирования
            text += f"\n\n{description}"

        return text

    def _render_keyboard(
        self, menu: MenuStructure, is_admin: bool
    ) -> InlineKeyboardMarkup:
        """Рендерить клавиатуру меню"""
        buttons = menu.get_visible_buttons(is_admin)

        if not buttons and not menu.config.show_back_button:
            return InlineKeyboardMarkup(inline_keyboard=[])

        # Группируем кнопки по колонкам
        rows = self._create_button_rows(buttons, menu.config.columns)

        # Добавляем кнопку назад
        if menu.config.show_back_button and menu.config.back_target:
            back_button = InlineKeyboardButton(
                text=menu.config.back_button_text,
                callback_data=f"menu_{menu.config.back_target}",
            )
            rows.append([back_button])

        return InlineKeyboardMarkup(inline_keyboard=rows)

    def _create_button_rows(
        self, buttons: List[MenuButton], columns: int
    ) -> List[List[InlineKeyboardButton]]:
        """Создать ряды кнопок"""
        rows = []

        # Специальная обработка для кнопок подтверждения
        confirm_cancel_buttons = []
        regular_buttons = []

        for button in buttons:
            if button.button_type in [ButtonType.CONFIRM, ButtonType.CANCEL]:
                confirm_cancel_buttons.append(button)
            else:
                regular_buttons.append(button)

        # Обычные кнопки в колонках
        for i in range(0, len(regular_buttons), columns):
            row = []
            for j in range(columns):
                if i + j < len(regular_buttons):
                    btn = regular_buttons[i + j]
                    telegram_btn = self._create_telegram_button(btn)
                    row.append(telegram_btn)

            if row:
                rows.append(row)

        # Кнопки подтверждения/отмены в одной строке
        if confirm_cancel_buttons:
            confirm_row = [
                self._create_telegram_button(btn) for btn in confirm_cancel_buttons
            ]
            rows.append(confirm_row)

        return rows

    def _create_telegram_button(self, button: MenuButton) -> InlineKeyboardButton:
        """Создать Telegram кнопку"""
        if button.button_type == ButtonType.URL:
            return InlineKeyboardButton(text=button.display_text, url=button.url)
        else:
            return InlineKeyboardButton(
                text=button.display_text, callback_data=button.callback_data
            )

    def _render_access_denied(self) -> MenuResponse:
        """Рендерить сообщение об отказе в доступе"""
        return MenuResponse(
            text="❌ <b>Доступ запрещён</b>\n\nУ вас нет прав для просмотра этого меню.",
            keyboard_markup=InlineKeyboardMarkup(inline_keyboard=[]),
        )

    def register_custom_renderer(
        self,
        menu_id: str,
        renderer: Callable[[MenuStructure, Dict[str, Any]], MenuResponse],
    ):
        """Зарегистрировать кастомный рендерер для меню"""
        self._custom_renderers[menu_id] = renderer


class MenuSender:
    """Отправщик меню в Telegram"""

    def __init__(self, renderer: MenuRenderer):
        self.renderer = renderer

    async def send_menu(
        self,
        menu: MenuStructure,
        target: Union[Message, CallbackQuery] = None,
        user_id: int = None,
        bot: Bot = None,
        chat_id: int = None,
        context: Dict[str, Any] = None,
    ) -> bool:
        """
        Отправить меню пользователю

        Поддерживает как событийную, так и программную отправку:
        - Событийная: передать target (Message/CallbackQuery) и user_id
        - Программная: передать bot, chat_id и user_id
        """
        try:
            # Определяем режим работы
            if target is not None:
                # Событийный режим
                if user_id is None:
                    user_id = (
                        target.from_user.id
                        if hasattr(target, "from_user")
                        else target.message.from_user.id
                    )

                response = self.renderer.render(menu, user_id, context)

                if isinstance(target, Message):
                    await target.answer(
                        text=response.text,
                        reply_markup=response.keyboard_markup,
                        parse_mode=response.parse_mode,
                    )
                elif isinstance(target, CallbackQuery):
                    await target.message.edit_text(
                        text=response.text,
                        reply_markup=response.keyboard_markup,
                        parse_mode=response.parse_mode,
                    )
                    await target.answer()

            elif bot is not None and chat_id is not None and user_id is not None:
                # Программный режим
                response = self.renderer.render(menu, user_id, context)

                await bot.send_message(
                    chat_id=chat_id,
                    text=response.text,
                    reply_markup=response.keyboard_markup,
                    parse_mode=response.parse_mode,
                )

            else:
                raise ValueError(
                    "Необходимо передать либо target и user_id (событийный режим), "
                    "либо bot, chat_id и user_id (программный режим)"
                )

            return True

        except Exception as e:
            # Логирование ошибки
            if isinstance(target, CallbackQuery):
                await target.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
            return False

    async def send_menu_to_chat(
        self,
        menu: MenuStructure,
        bot: Bot,
        chat_id: int,
        user_id: int = None,
        context: Dict[str, Any] = None,
    ) -> bool:
        """
        Программно отправить меню в чат
        """
        if user_id is None:
            user_id = chat_id

        return await self.send_menu(
            menu=menu, bot=bot, chat_id=chat_id, user_id=user_id, context=context
        )

    async def update_menu(
        self,
        menu: MenuStructure,
        callback: CallbackQuery,
        user_id: int,
        context: Dict[str, Any] = None,
    ) -> bool:
        """Обновить существующее меню"""
        return await self.send_menu(menu, callback, user_id, context=context)


# === ГОТОВЫЕ БИЛДЕРЫ ДЛЯ ЧАСТЫХ СЛУЧАЕВ ===


def create_crud_menu(
    menu_id: str,
    entity_name: str,
    create_callback: str = None,
    list_callback: str = None,
    back_target: str = "main",
) -> MenuBuilder:
    """Создать стандартное CRUD меню"""
    create_cb = create_callback or f"{menu_id}_create"
    list_cb = list_callback or f"{menu_id}_list"

    return (
        MenuBuilder(menu_id)
        .title(f"📋 <b>{entity_name}</b>")
        .description(f"Управление {entity_name.lower()}")
        .add_action("➕ Создать", create_cb)
        .add_action("📋 Список", list_cb)
        .back_button(back_target)
    )


def create_confirmation_menu(
    menu_id: str,
    title: str,
    confirm_callback: str = "confirm",
    cancel_callback: str = "cancel",
    back_target: str = None,
) -> MenuBuilder:
    """Создать меню подтверждения"""
    builder = (
        MenuBuilder(menu_id)
        .title(title)
        .add_confirm_cancel(
            confirm_callback=confirm_callback, cancel_callback=cancel_callback
        )
    )

    if back_target:
        builder.back_button(back_target)
    else:
        builder.no_back_button()

    return builder


def create_simple_menu(
    menu_id: str, title: str, description: str = "", back_target: str = "main"
) -> MenuBuilder:
    """Создать простое меню"""
    builder = MenuBuilder(menu_id).title(title)

    if description:
        builder.description(description)

    if back_target:
        builder.back_button(back_target)

    return builder
