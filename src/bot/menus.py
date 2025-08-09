"""
Конкретные меню для Telegram Price Bot
Создание и настройка меню бота для рассылки прайс-листов
"""

from typing import List, Optional
from menu_system import MenuManager, Menu, MenuItem
from database import Database


class BotMenus:
    """Класс для создания и управления меню бота"""

    def __init__(self, menu_manager: MenuManager):
        self.menu_manager = menu_manager
        self.setup_static_menus()

    def setup_static_menus(self):
        """Настройка статических меню бота"""
        self._create_main_menu()
        self._create_templates_menu()
        self._create_groups_menu()
        self._create_mailing_menu()
        self._create_history_menu()
        self._create_settings_menu()

    def _create_main_menu(self):
        """Создание главного меню"""
        main_menu = Menu(
            id="main",
            title="🤖 <b>Telegram Price Bot</b>",
            description="Бот для рассылки прайс-листов по группам чатов",
            back_button=False,
        )

        main_menu.add_item(
            MenuItem(
                id="templates",
                text="Шаблоны",
                icon="📋",
                callback_data="menu_templates",
            )
        )

        main_menu.add_item(
            MenuItem(
                id="groups", text="Группы чатов", icon="👥", callback_data="menu_groups"
            )
        )

        main_menu.add_item(
            MenuItem(
                id="mailing",
                text="Создать рассылку",
                icon="📮",
                callback_data="menu_mailing",
            )
        )

        main_menu.add_item(
            MenuItem(
                id="history", text="История", icon="📊", callback_data="menu_history"
            )
        )

        main_menu.add_item(
            MenuItem(
                id="settings", text="Настройки", icon="⚙️", callback_data="menu_settings"
            )
        )

        self.menu_manager.register_menu(main_menu)

    def _create_templates_menu(self):
        """Создание меню шаблонов"""
        templates_menu = Menu(
            id="templates",
            title="📋 <b>Управление шаблонами</b>",
            description="Создание и редактирование шаблонов сообщений",
            back_to="main",
            columns=1,
        )

        templates_menu.add_item(
            MenuItem(
                id="templates_list",
                text="Список шаблонов",
                icon="📄",
                callback_data="templates_list",
            )
        )

        templates_menu.add_item(
            MenuItem(
                id="templates_new",
                text="Создать новый",
                icon="➕",
                callback_data="templates_new",
            )
        )

        self.menu_manager.register_menu(templates_menu)

    def _create_groups_menu(self):
        """Создание меню групп чатов"""
        groups_menu = Menu(
            id="groups",
            title="👥 <b>Управление группами</b>",
            description="Создание и редактирование групп чатов для рассылки",
            back_to="main",
            columns=1,
        )

        groups_menu.add_item(
            MenuItem(
                id="groups_list",
                text="Список групп",
                icon="📋",
                callback_data="groups_list",
            )
        )

        groups_menu.add_item(
            MenuItem(
                id="groups_new",
                text="Создать новую",
                icon="➕",
                callback_data="groups_new",
            )
        )

        self.menu_manager.register_menu(groups_menu)

    def _create_mailing_menu(self):
        """Создание меню рассылки"""
        mailing_menu = Menu(
            id="mailing",
            title="📮 <b>Создание рассылки</b>",
            description="Выбор шаблона и групп для рассылки",
            back_to="main",
            columns=1,
        )

        mailing_menu.add_item(
            MenuItem(
                id="mailing_start",
                text="Начать рассылку",
                icon="🚀",
                callback_data="mailing_start",
            )
        )

        mailing_menu.add_item(
            MenuItem(
                id="mailing_preview",
                text="Предпросмотр",
                icon="👁",
                callback_data="mailing_preview",
            )
        )

        self.menu_manager.register_menu(mailing_menu)

    def _create_history_menu(self):
        """Создание меню истории"""
        history_menu = Menu(
            id="history",
            title="📊 <b>История рассылок</b>",
            description="Просмотр статистики и истории отправленных рассылок",
            back_to="main",
            columns=1,
        )

        history_menu.add_item(
            MenuItem(
                id="history_recent",
                text="Последние рассылки",
                icon="🕐",
                callback_data="history_recent",
            )
        )

        history_menu.add_item(
            MenuItem(
                id="history_stats",
                text="Статистика",
                icon="📈",
                callback_data="history_stats",
            )
        )

        self.menu_manager.register_menu(history_menu)

    def _create_settings_menu(self):
        """Создание меню настроек"""
        settings_menu = Menu(
            id="settings",
            title="⚙️ <b>Настройки бота</b>",
            description="Конфигурация и настройки системы",
            back_to="main",
            columns=1,
        )

        settings_menu.add_item(
            MenuItem(
                id="settings_general",
                text="Общие настройки",
                icon="🛠",
                callback_data="settings_general",
            )
        )

        settings_menu.add_item(
            MenuItem(
                id="settings_notifications",
                text="Уведомления",
                icon="🔔",
                callback_data="settings_notifications",
            )
        )

        settings_menu.add_item(
            MenuItem(
                id="settings_backup",
                text="Резервное копирование",
                icon="💾",
                callback_data="settings_backup",
            )
        )

        self.menu_manager.register_menu(settings_menu)

    async def create_templates_list_menu(self, db: Database) -> Menu:
        """Создание динамического меню списка шаблонов"""
        templates = await db.get_templates()

        items = []
        for template in templates:
            # Ограничиваем длину имени для кнопки
            display_name = (
                template.name[:30] + "..." if len(template.name) > 30 else template.name
            )

            items.append(
                {
                    "id": f"template_{template.id}",
                    "text": display_name,
                    "icon": "📄",
                    "callback_data": f"template_view_{template.id}",
                }
            )

        if not items:
            items.append(
                {
                    "id": "no_templates",
                    "text": "Нет шаблонов",
                    "icon": "📝",
                    "callback_data": "templates_new",
                }
            )

        # Добавляем кнопку создания нового шаблона
        items.append(
            {
                "id": "template_new",
                "text": "Создать новый",
                "icon": "➕",
                "callback_data": "templates_new",
            }
        )

        return self.menu_manager.add_dynamic_menu(
            menu_id="templates_list",
            title="📋 <b>Список шаблонов</b>",
            items=items,
            back_to="templates",
        )

    async def create_groups_list_menu(self, db: Database) -> Menu:
        """Создание динамического меню списка групп"""
        groups = await db.get_chat_groups()

        items = []
        for group in groups:
            # Показываем количество чатов в группе
            chat_count = len(group.chat_ids)
            display_name = f"{group.name} ({chat_count} чатов)"

            items.append(
                {
                    "id": f"group_{group.id}",
                    "text": display_name,
                    "icon": "👥",
                    "callback_data": f"group_view_{group.id}",
                }
            )

        if not items:
            items.append(
                {
                    "id": "no_groups",
                    "text": "Нет групп",
                    "icon": "👥",
                    "callback_data": "groups_new",
                }
            )

        # Добавляем кнопку создания новой группы
        items.append(
            {
                "id": "group_new",
                "text": "Создать новую",
                "icon": "➕",
                "callback_data": "groups_new",
            }
        )

        return self.menu_manager.add_dynamic_menu(
            menu_id="groups_list",
            title="👥 <b>Список групп чатов</b>",
            items=items,
            back_to="groups",
        )

    async def create_mailing_template_selection_menu(self, db: Database) -> Menu:
        """Создание меню выбора шаблона для рассылки"""
        templates = await db.get_templates()

        items = []
        for template in templates:
            display_name = (
                template.name[:25] + "..." if len(template.name) > 25 else template.name
            )

            items.append(
                {
                    "id": f"mail_template_{template.id}",
                    "text": display_name,
                    "icon": "📄",
                    "callback_data": f"mailing_select_template_{template.id}",
                }
            )

        if not items:
            items.append(
                {
                    "id": "no_templates_for_mailing",
                    "text": "Сначала создайте шаблон",
                    "icon": "📝",
                    "callback_data": "menu_templates",
                }
            )

        return self.menu_manager.add_dynamic_menu(
            menu_id="mailing_template_selection",
            title="📋 <b>Выберите шаблон</b>",
            description="Выберите шаблон для рассылки:",
            items=items,
            back_to="mailing",
        )

    async def create_mailing_groups_selection_menu(self, db: Database) -> Menu:
        """Создание меню выбора групп для рассылки"""
        groups = await db.get_chat_groups()

        items = []
        for group in groups:
            chat_count = len(group.chat_ids)
            display_name = f"{group.name} ({chat_count})"

            items.append(
                {
                    "id": f"mail_group_{group.id}",
                    "text": display_name,
                    "icon": "☐",  # Checkbox empty
                    "callback_data": f"mailing_toggle_group_{group.id}",
                }
            )

        if not items:
            items.append(
                {
                    "id": "no_groups_for_mailing",
                    "text": "Сначала создайте группу",
                    "icon": "👥",
                    "callback_data": "menu_groups",
                }
            )
        else:
            # Добавляем кнопки управления
            items.extend(
                [
                    {
                        "id": "select_all_groups",
                        "text": "Выбрать все",
                        "icon": "☑️",
                        "callback_data": "mailing_select_all_groups",
                    },
                    {
                        "id": "confirm_mailing",
                        "text": "Начать рассылку",
                        "icon": "🚀",
                        "callback_data": "mailing_confirm",
                    },
                ]
            )

        return self.menu_manager.add_dynamic_menu(
            menu_id="mailing_groups_selection",
            title="👥 <b>Выберите группы</b>",
            description="Отметьте группы для рассылки:",
            items=items,
            back_to="mailing_template_selection",
            columns=1,
        )

    async def create_history_list_menu(self, db: Database, limit: int = 10) -> Menu:
        """Создание меню истории рассылок"""
        mailings = await db.get_mailings_history(limit=limit)

        items = []
        for mailing in mailings:
            # Получаем шаблон для отображения
            template = await db.get_template(mailing.template_id)
            template_name = template.name if template else "Удаленный шаблон"

            # Форматируем статистику
            success_rate = (
                (mailing.sent_count / mailing.total_chats * 100)
                if mailing.total_chats > 0
                else 0
            )
            status_icon = (
                "✅"
                if mailing.status == "completed"
                else "❌" if mailing.status == "failed" else "⏳"
            )

            display_text = f"{template_name[:20]}... ({success_rate:.0f}%)"

            items.append(
                {
                    "id": f"history_{mailing.id}",
                    "text": display_text,
                    "icon": status_icon,
                    "callback_data": f"history_view_{mailing.id}",
                }
            )

        if not items:
            items.append(
                {
                    "id": "no_history",
                    "text": "История пуста",
                    "icon": "📭",
                    "callback_data": "menu_main",
                }
            )

        return self.menu_manager.add_dynamic_menu(
            menu_id="history_list",
            title="📊 <b>История рассылок</b>",
            items=items,
            back_to="history",
        )

    def update_mailing_groups_menu(self, selected_groups: List[int]):
        """Обновление меню выбора групп с отмеченными элементами"""
        menu = self.menu_manager.menus.get("mailing_groups_selection")
        if menu:
            for item in menu.items:
                if item.id.startswith("mail_group_"):
                    group_id = int(item.id.replace("mail_group_", ""))
                    if group_id in selected_groups:
                        item.icon = "☑️"  # Checkbox checked
                        item.text = item.text.replace("☐", "☑️")
                    else:
                        item.icon = "☐"  # Checkbox empty
                        item.text = item.text.replace("☑️", "☐")


def setup_bot_menus(menu_manager: MenuManager) -> BotMenus:
    """Инициализация меню бота"""
    return BotMenus(menu_manager)
