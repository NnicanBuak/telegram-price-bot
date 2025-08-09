"""
Расширяемая система меню для Telegram бота
Обновленная версия с поддержкой базы данных и новых обработчиков
"""

from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types, BaseMiddleware

if TYPE_CHECKING:
    from database import Database


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


@dataclass
class Menu:
    """Меню с элементами"""

    id: str
    title: str
    description: str = ""
    items: List[MenuItem] = field(default_factory=list)
    back_to: Optional[str] = None
    back_button: bool = True
    columns: int = 1
    admin_only: bool = False

    def add_item(self, item: MenuItem):
        """Добавить элемент в меню"""
        self.items.append(item)
        # Сортируем по order
        self.items.sort(key=lambda x: x.order)

    def remove_item(self, item_id: str) -> bool:
        """Удалить элемент из меню"""
        original_length = len(self.items)
        self.items = [item for item in self.items if item.id != item_id]
        return len(self.items) < original_length

    def get_item(self, item_id: str) -> Optional[MenuItem]:
        """Получить элемент по ID"""
        return next((item for item in self.items if item.id == item_id), None)


class MenuManager:
    """Менеджер системы меню"""

    def __init__(self, admin_ids: List[int]):
        self.menus: Dict[str, Menu] = {}
        self.admin_ids = admin_ids
        self._handlers: Dict[str, Callable] = {}
        self._dynamic_handlers: List[Callable] = []

    def register_menu(self, menu: Menu):
        """Регистрация меню"""
        self.menus[menu.id] = menu

    def unregister_menu(self, menu_id: str) -> bool:
        """Удаление меню"""
        if menu_id in self.menus:
            del self.menus[menu_id]
            return True
        return False

    def get_menu(self, menu_id: str) -> Optional[Menu]:
        """Получить меню по ID"""
        return self.menus.get(menu_id)

    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in self.admin_ids

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
        menu = self.get_menu(menu_id)
        if not menu:
            return "❌ Меню не найдено", InlineKeyboardMarkup(inline_keyboard=[])

        # Проверяем права доступа к меню
        if menu.admin_only and not self.is_admin(user_id):
            return "❌ Доступ запрещен", InlineKeyboardMarkup(inline_keyboard=[])

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

    def export_menu_config(self) -> dict:
        """Экспорт конфигурации меню"""
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
        return config

    def import_menu_config(self, config: dict):
        """Импорт конфигурации меню"""
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


class MenuMiddleware(BaseMiddleware):
    """Middleware для интеграции системы меню"""

    def __init__(self, menu_manager: MenuManager, database: "Database" = None):
        self.menu_manager = menu_manager
        self.database = database
        super().__init__()

    async def __call__(self, handler, event, data):
        """Основной метод middleware"""
        # Добавляем menu_manager в контекст
        data["menu_manager"] = self.menu_manager

        # Добавляем database в контекст если есть
        if self.database:
            data["database"] = self.database

        # Проверяем права доступа для личных сообщений
        if isinstance(event, (types.Message, types.CallbackQuery)):
            user_id = event.from_user.id
            chat_type = (
                event.message.chat.type
                if isinstance(event, types.CallbackQuery)
                else event.chat.type
            )

            # Если это личное сообщение, проверяем админские права
            if chat_type == "private" and not self.menu_manager.is_admin(user_id):
                if isinstance(event, types.Message):
                    await event.answer(
                        "❌ <b>Доступ запрещен</b>\n\n"
                        "Этот бот доступен только администраторам.\n"
                        "Обратитесь к администратору для получения доступа.",
                        parse_mode="HTML",
                    )
                elif isinstance(event, types.CallbackQuery):
                    await event.answer("❌ Доступ запрещен", show_alert=True)
                return

        # Обрабатываем callback запросы через menu_manager
        if isinstance(event, types.CallbackQuery):
            handled = await self.menu_manager.handle_callback(
                event, database=self.database, menu_manager=self.menu_manager
            )

            # Если обработано menu_manager, не передаем дальше
            if handled:
                return

        # Передаем управление следующему обработчику
        return await handler(event, data)


