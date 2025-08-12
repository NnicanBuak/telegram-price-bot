import logging
from aiogram import Router, F, types
from menu import MenuBuilder, create_crud_menu, menu_handler

logger = logging.getLogger(__name__)


def setup_menus(menu_manager) -> None:
    """Настройка основных меню системы"""

    # Главное меню
    main_menu = (
        MenuBuilder("main")
        .title("🏠 Главное меню")
        .description(
            "Добро пожаловать в Telegram Price Bot!\n\n"
            "🆕 <b>Обновления:</b>\n"
            "✅ Новая архитектура сервисов\n"
            "✅ Программное управление меню\n"
            "✅ Улучшенная производительность\n\n"
            "Выберите нужную функцию:"
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
        .add_action("📊 Статистика", "templates_stats", "📊")
        .add_action("📤 Экспорт", "templates_export", "📤", admin_only=True)
        .add_action("📥 Импорт", "templates_import", "📥", admin_only=True)
        .back_button("main")
        .build()
    )

    # CRUD меню для групп
    groups_menu = (
        create_crud_menu("groups", "👥 Управление группами чатов")
        .add_action("📊 Статистика", "groups_stats", "📊")
        .add_action("🔍 Поиск чата", "groups_search_chat", "🔍")
        .add_action("📤 Экспорт", "groups_export", "📤", admin_only=True)
        .back_button("main")
        .build()
    )

    # Меню рассылки
    mailing_menu = (
        MenuBuilder("mailing")
        .title("📮 Рассылка сообщений")
        .description(
            "Создавайте и запускайте рассылки по группам чатов.\n"
            "Новые возможности:\n"
            "✅ Улучшенная статистика\n"
            "✅ Тестовые отправки\n"
            "✅ Оценка времени выполнения\n\n"
            "Выберите действие:"
        )
        .add_action("📮 Создать рассылку", "mailing_create")
        .add_action("📊 История рассылок", "mailings_history")
        .add_action("📈 Статистика", "mailing_stats")
        .add_action("🧪 Тестирование", "mailing_test", admin_only=True)
        .back_button("main")
        .build()
    )

    # Меню настроек
    settings_menu = (
        MenuBuilder("settings")
        .title("⚙️ Настройки системы")
        .description("Управление конфигурацией и мониторинг системы.")
        .admin_only(True)
        .add_action("📊 Статус системы", "system_status")
        .add_action("📋 Конфигурация", "system_config")
        .add_action("📝 Логи", "system_logs")
        .add_action("💾 База данных", "system_database")
        .add_action("🔄 Резервные копии", "system_backup")
        .add_action("🧹 Очистка", "system_cleanup")
        .add_action("❤️ Проверка здоровья", "system_health")
        .back_button("main")
        .build()
    )

    # Регистрируем все меню
    for menu in [main_menu, templates_menu, groups_menu, mailing_menu, settings_menu]:
        menu_manager.register_menu(menu)

    logger.info("✅ Основные меню зарегистрированы")


def get_router(deps) -> Router:
    """Возвращает роутер с навигацией между меню и системными действиями"""
    router = Router()

    @router.callback_query(F.data.startswith("menu_") | F.data == "back")
    async def handle_menu_navigation(callback: types.CallbackQuery):
        """Автоматическая навигация между меню"""
        success = await deps.menu_manager.handle_callback(callback)
        if not success:
            await callback.answer("❌ Меню не найдено", show_alert=True)

    # === СИСТЕМНЫЕ ДЕЙСТВИЯ ===

    @menu_handler(deps.menu_manager, "system_status")
    async def show_system_status(callback: types.CallbackQuery, context: dict):
        """Показать статус системы"""
        try:
            # Используем системный сервис
            system_service = context.get("system_service")
            if not system_service:
                await callback.answer("❌ Системный сервис недоступен", show_alert=True)
                return

            status = system_service.get_system_status()

            status_text = "📊 <b>Статус системы</b>\n\n"

            if "error" in status:
                status_text += f"❌ Ошибка: {status['error']}"
            else:
                status_text += f"⏰ <b>Время работы:</b> {status['uptime_formatted']}\n"
                status_text += f"💾 <b>Память:</b> {status['memory']['rss_mb']} MB ({status['memory']['percent']}%)\n"
                status_text += f"⚡ <b>CPU:</b> {status['cpu_percent']}%\n\n"

                status_text += "<b>💽 Диски:</b>\n"
                for disk_name, disk_info in status["disk_usage"].items():
                    if "error" in disk_info:
                        status_text += f"  • {disk_name}: {disk_info['error']}\n"
                    else:
                        status_text += f"  • {disk_name}: {disk_info['percent']}% ({disk_info['free'] // 1024 // 1024} MB свободно)\n"

            await callback.message.edit_text(
                status_text,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="🔄 Обновить", callback_data="system_status"
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="◀️ Назад", callback_data="menu_settings"
                            )
                        ],
                    ]
                ),
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка получения статуса системы: {e}")
            await callback.answer("❌ Ошибка загрузки статуса", show_alert=True)

    @menu_handler(deps.menu_manager, "system_health")
    async def show_system_health(callback: types.CallbackQuery, context: dict):
        """Показать проверку здоровья системы"""
        try:
            system_service = context.get("system_service")
            if not system_service:
                await callback.answer("❌ Системный сервис недоступен", show_alert=True)
                return

            health = await system_service.get_health_check()

            # Иконки статусов
            status_icons = {
                "healthy": "✅",
                "warning": "⚠️",
                "unhealthy": "❌",
                "error": "💥",
            }

            check_icons = {"ok": "✅", "warning": "⚠️", "error": "❌"}

            health_text = f"❤️ <b>Проверка здоровья системы</b>\n\n"
            health_text += f"{status_icons.get(health['status'], '❓')} <b>Общий статус:</b> {health['status']}\n\n"

            if "checks" in health:
                health_text += "<b>🔍 Детальные проверки:</b>\n"
                for check_name, check_result in health["checks"].items():
                    icon = check_icons.get(check_result["status"], "❓")
                    health_text += (
                        f"{icon} <b>{check_name}:</b> {check_result['message']}\n"
                    )

            if "error" in health:
                health_text += f"\n💥 <b>Ошибка:</b> {health['error']}"

            await callback.message.edit_text(
                health_text,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="🔄 Обновить", callback_data="system_health"
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="◀️ Назад", callback_data="menu_settings"
                            )
                        ],
                    ]
                ),
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка проверки здоровья системы: {e}")
            await callback.answer("❌ Ошибка проверки здоровья", show_alert=True)

    # === СТАТИСТИКА СЕРВИСОВ ===

    @menu_handler(deps.menu_manager, "templates_stats")
    async def show_templates_stats(callback: types.CallbackQuery, context: dict):
        """Показать статистику шаблонов"""
        try:
            templates_service = context.get("templates_service")
            if not templates_service:
                await callback.answer("❌ Сервис шаблонов недоступен", show_alert=True)
                return

            stats = await templates_service.get_template_statistics()

            stats_text = "📊 <b>Статистика шаблонов</b>\n\n"
            stats_text += f"📝 <b>Всего шаблонов:</b> {stats['total_count']}\n"
            stats_text += f"📎 <b>С файлами:</b> {stats['with_files']}\n"
            stats_text += (
                f"📏 <b>Средняя длина:</b> {stats['average_text_length']} символов\n"
            )
            stats_text += f"🆕 <b>Создано сегодня:</b> {stats['created_today']}\n\n"

            if stats["file_types"]:
                stats_text += "<b>📁 Типы файлов:</b>\n"
                for file_type, count in stats["file_types"].items():
                    stats_text += f"  • {file_type}: {count}\n"

            await callback.message.edit_text(
                stats_text,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="🔄 Обновить", callback_data="templates_stats"
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="◀️ Назад", callback_data="menu_templates"
                            )
                        ],
                    ]
                ),
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка получения статистики шаблонов: {e}")
            await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)

    @menu_handler(deps.menu_manager, "groups_stats")
    async def show_groups_stats(callback: types.CallbackQuery, context: dict):
        """Показать статистику групп"""
        try:
            groups_service = context.get("groups_service")
            if not groups_service:
                await callback.answer("❌ Сервис групп недоступен", show_alert=True)
                return

            stats = await groups_service.get_group_statistics()

            stats_text = "📊 <b>Статистика групп</b>\n\n"

            if stats["total_groups"] == 0:
                stats_text += "❌ Групп не найдено"
            else:
                stats_text += f"👥 <b>Всего групп:</b> {stats['total_groups']}\n"
                stats_text += f"💬 <b>Всего чатов:</b> {stats['total_chats']}\n"
                stats_text += f"🔢 <b>Уникальных чатов:</b> {stats['unique_chats']}\n"
                stats_text += f"📊 <b>Среднее чатов на группу:</b> {stats['average_chats_per_group']:.1f}\n"
                stats_text += f"📂 <b>Пустых групп:</b> {stats['empty_groups']}\n\n"

                stats_text += "<b>🏆 Размеры групп:</b>\n"
                stats_text += f"  • Самая большая: {stats['largest_group']['name']} ({stats['largest_group']['size']} чатов)\n"
                stats_text += f"  • Самая маленькая: {stats['smallest_group']['name']} ({stats['smallest_group']['size']} чатов)\n"

            await callback.message.edit_text(
                stats_text,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="🔄 Обновить", callback_data="groups_stats"
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="◀️ Назад", callback_data="menu_groups"
                            )
                        ],
                    ]
                ),
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка получения статистики групп: {e}")
            await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)

    @menu_handler(deps.menu_manager, "mailing_stats")
    async def show_mailing_stats(callback: types.CallbackQuery, context: dict):
        """Показать статистику рассылок"""
        try:
            mailing_service = context.get("mailing_service")
            if not mailing_service:
                await callback.answer("❌ Сервис рассылки недоступен", show_alert=True)
                return

            stats = await mailing_service.get_mailing_statistics()

            stats_text = "📊 <b>Статистика рассылок</b>\n\n"
            stats_text += f"📮 <b>Всего рассылок:</b> {stats['total_mailings']}\n"
            stats_text += f"✅ <b>Завершенных:</b> {stats['completed_mailings']}\n"
            stats_text += f"❌ <b>Неудачных:</b> {stats['failed_mailings']}\n"
            stats_text += f"🔄 <b>Активных:</b> {stats['active_mailings']}\n"
            stats_text += (
                f"📨 <b>Отправлено сообщений:</b> {stats['total_messages_sent']}\n"
            )
            stats_text += f"📈 <b>Успешность:</b> {stats['success_rate']}%\n"

            await callback.message.edit_text(
                stats_text,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="🔄 Обновить", callback_data="mailing_stats"
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="◀️ Назад", callback_data="menu_mailing"
                            )
                        ],
                    ]
                ),
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка получения статистики рассылок: {e}")
            await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)

    # === НАВИГАЦИЯ МЕЖДУ МЕНЮ ===

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
