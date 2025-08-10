# Импорт всех роутеров
from .templates.handlers import template_router
from .groups.handlers import group_router
from .mailing.handlers import mailing_router

# Импорт меню (создаем их здесь)
from shared.menu_system import Menu, MenuItem


def get_all_routers():
    """Получить все роутеры features"""
    return [template_router, group_router, mailing_router]


def setup_all_menus(menu_manager):
    """Настройка всех меню features"""
    # Главное меню
    main_menu = Menu(
        id="main",
        title="🏠 <b>Главное меню</b>",
        description="Добро пожаловать в Telegram Price Bot!\n\nВыберите нужную функцию:",
        columns=1,
    )

    main_menu.add_item(
        MenuItem(
            id="templates",
            text="Шаблоны сообщений",
            icon="📄",
            callback_data="menu_templates",
            order=1,
        )
    )

    main_menu.add_item(
        MenuItem(
            id="groups",
            text="Группы чатов",
            icon="👥",
            callback_data="menu_groups",
            order=2,
        )
    )

    main_menu.add_item(
        MenuItem(
            id="mailing",
            text="Рассылка",
            icon="📮",
            callback_data="menu_mailing",
            order=3,
        )
    )

    main_menu.add_item(
        MenuItem(
            id="history",
            text="История рассылок",
            icon="📊",
            callback_data="mailings_history",
            order=4,
        )
    )

    main_menu.add_item(
        MenuItem(
            id="settings",
            text="Настройки",
            icon="⚙️",
            callback_data="menu_settings",
            admin_only=True,
            order=5,
        )
    )

    menu_manager.register_menu(main_menu)

    # Меню шаблонов
    templates_menu = Menu(
        id="templates",
        title="📄 <b>Шаблоны сообщений</b>",
        description="Создание и управление шаблонами для рассылки",
        back_to="main",
        columns=1,
    )

    templates_menu.add_item(
        MenuItem(
            id="templates_list",
            text="Список шаблонов",
            icon="📋",
            callback_data="templates_list",
            order=1,
        )
    )

    templates_menu.add_item(
        MenuItem(
            id="templates_new",
            text="Создать новый",
            icon="➕",
            callback_data="templates_new",
            order=2,
        )
    )

    templates_menu.add_item(
        MenuItem(
            id="templates_export",
            text="Экспорт шаблонов",
            icon="📤",
            callback_data="template_export_all",
            admin_only=True,
            order=3,
        )
    )

    templates_menu.add_item(
        MenuItem(
            id="templates_import",
            text="Импорт шаблонов",
            icon="📥",
            callback_data="template_import",
            admin_only=True,
            order=4,
        )
    )

    menu_manager.register_menu(templates_menu)

    # Меню групп
    groups_menu = Menu(
        id="groups",
        title="👥 <b>Группы чатов</b>",
        description="Управление группами чатов для рассылки",
        back_to="main",
        columns=1,
    )

    groups_menu.add_item(
        MenuItem(
            id="groups_list",
            text="Список групп",
            icon="📋",
            callback_data="groups_list",
            order=1,
        )
    )

    groups_menu.add_item(
        MenuItem(
            id="groups_new",
            text="Создать группу",
            icon="➕",
            callback_data="group_create",
            order=2,
        )
    )

    menu_manager.register_menu(groups_menu)

    # Меню рассылки
    mailing_menu = Menu(
        id="mailing",
        title="📮 <b>Рассылка сообщений</b>",
        description="Создание и запуск рассылок по группам чатов",
        back_to="main",
        columns=1,
    )

    mailing_menu.add_item(
        MenuItem(
            id="mailing_create",
            text="Создать рассылку",
            icon="📮",
            callback_data="mailing_create",
            order=1,
        )
    )

    mailing_menu.add_item(
        MenuItem(
            id="mailing_history",
            text="История рассылок",
            icon="📊",
            callback_data="mailings_history",
            order=2,
        )
    )

    menu_manager.register_menu(mailing_menu)

    # Меню настроек
    settings_menu = Menu(
        id="settings",
        title="⚙️ <b>Настройки</b>",
        description="Конфигурация и управление ботом",
        back_to="main",
        admin_only=True,
        columns=1,
    )

    settings_menu.add_item(
        MenuItem(
            id="backup",
            text="Резервная копия",
            icon="💾",
            callback_data="backup_create",
            admin_only=True,
            order=1,
        )
    )

    settings_menu.add_item(
        MenuItem(
            id="logs",
            text="Логи системы",
            icon="📋",
            callback_data="logs_view",
            admin_only=True,
            order=2,
        )
    )

    settings_menu.add_item(
        MenuItem(
            id="stats",
            text="Статистика",
            icon="📈",
            callback_data="stats_view",
            admin_only=True,
            order=3,
        )
    )

    menu_manager.register_menu(settings_menu)
