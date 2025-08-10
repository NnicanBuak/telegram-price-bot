from typing import Dict, List, Optional, Callable, Any, Union
from aiogram.types import CallbackQuery, Message

from .models import MenuStructure, NavigationState, ButtonType
from .renderer import MenuRenderer, MenuSender


class MenuManager:
    """Менеджер системы меню"""

    def __init__(self, admin_user_ids: List[int]):
        self.admin_user_ids = admin_user_ids

        # Компоненты системы
        self.renderer = MenuRenderer(admin_user_ids)
        self.sender = MenuSender(self.renderer)

        # Хранилища
        self._menus: Dict[str, MenuStructure] = {}
        self._user_states: Dict[int, NavigationState] = {}
        self._callback_handlers: Dict[str, Callable] = {}
        self._menu_handlers: Dict[str, Callable] = {}

        # Регистрируем базовый обработчик навигации
        self._register_navigation_handler()

    # === РЕГИСТРАЦИЯ МЕНЮ ===

    def register_menu(self, menu: MenuStructure) -> "MenuManager":
        """Зарегистрировать меню"""
        self._menus[menu.config.id] = menu
        return self

    def get_menu(self, menu_id: str) -> Optional[MenuStructure]:
        """Получить меню по ID"""
        return self._menus.get(menu_id)

    def has_menu(self, menu_id: str) -> bool:
        """Проверить существование меню"""
        return menu_id in self._menus

    # === НАВИГАЦИЯ ===

    async def navigate_to(
        self,
        menu_id: str,
        target: Union[Message, CallbackQuery],
        user_id: int,
        context: Dict[str, Any] = None,
    ) -> bool:
        """Перейти к меню"""
        menu = self.get_menu(menu_id)
        if not menu:
            if isinstance(target, CallbackQuery):
                await target.answer(f"❌ Меню '{menu_id}' не найдено", show_alert=True)
            return False

        # Проверяем доступ
        if menu.config.admin_only and user_id not in self.admin_user_ids:
            if isinstance(target, CallbackQuery):
                await target.answer("❌ Доступ запрещён", show_alert=True)
            return False

        # Обновляем состояние навигации
        state = self._get_user_state(user_id)
        state.navigate_to(menu_id)

        # Обогащаем контекст
        context = context or {}
        context.update(
            {
                "user_id": user_id,
                "current_menu": menu_id,
                "navigation_history": state.history.copy(),
                "is_admin": user_id in self.admin_user_ids,
            }
        )

        # Отправляем меню
        success = await self.sender.send_menu(menu, target, user_id, context)

        if success:
            # Вызываем обработчик меню если есть
            if menu_id in self._menu_handlers:
                try:
                    await self._menu_handlers[menu_id](target, user_id, context)
                except Exception as e:
                    print(f"Ошибка в обработчике меню {menu_id}: {e}")

        return success

    async def go_back(
        self,
        target: Union[Message, CallbackQuery],
        user_id: int,
        context: Dict[str, Any] = None,
    ) -> bool:
        """Вернуться к предыдущему меню"""
        state = self._get_user_state(user_id)
        previous_menu = state.go_back()

        if previous_menu:
            return await self.navigate_to(previous_menu, target, user_id, context)
        else:
            # Возвращаемся к главному меню
            return await self.navigate_to("main", target, user_id, context)

    def get_current_menu(self, user_id: int) -> Optional[str]:
        """Получить текущее меню пользователя"""
        state = self._get_user_state(user_id)
        return state.current_menu

    def clear_navigation(self, user_id: int):
        """Очистить навигацию пользователя"""
        if user_id in self._user_states:
            self._user_states[user_id].clear()

    # === ОБРАБОТЧИКИ ===

    def register_callback_handler(
        self,
        callback_data: str,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Any],
    ) -> "MenuManager":
        """Зарегистрировать обработчик callback_data"""
        self._callback_handlers[callback_data] = handler
        return self

    def register_menu_handler(
        self,
        menu_id: str,
        handler: Callable[[Union[Message, CallbackQuery], int, Dict[str, Any]], Any],
    ) -> "MenuManager":
        """Зарегистрировать обработчик открытия меню"""
        self._menu_handlers[menu_id] = handler
        return self

    async def handle_callback(
        self, callback: CallbackQuery, context: Dict[str, Any] = None
    ) -> bool:
        """Обработать callback запрос"""
        callback_data = callback.data
        user_id = callback.from_user.id
        context = context or {}

        # Проверяем навигацию между меню
        if callback_data.startswith("menu_"):
            menu_id = callback_data[5:]  # Убираем "menu_"
            return await self.navigate_to(menu_id, callback, user_id, context)

        # Специальные команды
        if callback_data == "back":
            return await self.go_back(callback, user_id, context)

        # Зарегистрированные обработчики
        if callback_data in self._callback_handlers:
            try:
                await self._callback_handlers[callback_data](callback, context)
                return True
            except Exception as e:
                await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
                return False

        # Паттерн-матчинг для обработчиков
        for pattern, handler in self._callback_handlers.items():
            if self._match_pattern(callback_data, pattern):
                try:
                    await handler(callback, context)
                    return True
                except Exception as e:
                    await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
                    return False

        return False

    # === СОСТОЯНИЕ ===

    def _get_user_state(self, user_id: int) -> NavigationState:
        """Получить состояние пользователя"""
        if user_id not in self._user_states:
            self._user_states[user_id] = NavigationState(user_id=user_id)
        return self._user_states[user_id]

    def get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Получить контекст пользователя"""
        state = self._get_user_state(user_id)
        return state.context.copy()

    def set_user_context(self, user_id: int, **context):
        """Установить контекст пользователя"""
        state = self._get_user_state(user_id)
        state.context.update(context)

    def clear_user_context(self, user_id: int):
        """Очистить контекст пользователя"""
        state = self._get_user_state(user_id)
        state.context.clear()

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _register_navigation_handler(self):
        """Регистрируем базовый обработчик навигации"""

        async def navigation_handler(callback: CallbackQuery, context: Dict[str, Any]):
            # Этот обработчик уже выполнен в handle_callback
            pass

        # Регистрируем для всех паттернов навигации
        self.register_callback_handler("menu_*", navigation_handler)

    def _match_pattern(self, callback_data: str, pattern: str) -> bool:
        """Проверить соответствие паттерну"""
        if "*" not in pattern:
            return callback_data == pattern

        # Простой wildcard matching
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return callback_data.startswith(prefix)

        if pattern.startswith("*"):
            suffix = pattern[1:]
            return callback_data.endswith(suffix)

        return False

    # === УТИЛИТЫ ===

    def get_menu_statistics(self) -> Dict[str, Any]:
        """Получить статистику меню"""
        return {
            "total_menus": len(self._menus),
            "active_users": len(self._user_states),
            "menu_list": list(self._menus.keys()),
            "callback_handlers": len(self._callback_handlers),
        }

    def export_navigation_state(self, user_id: int) -> Dict[str, Any]:
        """Экспортировать состояние навигации"""
        if user_id not in self._user_states:
            return {}

        state = self._user_states[user_id]
        return {
            "user_id": state.user_id,
            "current_menu": state.current_menu,
            "history": state.history.copy(),
            "context": state.context.copy(),
        }

    def import_navigation_state(self, user_id: int, state_data: Dict[str, Any]):
        """Импортировать состояние навигации"""
        state = NavigationState(
            user_id=user_id,
            current_menu=state_data.get("current_menu"),
            history=state_data.get("history", []).copy(),
            context=state_data.get("context", {}).copy(),
        )
        self._user_states[user_id] = state


class MenuRegistry:
    """Реестр меню для организации"""

    def __init__(self, menu_manager: MenuManager):
        self.menu_manager = menu_manager
        self._menu_groups: Dict[str, List[str]] = {}

    def register_menu_group(self, group_name: str, menu_ids: List[str]):
        """Зарегистрировать группу меню"""
        self._menu_groups[group_name] = menu_ids

    def get_menu_group(self, group_name: str) -> List[MenuStructure]:
        """Получить меню группы"""
        menu_ids = self._menu_groups.get(group_name, [])
        menus = []

        for menu_id in menu_ids:
            menu = self.menu_manager.get_menu(menu_id)
            if menu:
                menus.append(menu)

        return menus

    def register_feature_menus(self, feature_name: str, menus: List[MenuStructure]):
        """Зарегистрировать меню feature"""
        menu_ids = []

        for menu in menus:
            self.menu_manager.register_menu(menu)
            menu_ids.append(menu.config.id)

        self.register_menu_group(feature_name, menu_ids)


# === ДЕКОРАТОРЫ ДЛЯ УПРОЩЕНИЯ ===


def menu_handler(menu_manager: MenuManager, callback_pattern: str):
    """Декоратор для регистрации обработчика"""

    def decorator(func):
        menu_manager.register_callback_handler(callback_pattern, func)
        return func

    return decorator


def menu_opener(menu_manager: MenuManager, menu_id: str):
    """Декоратор для обработчика открытия меню"""

    def decorator(func):
        menu_manager.register_menu_handler(menu_id, func)
        return func

    return decorator
