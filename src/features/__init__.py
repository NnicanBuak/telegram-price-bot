# Импорт всех роутеров
from .templates.handlers import TemplateHandlers
from .groups.handlers import group_router
from .mailing.handlers import mailing_router

# Импорт сервисов
from .templates.services import TemplateService
from .templates.models import TemplateData

# Импорт меню (создаем их здесь)
from shared.menu_system import Menu, MenuItem, MenuManager


class FeatureRegistry:
    """Реестр всех features приложения"""

    def __init__(self, database):
        self.database = database
        self.routers = []
        self.services = {}
        self.menu_manager = None

        # Инициализируем все features
        self._setup_template_feature()
        self._setup_group_feature()
        self._setup_mailing_feature()

    def _setup_template_feature(self):
        """Настройка feature шаблонов"""
        template_service = TemplateService(self.database)
        template_handlers = TemplateHandlers(template_service)

        self.routers.append(template_handlers.router)
        self.services["template_service"] = template_service

    def _setup_group_feature(self):
        """Настройка feature групп"""
        self.routers.append(group_router)

    def _setup_mailing_feature(self):
        """Настройка feature рассылки"""
        self.routers.append(mailing_router)

    def setup_menu_system(self, admin_ids):
        """Настройка системы меню"""
        self.menu_manager = MenuManager(admin_ids)
        self._setup_all_menus()
        return self.menu_manager

    def _setup_all_menus(self):
        """Настройка всех меню features"""
        if not self.menu_manager:
            return

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

        self.menu_manager.register_menu(main_menu)

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
                callback_data="template_list",
                order=1,
            )
        )

        templates_menu.add_item(
            MenuItem(
                id="templates_new",
                text="Создать новый",
                icon="➕",
                callback_data="template_create",
                order=2,
            )
        )

        self.menu_manager.register_menu(templates_menu)

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

        self.menu_manager.register_menu(groups_menu)

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

        self.menu_manager.register_menu(mailing_menu)

    def get_routers(self):
        """Получить все роутеры"""
        return self.routers

    def get_all_services(self):
        """Получить все сервисы"""
        return self.services

    def get_menu_manager(self):
        """Получить менеджер меню"""
        return self.menu_manager


def setup_features(database):
    """Главная функция настройки всех features"""
    return FeatureRegistry(database)


def get_all_routers():
    """Получить все роутеры features (для обратной совместимости)"""
    # Эта функция теперь не используется, но оставляем для совместимости
    return []
