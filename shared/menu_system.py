"""
Расширяемая система меню для Telegram ботов
Перенесена в shared для переиспользования
"""

import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types, BaseMiddleware


@dataclass
class MenuItem:
    """Элемент меню"""

    id: str
    text: str
    icon: str = ""
    callback_data: str = ""
    url: str = ""
    admin_only: bool = False
    visible: bool = True
    order: int = 0
    parent: Optional["Menu"] = field(default=None, init=False)


@dataclass
class Menu:
    """Меню с элементами"""

    id: str
    title: str
    description: str = ""
    back_to: Optional[str] = None
    back_button: bool = True
    columns: int = 1
    admin_only: bool = False
    items: List[MenuItem] = field(default_factory=list)

    def add_item(self, item: MenuItem) -> "Menu":
        """Добавить элемент в меню"""
        item.parent = self
        self.items.append(item)
        self.items.sort(key=lambda x: x.order)
        return self

    def remove_item(self, item_id: str) -> bool:
        """Удалить элемент из меню"""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                return True
        return False

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        """Получить элемент по ID"""
        for item in self.items:
            if item.id == item_id:
                return item
        return None


class MenuManager:
    """Менеджер системы меню с полным API"""

    def __init__(self, admin_ids: List[int]):
        self.admin_ids = admin_ids
        self.menus: Dict[str, Menu] = {}
        self._handlers: Dict[str, Callable] = {}
        self._dynamic_handlers: List[Callable] = []
        self._user_history: Dict[int, List[str]] = {}  # История навигации
        self._current_menu: Dict[int, str] = {}  # Текущее меню пользователя
        self._callbacks: Dict[str, Callable] = {}  # Зарегистрированные колбэки

    def register_menu(self, menu: Menu):
        """Регистрация меню"""
        self.menus[menu.id] = menu

    def unregister_menu(self, menu_id: str) -> bool:
        """Удаление меню"""
        if menu_id in self.menus:
            del self.menus[menu_id]
            return True
        return False

    def get_menu(self, menu_id: str, user_id: Optional[int] = None) -> Optional[Menu]:
        """Получить меню по ID"""
        menu = self.menus.get(menu_id)
        if (
            menu
            and user_id is not None
            and menu.admin_only
            and not self.is_admin(user_id)
        ):
            return None
        return menu

    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in self.admin_ids

    # ========== МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ С ТЕСТАМИ ==========

    def set_current_menu(self, user_id: int, menu_id: str):
        """Установить текущее меню пользователя"""
        self._current_menu[user_id] = menu_id

        # Добавляем в историю
        if user_id not in self._user_history:
            self._user_history[user_id] = []

        # Избегаем дублирования в истории
        if (
            not self._user_history[user_id]
            or self._user_history[user_id][-1] != menu_id
        ):
            self._user_history[user_id].append(menu_id)

        # Ограничиваем историю (последние 10 меню)
        if len(self._user_history[user_id]) > 10:
            self._user_history[user_id] = self._user_history[user_id][-10:]

    def get_current_menu(self, user_id: int) -> Optional[str]:
        """Получить текущее меню пользователя"""
        return self._current_menu.get(user_id)

    def get_menu_history(self, user_id: int) -> List[str]:
        """Получить историю навигации пользователя"""
        return self._user_history.get(user_id, [])

    def clear_history(self, user_id: int):
        """Очистить историю пользователя"""
        self._user_history.pop(user_id, None)
        self._current_menu.pop(user_id, None)

    def build_keyboard(
        self, menu_id: str, user_id: int, **context
    ) -> InlineKeyboardMarkup:
        """Построить клавиатуру меню"""
        menu = self.get_menu(menu_id, user_id)
        if not menu:
            return InlineKeyboardMarkup(inline_keyboard=[])

        return self._build_keyboard(menu, user_id, **context)

    async def navigate_to(
        self, menu_id: str, callback: types.CallbackQuery, **context
    ) -> bool:
        """Навигация к меню"""
        user_id = callback.from_user.id

        # Проверяем доступ к меню
        menu = self.get_menu(menu_id, user_id)
        if not menu:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return False

        # Обновляем текущее меню
        self.set_current_menu(user_id, menu_id)

        # Рендерим меню
        text, keyboard = self.render_menu(menu_id, user_id, **context)

        try:
            await callback.message.edit_text(
                text, reply_markup=keyboard, parse_mode="HTML"
            )
            await callback.answer()
            return True
        except Exception as e:
            await callback.answer(f"Ошибка навигации: {str(e)}", show_alert=True)
            return False

    def register_callback(self, callback_data: str, handler: Callable):
        """Регистрация обработчика для callback_data"""
        self._callbacks[callback_data] = handler

    # ========== ОСНОВНЫЕ МЕТОДЫ ==========

    def register_handler(self, callback_data: str, handler: Callable):
        """Регистрация обработчика для callback_data"""
        self._handlers[callback_data] = handler

    def register_dynamic_handler(self, handler: Callable):
        """Регистрация динамического обработчика"""
        self._dynamic_handlers.append(handler)

    async def handle_callback(self, callback: types.CallbackQuery, **kwargs) -> bool:
        """Обработка callback запроса"""
        callback_data = callback.data

        # Проверяем зарегистрированные обработчики
        if callback_data in self._handlers:
            await self._handlers[callback_data](callback, **kwargs)
            return True

        if callback_data in self._callbacks:
            await self._callbacks[callback_data](callback, **kwargs)
            return True

        # Проверяем динамические обработчики
        for handler in self._dynamic_handlers:
            try:
                result = await handler(callback, **kwargs)
                if result:
                    return True
            except Exception:
                continue

        return False

    def render_menu(
        self, menu_id: str, user_id: int, **context
    ) -> tuple[str, InlineKeyboardMarkup]:
        """Отрендерить меню для пользователя"""
        menu = self.get_menu(menu_id, user_id)
        if not menu:
            return "❌ Меню не найдено", InlineKeyboardMarkup(inline_keyboard=[])

        # Формируем текст
        text = f"{menu.title}"
        if menu.description:
            text += f"\n\n{menu.description}"

        # Формируем клавиатуру
        keyboard = self._build_keyboard(menu, user_id, **context)

        return text, keyboard

    def _build_keyboard(
        self, menu: Menu, user_id: int, **context
    ) -> InlineKeyboardMarkup:
        """Построить клавиатуру меню"""
        buttons = []

        # Фильтруем видимые элементы
        visible_items = [
            item
            for item in menu.items
            if item.visible and (not item.admin_only or self.is_admin(user_id))
        ]

        # Группируем кнопки по столбцам
        for i in range(0, len(visible_items), menu.columns):
            row = []
            for j in range(menu.columns):
                if i + j < len(visible_items):
                    item = visible_items[i + j]
                    button_text = f"{item.icon} {item.text}".strip()

                    if item.url:
                        button = InlineKeyboardButton(text=button_text, url=item.url)
                    else:
                        button = InlineKeyboardButton(
                            text=button_text, callback_data=item.callback_data
                        )

                    row.append(button)

            if row:
                buttons.append(row)

        # Добавляем кнопку "Назад"
        if menu.back_button and menu.back_to:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="◀️ Назад", callback_data=f"menu_{menu.back_to}"
                    )
                ]
            )

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    # ========== ДИНАМИЧЕСКИЕ МЕНЮ ==========

    async def add_dynamic_menu(
        self, menu_id: str, title: str, items: List[dict], **kwargs
    ):
        """Добавить динамическое меню"""
        menu = Menu(
            id=menu_id,
            title=title,
            description=kwargs.get("description", ""),
            back_to=kwargs.get("back_to"),
            columns=kwargs.get("columns", 1),
        )

        for item_data in items:
            item = MenuItem(
                id=item_data["id"],
                text=item_data["text"],
                icon=item_data.get("icon", ""),
                callback_data=item_data.get("callback_data", ""),
                url=item_data.get("url", ""),
                admin_only=item_data.get("admin_only", False),
                order=item_data.get("order", 0),
            )
            menu.add_item(item)

        self.register_menu(menu)

    # ========== ЭКСПОРТ/ИМПОРТ ==========

    def export_menu_config(self) -> str:
        """Экспорт конфигурации меню в JSON"""
        config = {}
        for menu_id, menu in self.menus.items():
            config[menu_id] = {
                "title": menu.title,
                "description": menu.description,
                "back_to": menu.back_to,
                "back_button": menu.back_button,
                "columns": menu.columns,
                "admin_only": menu.admin_only,
                "items": [
                    {
                        "id": item.id,
                        "text": item.text,
                        "icon": item.icon,
                        "callback_data": item.callback_data,
                        "url": item.url,
                        "admin_only": item.admin_only,
                        "visible": item.visible,
                        "order": item.order,
                    }
                    for item in menu.items
                ],
            }
        return json.dumps(config, ensure_ascii=False, indent=2)

    def import_menu_config(self, config_data: str):
        """Импорт конфигурации меню из JSON"""
        if isinstance(config_data, str):
            config = json.loads(config_data)
        else:
            config = config_data

        for menu_id, menu_data in config.items():
            menu = Menu(
                id=menu_id,
                title=menu_data["title"],
                description=menu_data.get("description", ""),
                back_to=menu_data.get("back_to"),
                back_button=menu_data.get("back_button", True),
                columns=menu_data.get("columns", 1),
                admin_only=menu_data.get("admin_only", False),
            )

            for item_data in menu_data.get("items", []):
                item = MenuItem(
                    id=item_data["id"],
                    text=item_data["text"],
                    icon=item_data.get("icon", ""),
                    callback_data=item_data.get("callback_data", ""),
                    url=item_data.get("url", ""),
                    admin_only=item_data.get("admin_only", False),
                    visible=item_data.get("visible", True),
                    order=item_data.get("order", 0),
                )
                menu.add_item(item)

            self.register_menu(menu)


