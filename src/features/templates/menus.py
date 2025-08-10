"""Конфигурация меню для шаблонов"""

from shared.menu_system import Menu, MenuItem


def get_templates_menus():
    """Получить конфигурацию меню шаблонов"""
    templates_menu = Menu(
        id="templates",
        title="📋 <b>Управление шаблонами</b>",
        description="Создание и редактирование шаблонов сообщений",
        back_to="main",
        columns=1,
    )

    templates_menu.add_item(
        MenuItem(
            id="templates_create",
            text="Создать шаблон",
            icon="➕",
            callback_data="template_create",
        )
    )

    templates_menu.add_item(
        MenuItem(
            id="templates_list",
            text="Список шаблонов",
            icon="📋",
            callback_data="templates_list",
        )
    )

    return [templates_menu]
