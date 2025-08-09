"""
Абстрактная система меню для Telegram ботов
Предоставляет базовые классы и функциональность для создания интерактивных меню
"""

import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


@dataclass
class MenuItem:
    """Элемент меню"""

    id: str
    text: str
    callback_data: str
    icon: str = ""
    admin_only: bool = True
    visible: bool = True
    action: Optional[Callable] = None
    submenu: Optional[str] = None
    parent: Optional[str] = None
    row: Optional[int] = None


@dataclass
class Menu:
    """Меню"""

    id: str
    title: str
    description: str = ""
    back_to: Optional[str] = None
    back_button: bool = True
    columns: int = 1
    items: List[MenuItem] = field(default_factory=list)

    def add_item(self, item: MenuItem):
        """Добавить элемент в меню"""
        item.parent = self.id
        self.items.append(item)
        return self

    def remove_item(self, item_id: str):
        """Удалить элемент из меню"""
        self.items = [item for item in self.items if item.id != item_id]
        return self

    def clear_items(self):
        """Очистить все элементы"""
        self.items.clear()
        return self


class MenuManager:
    """Менеджер системы меню"""

    def __init__(self, admin_ids: List[int]):
        self.admin_ids = admin_ids
        self.menus: Dict[str, Menu] = {}
        self.current_menu: Dict[int, str] = {}
        self.menu_history: Dict[int, List[str]] = {}
        self._callbacks: Dict[str, Callable] = {}

    def register_menu(self, menu: Menu):
        """Регистрация меню"""
        self.menus[menu.id] = menu
        return menu

    def unregister_menu(self, menu_id: str):
        """Удаление меню"""
        self.menus.pop(menu_id, None)

    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in self.admin_ids

    def get_menu(self, menu_id: str, user_id: int) -> Optional[Menu]:
        """Получение меню с проверкой доступа"""
        if not self.is_admin(user_id):
            return None
        return self.menus.get(menu_id)

    def set_current_menu(self, user_id: int, menu_id: str):
        """Установка текущего меню"""
        self.current_menu[user_id] = menu_id

        # Обновляем историю
        if user_id not in self.menu_history:
            self.menu_history[user_id] = []

        self.menu_history[user_id].append(menu_id)

        # Ограничиваем историю 10 элементами
        if len(self.menu_history[user_id]) > 10:
            self.menu_history[user_id] = self.menu_history[user_id][-10:]

    def get_current_menu(self, user_id: int) -> Optional[str]:
        """Получение текущего меню"""
        return self.current_menu.get(user_id)

    def go_back(self, user_id: int) -> Optional[str]:
        """Возврат к предыдущему меню"""
        history = self.menu_history.get(user_id, [])
        if len(history) > 1:
            history.pop()  # Убираем текущее
            previous = history[-1]  # Берем предыдущее
            self.current_menu[user_id] = previous
            return previous
        return None

    def build_keyboard(self, menu: Menu, user_id: int) -> InlineKeyboardMarkup:
        """Построение клавиатуры для меню"""
        keyboard = []
        current_row = []

        for item in menu.items:
            # Проверяем видимость и права доступа
            if not item.visible:
                continue
            if item.admin_only and not self.is_admin(user_id):
                continue

            # Формируем текст кнопки
            button_text = f"{item.icon} {item.text}".strip()

            button = InlineKeyboardButton(
                text=button_text, callback_data=item.callback_data
            )

            current_row.append(button)

            # Проверяем, нужно ли создать новый ряд
            if len(current_row) >= menu.columns:
                keyboard.append(current_row)
                current_row = []

        # Добавляем оставшиеся кнопки
        if current_row:
            keyboard.append(current_row)

        # Добавляем кнопку "Назад"
        if menu.back_button and menu.back_to:
            back_button = InlineKeyboardButton(
                text="🔙 Назад", callback_data=f"menu_{menu.back_to}"
            )
            keyboard.append([back_button])

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    def render_menu(
        self, menu_id: str, user_id: int
    ) -> tuple[str, Optional[InlineKeyboardMarkup]]:
        """Рендеринг меню"""
        menu = self.get_menu(menu_id, user_id)
        if not menu:
            return "❌ Меню не найдено или нет доступа", None

        # Устанавливаем как текущее меню
        self.set_current_menu(user_id, menu_id)

        # Формируем текст
        text = menu.title
        if menu.description:
            text += f"\n\n{menu.description}"

        # Формируем клавиатуру
        keyboard = self.build_keyboard(menu, user_id)

        return text, keyboard

    async def navigate_to(self, menu_id: str, callback: CallbackQuery) -> bool:
        """Навигация к меню"""
        user_id = callback.from_user.id

        menu = self.get_menu(menu_id, user_id)
        if not menu:
            await callback.answer("Нет доступа к этому меню", show_alert=True)
            return False

        text, keyboard = self.render_menu(menu_id, user_id)

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        return True

    def add_dynamic_menu(
        self,
        menu_id: str,
        title: str,
        items: List[dict],
        back_to: str = "main",
        **kwargs,
    ) -> Menu:
        """Добавление динамического меню"""
        menu = Menu(id=menu_id, title=title, back_to=back_to, **kwargs)

        for item_data in items:
            item = MenuItem(**item_data)
            menu.add_item(item)

        self.register_menu(menu)
        return menu

    def update_dynamic_menu(self, menu_id: str, items: List[dict]):
        """Обновление динамического меню"""
        menu = self.menus.get(menu_id)
        if menu:
            menu.clear_items()
            for item_data in items:
                item = MenuItem(**item_data)
                menu.add_item(item)

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
                "items": [
                    {
                        "id": item.id,
                        "text": item.text,
                        "icon": item.icon,
                        "callback_data": item.callback_data,
                        "admin_only": item.admin_only,
                        "visible": item.visible,
                        "submenu": item.submenu,
                        "row": item.row,
                    }
                    for item in menu.items
                ],
            }

        return json.dumps(config, ensure_ascii=False, indent=2)

    def import_menu_config(self, config_json: str):
        """Импорт конфигурации меню из JSON"""
        config = json.loads(config_json)

        for menu_id, menu_data in config.items():
            menu = Menu(
                id=menu_id,
                title=menu_data["title"],
                description=menu_data.get("description", ""),
                back_to=menu_data.get("back_to"),
                back_button=menu_data.get("back_button", True),
                columns=menu_data.get("columns", 1),
            )

            for item_data in menu_data.get("items", []):
                item = MenuItem(
                    id=item_data["id"],
                    text=item_data["text"],
                    callback_data=item_data["callback_data"],
                    icon=item_data.get("icon", ""),
                    admin_only=item_data.get("admin_only", True),
                    visible=item_data.get("visible", True),
                    submenu=item_data.get("submenu"),
                    row=item_data.get("row"),
                )
                menu.add_item(item)

            self.register_menu(menu)

    def register_callback(self, callback_data: str, handler: Callable):
        """Регистрация обработчика callback"""
        self._callbacks[callback_data] = handler

    def get_callback_handler(self, callback_data: str) -> Optional[Callable]:
        """Получение обработчика callback"""
        return self._callbacks.get(callback_data)

    def clear_user_history(self, user_id: int):
        """Очистка истории пользователя"""
        self.menu_history.pop(user_id, None)
        self.current_menu.pop(user_id, None)


class MenuMiddleware:
    """Middleware для системы меню"""

    def __init__(self, menu_manager: MenuManager):
        self.menu_manager = menu_manager

    async def __call__(self, handler, event, data):
        """Обработка middleware"""
        # Добавляем menu_manager в data
        data["menu_manager"] = self.menu_manager

        # Проверяем доступ для личных сообщений
        if hasattr(event, "chat") and event.chat.type == "private":
            user_id = event.from_user.id
            if not self.menu_manager.is_admin(user_id):
                await event.answer(
                    "❌ У вас нет доступа к этому боту.\n"
                    "Обратитесь к администратору для получения прав.",
                    parse_mode="HTML",
                )
                return

        # Продолжаем обработку
        return await handler(event, data)