# ========== MIDDLEWARE ==========


class MenuMiddleware(BaseMiddleware):
    """Middleware для системы меню"""

    def __init__(self, menu_manager: MenuManager, admin_ids: List[int]):
        self.menu_manager = menu_manager
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[types.Message, Dict[str, Any]], Any],
        event: types.Message | types.CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        """Обработка событий"""
        user_id = event.from_user.id

        # Проверка доступа для личных сообщений
        if hasattr(event, "chat") and event.chat.type == "private":
            if user_id not in self.admin_ids:
                # Отправляем сообщение об ограничении доступа
                if isinstance(event, types.Message):
                    await event.answer(
                        "❌ <b>Доступ запрещен</b>\n\n"
                        "Этот бот доступен только администраторам.\n"
                        "Обратитесь к администратору для получения доступа.",
                        parse_mode="HTML",
                    )
                else:
                    await event.answer("нет доступа", show_alert=True)
                return

        # Добавляем menu_manager в контекст
        data["menu_manager"] = self.menu_manager

        return await handler(event, data)


# ========== УТИЛИТЫ ==========


def create_pagination_keyboard(
    items: List[dict],
    page: int = 0,
    items_per_page: int = 5,
    callback_prefix: str = "page",
) -> List[List[InlineKeyboardButton]]:
    """Создать пагинированную клавиатуру"""
    buttons = []

    # Элементы текущей страницы
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]

    for item in page_items:
        button = InlineKeyboardButton(
            text=f"{item.get('icon', '')} {item['text']}".strip(),
            callback_data=item["callback_data"],
        )
        buttons.append([button])

    # Кнопки навигации
    nav_buttons = []
    total_pages = (len(items) + items_per_page - 1) // items_per_page

    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад", callback_data=f"{callback_prefix}_{page-1}"
            )
        )

    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ▶️", callback_data=f"{callback_prefix}_{page+1}"
            )
        )

    if nav_buttons:
        buttons.append(nav_buttons)

    return buttons


def create_settings_menu(admin_only: bool = True) -> Menu:
    """Создать меню настроек"""
    menu = Menu(
        id="settings",
        title="⚙️ <b>Настройки</b>",
        description="Конфигурация и управление ботом",
        back_to="main",
        admin_only=admin_only,
    )

    menu.add_item(
        MenuItem(
            id="backup",
            text="Резервная копия",
            icon="💾",
            callback_data="backup_create",
            admin_only=True,
            order=1,
        )
    )

    menu.add_item(
        MenuItem(
            id="logs",
            text="Логи",
            icon="📋",
            callback_data="logs_view",
            admin_only=True,
            order=2,
        )
    )

    menu.add_item(
        MenuItem(
            id="stats",
            text="Статистика",
            icon="📈",
            callback_data="stats_view",
            admin_only=True,
            order=3,
        )
    )

    return menu