class DatabaseMenuIntegration:
    """Интеграция меню с базой данных"""

    def __init__(self, menu_manager: MenuManager, database: "Database"):
        self.menu_manager = menu_manager
        self.database = database

    async def update_templates_menu(self):
        """Обновить меню шаблонов данными из БД"""
        templates = await self.database.get_templates()

        items = []
        for template in templates:
            icon = "📄" if not template.file_path else "📎"
            items.append(
                {
                    "id": f"template_{template.id}",
                    "text": template.name,
                    "icon": icon,
                    "callback_data": f"template_view_{template.id}",
                    "order": template.id,
                }
            )

        # Добавляем кнопку создания нового шаблона
        items.append(
            {
                "id": "template_create_new",
                "text": "Создать новый",
                "icon": "➕",
                "callback_data": "template_create",
                "order": 999,
            }
        )

        await self.menu_manager.add_dynamic_menu(
            menu_id="templates_dynamic",
            title="📋 <b>Шаблоны сообщений</b>",
            items=items,
            description=f"Найдено шаблонов: {len(templates)}",
            back_to="templates",
            columns=1,
        )

    async def update_groups_menu(self):
        """Обновить меню групп данными из БД"""
        groups = await self.database.get_chat_groups()

        items = []
        for group in groups:
            chat_count = len(group.chat_ids) if group.chat_ids else 0
            items.append(
                {
                    "id": f"group_{group.id}",
                    "text": f"{group.name} ({chat_count} чатов)",
                    "icon": "👥",
                    "callback_data": f"group_view_{group.id}",
                    "order": group.id,
                }
            )

        # Добавляем кнопку создания новой группы
        items.append(
            {
                "id": "group_create_new",
                "text": "Создать группу",
                "icon": "➕",
                "callback_data": "group_create",
                "order": 999,
            }
        )

        await self.menu_manager.add_dynamic_menu(
            menu_id="groups_dynamic",
            title="👥 <b>Группы чатов</b>",
            items=items,
            description=f"Найдено групп: {len(groups)}",
            back_to="groups",
            columns=1,
        )

    async def update_history_menu(self):
        """Обновить меню истории рассылок"""
        mailings = await self.database.get_mailings_history(limit=10)

        items = []
        for mailing in mailings:
            status_icon = {
                "pending": "⏳",
                "running": "🚀",
                "completed": "✅",
                "failed": "❌",
            }.get(mailing.status, "❓")

            success_rate = 0
            if mailing.total_chats > 0:
                success_rate = mailing.sent_count / mailing.total_chats * 100

            items.append(
                {
                    "id": f"mailing_{mailing.id}",
                    "text": f"#{mailing.id} ({success_rate:.0f}%) {status_icon}",
                    "icon": "📊",
                    "callback_data": f"mailing_details_{mailing.id}",
                    "order": -mailing.id,  # Обратная сортировка (новые первыми)
                }
            )

        await self.menu_manager.add_dynamic_menu(
            menu_id="history_dynamic",
            title="📊 <b>История рассылок</b>",
            items=items,
            description=f"Последние {len(mailings)} рассылок",
            back_to="history",
            columns=1,
        )

    async def refresh_all_menus(self):
        """Обновить все динамические меню"""
        await self.update_templates_menu()
        await self.update_groups_menu()
        await self.update_history_menu()


# Утилиты для работы с меню
def create_confirmation_menu(
    title: str,
    description: str,
    confirm_text: str = "✅ Подтвердить",
    confirm_callback: str = "confirm",
    cancel_text: str = "❌ Отмена",
    cancel_callback: str = "cancel",
) -> Menu:
    """Создать меню подтверждения"""
    menu = Menu(
        id="confirmation",
        title=title,
        description=description,
        back_button=False,
        columns=2,
    )

    menu.add_item(
        MenuItem(
            id="confirm", text=confirm_text, callback_data=confirm_callback, order=1
        )
    )

    menu.add_item(
        MenuItem(id="cancel", text=cancel_text, callback_data=cancel_callback, order=2)
    )

    return menu


def create_pagination_menu(
    items: List[dict],
    page: int = 0,
    items_per_page: int = 5,
    callback_prefix: str = "page",
) -> List[List[InlineKeyboardButton]]:
    """Создать пагинированное меню"""
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
