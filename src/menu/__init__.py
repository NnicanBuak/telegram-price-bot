# Основные компоненты
from .renderer import MenuBuilder, MenuRenderer, MenuSender
from .manager import MenuManager, MenuRegistry, menu_handler, menu_opener

# Модели данных
from .models import (
    MenuStructure,
    MenuConfig,
    MenuButton,
    MenuResponse,
    NavigationState,
    ButtonType,
)

# Готовые билдеры
from .renderer import create_crud_menu, create_confirmation_menu, create_simple_menu

# Специализированные компоненты (если нужны)
from .keyboards import *

__all__ = [
    # === ОСНОВНЫЕ КОМПОНЕНТЫ ===
    "MenuBuilder",  # Строитель меню
    "MenuManager",  # Менеджер навигации и состояния
    "MenuRenderer",  # Рендерер в Telegram формат
    "MenuSender",  # Отправщик сообщений
    "MenuRegistry",  # Реестр для организации меню
    # === МОДЕЛИ ДАННЫХ ===
    "MenuStructure",  # Структура готового меню
    "MenuConfig",  # Конфигурация меню
    "MenuButton",  # Кнопка меню
    "MenuResponse",  # Ответ системы
    "NavigationState",  # Состояние навигации
    "ButtonType",  # Типы кнопок
    # === ГОТОВЫЕ БИЛДЕРЫ ===
    "create_crud_menu",  # CRUD меню
    "create_confirmation_menu",  # Меню подтверждения
    "create_simple_menu",  # Простое меню
    # === ДЕКОРАТОРЫ ===
    "menu_handler",  # Декоратор для обработчиков
    "menu_opener",  # Декоратор для открытия меню
    # === КЛАВИАТУРЫ (если нужны специальные) ===
    "BaseKeyboard",
    "PaginatedKeyboard",
    "ConfirmationKeyboard",
    "CrudKeyboard",
]

# Версия модуля
__version__ = "2.0.0"

# Мета-информация
__description__ = "Полноценная система меню для Telegram ботов"
__author__ = "Menu System Team"


# === ФАБРИЧНЫЕ ФУНКЦИИ ===


def create_menu_system(admin_user_ids: list[int]) -> tuple[MenuManager, MenuRegistry]:
    """
    Создать полную систему меню

    Args:
        admin_user_ids: Список ID администраторов

    Returns:
        tuple: (MenuManager, MenuRegistry)

    Example:
        ```python
        menu_manager, menu_registry = create_menu_system([123456789])

        # Создаем меню
        main_menu = (MenuBuilder("main")
            .title("🏠 Главное меню")
            .description("Выберите раздел:")
            .add_menu_link("Настройки", "settings", "⚙️")
            .add_action("Помощь", "help", "❓")
            .build())

        # Регистрируем
        menu_manager.register_menu(main_menu)

        # Отправляем
        await menu_manager.navigate_to("main", message, user_id)
        ```
    """
    menu_manager = MenuManager(admin_user_ids)
    menu_registry = MenuRegistry(menu_manager)

    return menu_manager, menu_registry


def quick_menu(
    menu_id: str, title: str, description: str = "", back_target: str = "main"
) -> MenuBuilder:
    """
    Быстрое создание простого меню

    Args:
        menu_id: Уникальный ID меню
        title: Заголовок меню
        description: Описание (опционально)
        back_target: Целевое меню для кнопки "Назад"

    Returns:
        MenuBuilder: Настроенный билдер меню

    Example:
        ```python
        menu = (quick_menu("settings", "⚙️ Настройки", "Конфигурация бота")
            .add_action("Логи", "show_logs", "📋")
            .add_action("Статистика", "show_stats", "📊")
            .build())
        ```
    """
    return create_simple_menu(menu_id, title, description, back_target)
