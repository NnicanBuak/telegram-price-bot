from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union, Callable
from enum import Enum


class ButtonType(Enum):
    """Типы кнопок меню"""

    ACTION = "action"  # Кнопка действия (callback_data)
    MENU_LINK = "menu_link"  # Ссылка на другое меню
    URL = "url"  # Внешняя ссылка
    BACK = "back"  # Кнопка возврата
    CONFIRM = "confirm"  # Подтверждение
    CANCEL = "cancel"  # Отмена


@dataclass
class MenuButton:
    """Кнопка меню"""

    text: str
    button_type: ButtonType
    callback_data: Optional[str] = None
    url: Optional[str] = None
    target_menu: Optional[str] = None  # ID целевого меню для MENU_LINK
    icon: str = ""
    admin_only: bool = False
    visible: bool = True
    order: int = 0

    def __post_init__(self):
        """Валидация после создания"""
        if self.button_type == ButtonType.ACTION and not self.callback_data:
            raise ValueError("ACTION кнопка должна иметь callback_data")
        if self.button_type == ButtonType.URL and not self.url:
            raise ValueError("URL кнопка должна иметь url")
        if self.button_type == ButtonType.MENU_LINK and not self.target_menu:
            raise ValueError("MENU_LINK кнопка должна иметь target_menu")

    @property
    def display_text(self) -> str:
        """Текст кнопки с иконкой"""
        return f"{self.icon} {self.text}".strip() if self.icon else self.text


@dataclass
class MenuConfig:
    """Конфигурация меню"""

    id: str
    title: str
    description: str = ""
    columns: int = 1
    admin_only: bool = False
    parse_mode: str = "HTML"
    show_back_button: bool = True
    back_target: Optional[str] = None
    back_button_text: str = "◀️ Назад"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MenuStructure:
    """Структура готового меню"""

    config: MenuConfig
    buttons: List[MenuButton] = field(default_factory=list)

    def add_button(self, button: MenuButton) -> "MenuStructure":
        """Добавить кнопку"""
        self.buttons.append(button)
        self._sort_buttons()
        return self

    def get_visible_buttons(self, is_admin: bool = False) -> List[MenuButton]:
        """Получить видимые кнопки"""
        return [
            btn
            for btn in self.buttons
            if btn.visible and (not btn.admin_only or is_admin)
        ]

    def _sort_buttons(self):
        """Сортировать кнопки по порядку"""
        self.buttons.sort(key=lambda x: x.order)


@dataclass
class MenuResponse:
    """Ответ системы меню"""

    text: str
    keyboard_markup: Any  # InlineKeyboardMarkup
    parse_mode: str = "HTML"

    @property
    def has_keyboard(self) -> bool:
        """Есть ли клавиатура"""
        return self.keyboard_markup is not None


@dataclass
class NavigationState:
    """Состояние навигации пользователя"""

    user_id: int
    current_menu: Optional[str] = None
    history: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def navigate_to(self, menu_id: str):
        """Перейти к меню"""
        if self.current_menu and self.current_menu != menu_id:
            if not self.history or self.history[-1] != self.current_menu:
                self.history.append(self.current_menu)

        self.current_menu = menu_id

        # Ограничиваем историю
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def go_back(self) -> Optional[str]:
        """Вернуться назад"""
        if self.history:
            previous = self.history.pop()
            self.current_menu = previous
            return previous
        return None

    def clear(self):
        """Очистить состояние"""
        self.current_menu = None
        self.history.clear()
        self.context.clear()


@dataclass
class MenuItem:
    text: str
    callback_data: Optional[str] = None
    url: Optional[str] = None
    icon: str = ""
    admin_only: bool = False

    @property
    def button_text(self) -> str:
        """Текст кнопки с иконкой"""
        return f"{self.icon} {self.text}".strip() if self.icon else self.text


@dataclass
class Menu:
    """Модель меню"""

    config: MenuConfig
    buttons: List[MenuButton] = field(default_factory=list)

    def add_button(self, button: MenuButton) -> "Menu":
        """Добавить кнопку в меню"""
        self.buttons.append(button)
        self._sort_buttons()
        return self

    def add_buttons(self, buttons: List[MenuButton]) -> "Menu":
        """Добавить сразу несколько кнопок"""
        self.buttons.extend(buttons)
        self._sort_buttons()
        return self

    def _sort_buttons(self):
        """Сортировать кнопки по order"""
        self.buttons.sort(key=lambda b: b.order)

    def get_visible_buttons(self, is_admin: bool = False) -> List[MenuButton]:
        """Вернуть только те кнопки, которые видимы пользователю"""
        return [b for b in self.buttons if b.visible and (not b.admin_only or is_admin)]

    def to_structure(self) -> MenuStructure:
        """Преобразовать в MenuStructure для рендера"""
        return MenuStructure(config=self.config, buttons=self.buttons)


# Типы для кастомизации
MenuValidator = Callable[[MenuStructure, int], bool]
MenuRenderer = Callable[[MenuStructure, Dict[str, Any]], MenuResponse]
ButtonProcessor = Callable[[MenuButton, Dict[str, Any]], MenuButton]
