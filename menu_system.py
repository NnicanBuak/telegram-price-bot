"""
Расширяемая система меню для Telegram бота
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import json


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
    row: Optional[int] = None  # Для группировки кнопок в ряды


@dataclass
class Menu:
    """Меню с элементами"""

    id: str
    title: str
    description: str = ""
    items: List[MenuItem] = field(default_factory=list)
    back_button: bool = True
    back_to: Optional[str] = None
    columns: int = 1  # Количество колонок для кнопок

    def add_item(self, item: MenuItem):
        """Добавить элемент в меню"""
        item.parent = self.id
        self.items.append(item)
        return self

    def remove_item(self, item_id: str):
        """Удалить элемент из меню"""
        self.items = [item for item in self.items if item.id != item_id]
        return self


class MenuManager:
    """Менеджер системы меню"""

    def __init__(self, admin_ids: List[int]):
        self.menus: Dict[str, Menu] = {}
        self.admin_ids = admin_ids
        self.current_menu: Dict[int, str] = {}  # user_id -> menu_id
        self.menu_history: Dict[int, List[str]] = {}  # История навигации
        self._callbacks: Dict[str, Callable] = {}  # callback_data -> function
        self._init_default_menus()

    def _init_default_menus(self):
        """Инициализация стандартных меню"""
        # Главное меню
        main_menu = Menu(
            id="main",
            title="🤖 <b>Бот для рассылки прайс-листов</b>",
            description="Выберите действие:",
            back_button=False,
        )

        main_menu.add_item(
            MenuItem(
                id="templates_btn",
                text="Шаблоны",
                icon="📋",
                callback_data="menu_templates",
                submenu="templates",
            )
        )

        main_menu.add_item(
            MenuItem(
                id="groups_btn",
                text="Группы чатов",
                icon="👥",
                callback_data="menu_groups",
                submenu="groups",
            )
        )

        main_menu.add_item(
            MenuItem(
                id="mailing_btn",
                text="Создать рассылку",
                icon="📮",
                callback_data="create_mailing",
            )
        )

        main_menu.add_item(
            MenuItem(
                id="history_btn",
                text="История рассылок",
                icon="📊",
                callback_data="history",
            )
        )

        main_menu.add_item(
            MenuItem(
                id="settings_btn",
                text="Настройки",
                icon="⚙️",
                callback_data="menu_settings",
                submenu="settings",
            )
        )

        self.register_menu(main_menu)

        # Меню шаблонов
        templates_menu = Menu(
            id="templates",
            title="📋 <b>Шаблоны сообщений</b>",
            description="Управление шаблонами:",
            back_to="main",
        )

        templates_menu.add_item(
            MenuItem(
                id="new_template",
                text="Создать новый",
                icon="➕",
                callback_data="new_template",
            )
        )

        templates_menu.add_item(
            MenuItem(
                id="list_templates",
                text="Список шаблонов",
                icon="📄",
                callback_data="list_templates",
            )
        )

        templates_menu.add_item(
            MenuItem(
                id="import_template",
                text="Импорт шаблона",
                icon="📥",
                callback_data="import_template",
            )
        )

        self.register_menu(templates_menu)

        # Меню групп
        groups_menu = Menu(
            id="groups",
            title="👥 <b>Группы чатов</b>",
            description="Управление группами:",
            back_to="main",
        )

        groups_menu.add_item(
            MenuItem(
                id="new_group",
                text="Создать новую",
                icon="➕",
                callback_data="new_group",
            )
        )

        groups_menu.add_item(
            MenuItem(
                id="list_groups",
                text="Список групп",
                icon="📝",
                callback_data="list_groups",
            )
        )

        groups_menu.add_item(
            MenuItem(
                id="import_chats",
                text="Импорт чатов",
                icon="📥",
                callback_data="import_chats",
            )
        )

        self.register_menu(groups_menu)

        # Меню настроек
        settings_menu = Menu(
            id="settings",
            title="⚙️ <b>Настройки</b>",
            description="Параметры бота:",
            back_to="main",
        )

        settings_menu.add_item(
            MenuItem(
                id="mailing_settings",
                text="Параметры рассылки",
                icon="📬",
                callback_data="mailing_settings",
            )
        )

        settings_menu.add_item(
            MenuItem(
                id="admin_list",
                text="Администраторы",
                icon="👤",
                callback_data="admin_list",
            )
        )

        settings_menu.add_item(
            MenuItem(
                id="backup", text="Резервная копия", icon="💾", callback_data="backup"
            )
        )

        settings_menu.add_item(
            MenuItem(
                id="statistics",
                text="Статистика",
                icon="📈",
                callback_data="statistics",
            )
        )

        self.register_menu(settings_menu)

    def register_menu(self, menu: Menu):
        """Регистрация меню"""
        self.menus[menu.id] = menu
        return self

    def register_callback(self, callback_data: str, handler: Callable):
        """Регистрация обработчика для callback_data"""
        self._callbacks[callback_data] = handler
        return self

    def get_callback_handler(self, callback_data: str) -> Optional[Callable]:
        """Получить обработчик для callback_data"""
        return self._callbacks.get(callback_data)

    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.admin_ids

    def get_menu(self, menu_id: str, user_id: int) -> Optional[Menu]:
        """Получить меню для пользователя"""
        if not self.is_admin(user_id):
            return None
        return self.menus.get(menu_id)

    def get_current_menu(self, user_id: int) -> Optional[str]:
        """Получить текущее меню пользователя"""
        return self.current_menu.get(user_id)

    def set_current_menu(self, user_id: int, menu_id: str):
        """Установить текущее меню пользователя"""
        self.current_menu[user_id] = menu_id

        # Обновляем историю
        if user_id not in self.menu_history:
            self.menu_history[user_id] = []

        # Если это не возврат назад, добавляем в историю
        history = self.menu_history[user_id]
        if not history or history[-1] != menu_id:
            history.append(menu_id)
            # Ограничиваем историю 10 элементами
            if len(history) > 10:
                history.pop(0)

    def go_back(self, user_id: int) -> Optional[str]:
        """Вернуться к предыдущему меню"""
        history = self.menu_history.get(user_id, [])
        if len(history) > 1:
            history.pop()  # Удаляем текущее меню
            previous_menu = history[-1]
            self.current_menu[user_id] = previous_menu
            return previous_menu
        return None

    def build_keyboard(self, menu: Menu, user_id: int) -> InlineKeyboardMarkup:
        """Построить клавиатуру для меню"""
        buttons = []
        current_row = []
        current_row_num = 0

        for item in menu.items:
            # Проверяем видимость и права доступа
            if not item.visible:
                continue

            if item.admin_only and not self.is_admin(user_id):
                continue

            # Создаем кнопку
            btn_text = f"{item.icon} {item.text}" if item.icon else item.text
            btn = InlineKeyboardButton(text=btn_text, callback_data=item.callback_data)

            # Группировка по рядам
            if item.row is not None and item.row != current_row_num:
                if current_row:
                    buttons.append(current_row)
                current_row = [btn]
                current_row_num = item.row
            else:
                current_row.append(btn)

                # Разбиваем по колонкам
                if len(current_row) >= menu.columns:
                    buttons.append(current_row)
                    current_row = []

        # Добавляем оставшиеся кнопки
        if current_row:
            buttons.append(current_row)

        # Добавляем кнопку "Назад"
        if menu.back_button and menu.back_to:
            back_btn = InlineKeyboardButton(
                text="🔙 Назад", callback_data=f"menu_{menu.back_to}"
            )
            buttons.append([back_btn])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def render_menu(
        self, menu_id: str, user_id: int
    ) -> tuple[str, InlineKeyboardMarkup]:
        """Отрендерить меню (текст + клавиатура)"""
        menu = self.get_menu(menu_id, user_id)
        if not menu:
            return "❌ Меню не найдено или нет доступа", None

        # Формируем текст
        text = menu.title
        if menu.description:
            text += f"\n\n{menu.description}"

        # Строим клавиатуру
        keyboard = self.build_keyboard(menu, user_id)

        # Сохраняем текущее меню
        self.set_current_menu(user_id, menu_id)

        return text, keyboard

    async def navigate_to(self, menu_id: str, callback: types.CallbackQuery):
        """Навигация к указанному меню"""
        user_id = callback.from_user.id
        text, keyboard = self.render_menu(menu_id, user_id)

        if keyboard:
            await callback.message.edit_text(
                text, reply_markup=keyboard, parse_mode="HTML"
            )
            await callback.answer()
            return True
        else:
            await callback.answer("Нет доступа к этому меню", show_alert=True)
            return False

    def add_dynamic_menu(
        self,
        menu_id: str,
        title: str,
        items: List[Dict[str, Any]],
        back_to: str = "main",
    ):
        """Добавить динамическое меню"""
        menu = Menu(id=menu_id, title=title, back_to=back_to)

        for item_data in items:
            item = MenuItem(
                id=item_data.get("id", ""),
                text=item_data.get("text", ""),
                icon=item_data.get("icon", ""),
                callback_data=item_data.get("callback_data", ""),
                admin_only=item_data.get("admin_only", True),
            )
            menu.add_item(item)

        self.register_menu(menu)
        return menu

    def export_menu_config(self) -> str:
        """Экспорт конфигурации меню в JSON"""
        config = {}
        for menu_id, menu in self.menus.items():
            config[menu_id] = {
                "title": menu.title,
                "description": menu.description,
                "back_to": menu.back_to,
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
                columns=menu_data.get("columns", 1),
            )

            for item_data in menu_data.get("items", []):
                item = MenuItem(
                    id=item_data["id"],
                    text=item_data["text"],
                    icon=item_data.get("icon", ""),
                    callback_data=item_data["callback_data"],
                    admin_only=item_data.get("admin_only", True),
                    visible=item_data.get("visible", True),
                    submenu=item_data.get("submenu"),
                    row=item_data.get("row"),
                )
                menu.add_item(item)

            self.register_menu(menu)


class MenuMiddleware:
    """Middleware для обработки меню"""

    def __init__(self, menu_manager: MenuManager):
        self.menu_manager = menu_manager

    async def __call__(self, handler, event, data):
        """Обработка события"""
        # Добавляем menu_manager в data для доступа в хендлерах
        data["menu_manager"] = self.menu_manager

        # Проверяем права доступа для личных сообщений
        if isinstance(event, types.Message):
            if event.chat.type == "private":
                user_id = event.from_user.id
                if not self.menu_manager.is_admin(user_id):
                    await event.answer(
                        "⛔ У вас нет доступа к этому боту.\n"
                        "Обратитесь к администратору."
                    )
                    return  # Прерываем обработку

        return await handler(event, data)
