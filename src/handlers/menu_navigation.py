import logging
from aiogram import Router, F, types
from menu import MenuBuilder, create_crud_menu

logger = logging.getLogger(__name__)


def setup_menus(menu_manager) -> None:
    """Настройка основных меню системы"""

    # Главное меню
    main_menu = (
        MenuBuilder("main")
        .title("🏠 Главное меню")
        .description(
            "Добро пожаловать в Telegram Price Bot!\n\nВыберите нужную функцию:"
        )
        .add_menu_link("📄 Шаблоны сообщений", "templates")
        .add_menu_link("👥 Группы чатов", "groups")
        .add_menu_link("📮 Рассылка", "mailing")
        .add_action("📊 История рассылок", "mailings_history")
        .add_menu_link("⚙️ Настройки", "settings")
        .no_back_button()
        .build()
    )

    # CRUD меню для шаблонов
    templates_menu = (
        create_crud_menu("templates", "📄 Управление шаблонами")
        .back_button("main")
        .build()
    )

    # CRUD меню для групп
    groups_menu = (
        create_crud_menu("groups", "👥 Управление группами чатов")
        .back_button("main")
        .build()
    )

    # Меню рассылки
    mailing_menu = (
        MenuBuilder("mailing")
        .title("📮 Рассылка сообщений")
        .description(
            "Создавайте и запускайте рассылки по группам чатов.\nВыберите действие:"
        )
        .add_action("📮 Создать рассылку", "mailing_create")
        .add_action("📊 История рассылок", "mailings_history")
        .back_button("main")
        .build()
    )

    # Меню настроек
    settings_menu = (
        MenuBuilder("settings")
        .title("⚙️ Настройки системы")
        .description("Управление конфигурацией и мониторинг системы.")
        .add_action("📊 Статус системы", "system_status")
        .add_action("📋 Конфигурация", "system_config")
        .add_action("📝 Логи", "system_logs")
        .back_button("main")
        .build()
    )

    # Регистрируем все меню
    for menu in [main_menu, templates_menu, groups_menu, mailing_menu, settings_menu]:
        menu_manager.register_menu(menu)

    logger.info("✅ Основные меню зарегистрированы")


def get_router(deps) -> Router:
    """Возвращает роутер с навигацией между меню"""
    router = Router()

    @router.callback_query(F.data.startswith("menu_") | F.data == "back")
    async def handle_menu_navigation(callback: types.CallbackQuery):
        """Автоматическая навигация между меню"""
        success = await deps.menu_manager.handle_callback(callback)
        if not success:
            await callback.answer("❌ Меню не найдено", show_alert=True)

    @router.callback_query(F.data == "menu_main")
    async def show_main_menu(callback: types.CallbackQuery):
        """Показать главное меню"""
        await deps.menu_manager.navigate_to("main", callback, callback.from_user.id)

    @router.callback_query(F.data == "menu_templates")
    async def show_templates_menu(callback: types.CallbackQuery):
        """Показать меню шаблонов"""
        await deps.menu_manager.navigate_to(
            "templates", callback, callback.from_user.id
        )

    @router.callback_query(F.data == "menu_groups")
    async def show_groups_menu(callback: types.CallbackQuery):
        """Показать меню групп"""
        await deps.menu_manager.navigate_to("groups", callback, callback.from_user.id)

    @router.callback_query(F.data == "menu_mailing")
    async def show_mailing_menu(callback: types.CallbackQuery):
        """Показать меню рассылки"""
        await deps.menu_manager.navigate_to("mailing", callback, callback.from_user.id)

    @router.callback_query(F.data == "menu_settings")
    async def show_settings_menu(callback: types.CallbackQuery):
        """Показать меню настроек"""
        await deps.menu_manager.navigate_to("settings", callback, callback.from_user.id)

    return router
