"""
Исправленные обработчики меню для Telegram Price Bot
Убрана проблема с импортом db из main и добавлено правильное dependency injection
"""

import re
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from database import Database
    from menu_system import MenuManager
    from bot.menus import BotMenus

# Создаем роутер для обработчиков меню
menu_router = Router()

# ========== FSM СОСТОЯНИЯ ==========


class TemplateStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_text = State()
    waiting_for_file = State()


class GroupStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_chats = State()


class MailingStates(StatesGroup):
    selecting_template = State()
    selecting_groups = State()
    confirming = State()


# ========== КОМАНДЫ ==========


@menu_router.message(Command("start"))
async def cmd_start(message: types.Message, menu_manager: "MenuManager"):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    text, keyboard = menu_manager.render_menu("main", user_id)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@menu_router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = """
🤖 <b>Telegram Price Bot - Справка</b>

<b>📋 Основные функции:</b>
• Создание шаблонов сообщений с файлами
• Управление группами чатов для рассылки
• Автоматическая рассылка по выбранным группам
• История и статистика рассылок

<b>🚀 Быстрый старт:</b>
1. Создайте шаблон сообщения
2. Создайте группу чатов для рассылки
3. Запустите рассылку, выбрав шаблон и группы

<b>📝 Примечания:</b>
• Бот должен быть администратором в чатах
• Можно прикреплять файлы к шаблонам
• Поддерживается HTML разметка в тексте
    """
    await message.answer(help_text, parse_mode="HTML")


@menu_router.message(Command("templates"))
async def cmd_templates(message: types.Message, menu_manager: "MenuManager"):
    """Обработчик команды /templates"""
    user_id = message.from_user.id
    text, keyboard = menu_manager.render_menu("templates", user_id)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@menu_router.message(Command("groups"))
async def cmd_groups(message: types.Message, menu_manager: "MenuManager"):
    """Обработчик команды /groups"""
    user_id = message.from_user.id
    text, keyboard = menu_manager.render_menu("groups", user_id)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@menu_router.message(Command("mailing"))
async def cmd_mailing(message: types.Message, menu_manager: "MenuManager"):
    """Обработчик команды /mailing"""
    user_id = message.from_user.id
    text, keyboard = menu_manager.render_menu("mailing", user_id)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@menu_router.message(Command("history"))
async def cmd_history(message: types.Message, menu_manager: "MenuManager"):
    """Обработчик команды /history"""
    user_id = message.from_user.id
    text, keyboard = menu_manager.render_menu("history", user_id)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@menu_router.message(Command("id"))
async def cmd_id(message: types.Message):
    """Обработчик команды /id - получение ID чата"""
    chat_info = f"💬 <b>Информация о чате:</b>\n\n"
    chat_info += f"ID: <code>{message.chat.id}</code>\n"
    chat_info += f"Тип: {message.chat.type}\n"

    if message.chat.type != "private":
        chat_info += f"Название: {message.chat.title or 'Без названия'}\n"
        if message.chat.username:
            chat_info += f"Username: @{message.chat.username}\n"

    chat_info += f"\n<b>Пользователь:</b>\n"
    chat_info += f"ID: <code>{message.from_user.id}</code>\n"
    chat_info += f"Имя: {message.from_user.first_name}"

    if message.from_user.last_name:
        chat_info += f" {message.from_user.last_name}"

    if message.from_user.username:
        chat_info += f"\nUsername: @{message.from_user.username}"

    await message.answer(chat_info, parse_mode="HTML")


# ========== ОСНОВНЫЕ CALLBACK ОБРАБОТЧИКИ ==========


@menu_router.callback_query(F.data.startswith("menu_"))
async def handle_menu_navigation(
    callback: types.CallbackQuery, menu_manager: "MenuManager"
):
    """Обработчик навигации по меню"""
    menu_id = callback.data.replace("menu_", "")
    success = await menu_manager.navigate_to(menu_id, callback)
    if not success:
        await callback.answer("Ошибка навигации", show_alert=True)


@menu_router.callback_query(F.data == "templates_list")
async def handle_templates_list(
    callback: types.CallbackQuery,
    menu_manager: "MenuManager",
    db: "Database",
    bot_menus: "BotMenus",
):
    """Обработчик списка шаблонов"""
    await bot_menus.create_templates_list_menu(db)
    await menu_manager.navigate_to("templates_list", callback)


@menu_router.callback_query(F.data == "groups_list")
async def handle_groups_list(
    callback: types.CallbackQuery,
    menu_manager: "MenuManager",
    db: "Database",
    bot_menus: "BotMenus",
):
    """Обработчик списка групп"""
    await bot_menus.create_groups_list_menu(db)
    await menu_manager.navigate_to("groups_list", callback)


# ========== РАБОТА С ШАБЛОНАМИ ==========


@menu_router.callback_query(F.data == "templates_new")
async def handle_new_template(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик создания нового шаблона"""
    await callback.message.edit_text(
        "📋 <b>Создание нового шаблона</b>\n\n" "Введите название для нового шаблона:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="templates_list")]
            ]
        ),
        parse_mode="HTML",
    )
    await state.set_state(TemplateStates.waiting_for_name)
    await callback.answer()


@menu_router.message(TemplateStates.waiting_for_name)
async def template_name_received(message: types.Message, state: FSMContext):
    """Получение названия шаблона"""
    if len(message.text) > 100:
        await message.answer(
            "❌ Название слишком длинное. Максимум 100 символов. Попробуйте еще раз:"
        )
        return

    await state.update_data(name=message.text)
    await message.answer(
        "📝 <b>Введите текст шаблона:</b>\n\n"
        "Поддерживается HTML разметка:\n"
        "• <code>&lt;b&gt;жирный&lt;/b&gt;</code>\n"
        "• <code>&lt;i&gt;курсив&lt;/i&gt;</code>\n"
        "• <code>&lt;u&gt;подчеркнутый&lt;/u&gt;</code>\n"
        "• <code>&lt;code&gt;моноширинный&lt;/code&gt;</code>",
        parse_mode="HTML",
    )
    await state.set_state(TemplateStates.waiting_for_text)


@menu_router.message(TemplateStates.waiting_for_text)
async def template_text_received(
    message: types.Message, state: FSMContext, db: "Database"
):
    """Получение текста шаблона"""
    if len(message.text) > 4096:
        await message.answer(
            "❌ Текст слишком длинный. Максимум 4096 символов. Попробуйте еще раз:"
        )
        return

    await state.update_data(text=message.text)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📎 Прикрепить файл", callback_data="template_add_file"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Сохранить без файла", callback_data="template_save_no_file"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="templates_list")],
        ]
    )

    await message.answer(
        "📎 <b>Хотите прикрепить файл к шаблону?</b>\n\n"
        "Файл будет отправляться вместе с текстом сообщения.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@menu_router.callback_query(F.data == "template_save_no_file")
async def save_template_without_file(
    callback: types.CallbackQuery, state: FSMContext, db: "Database"
):
    """Сохранение шаблона без файла"""
    data = await state.get_data()

    try:
        template = await db.create_template(name=data["name"], text=data["text"])

        success_text = f"✅ <b>Шаблон создан!</b>\n\n"
        success_text += f"📋 Название: {template.name}\n"
        success_text += f"📄 Символов: {len(template.text)}\n"
        success_text += f"🕐 Создан: {template.created_at.strftime('%d.%m.%Y %H:%M')}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 К списку", callback_data="templates_list"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ Создать еще", callback_data="templates_new"
                    )
                ],
            ]
        )

        await callback.message.edit_text(
            success_text, reply_markup=keyboard, parse_mode="HTML"
        )
        await state.clear()

    except Exception as e:
        await callback.answer(f"❌ Ошибка при сохранении: {e}", show_alert=True)


@menu_router.callback_query(F.data.startswith("template_delete_"))
async def handle_template_delete(callback: types.CallbackQuery, db: "Database"):
    """Обработчик удаления шаблона"""
    template_id = int(callback.data.replace("template_delete_", ""))
    success = await db.delete_template(template_id)

    if success:
        await callback.message.edit_text(
            "✅ <b>Шаблон удален!</b>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📋 К списку", callback_data="templates_list"
                        )
                    ]
                ]
            ),
            parse_mode="HTML",
        )
    else:
        await callback.answer("Ошибка при удалении шаблона", show_alert=True)

    await callback.answer()


# ========== РАБОТА С ГРУППАМИ ==========


@menu_router.callback_query(F.data.startswith("group_view_"))
async def handle_group_view(callback: types.CallbackQuery, db: "Database"):
    """Обработчик просмотра группы"""
    group_id = int(callback.data.replace("group_view_", ""))
    group = await db.get_chat_group(group_id)

    if not group:
        await callback.answer("Группа не найдена", show_alert=True)
        return

    text = f"👥 <b>{group.name}</b>\n\n"
    text += f"📊 <b>Количество чатов:</b> {len(group.chat_ids)}\n\n"

    if group.chat_ids:
        text += "<b>Список чатов:</b>\n"
        for i, chat_id in enumerate(
            group.chat_ids[:10], 1
        ):  # Показываем только первые 10
            text += f"{i}. <code>{chat_id}</code>\n"

        if len(group.chat_ids) > 10:
            text += f"... и еще {len(group.chat_ids) - 10} чатов\n"
    else:
        text += "<i>Чаты не добавлены</i>\n"

    text += f"\n📅 Создана: {group.created_at.strftime('%d.%m.%Y %H:%M')}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data=f"group_edit_{group_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить", callback_data=f"group_delete_{group_id}"
                ),
            ],
            [InlineKeyboardButton(text="🔙 К списку", callback_data="groups_list")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@menu_router.callback_query(F.data == "groups_new")
async def handle_new_group(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик создания новой группы"""
    await callback.message.edit_text(
        "👥 <b>Создание новой группы чатов</b>\n\n"
        "Введите название для новой группы:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="groups_list")]
            ]
        ),
        parse_mode="HTML",
    )
    await state.set_state(GroupStates.waiting_for_name)
    await callback.answer()


@menu_router.message(GroupStates.waiting_for_name)
async def group_name_received(message: types.Message, state: FSMContext):
    """Получение названия группы"""
    if len(message.text) > 100:
        await message.answer(
            "❌ Название слишком длинное. Максимум 100 символов. Попробуйте еще раз:"
        )
        return

    await state.update_data(name=message.text)
    await message.answer(
        "📝 <b>Введите ID чатов через запятую:</b>\n\n"
        "<b>Пример:</b>\n"
        "<code>-1001234567890, -1009876543210</code>\n\n"
        "💡 <b>Как получить ID чата:</b>\n"
        "1. Добавьте бота в чат как администратора\n"
        "2. Отправьте команду <code>/id</code> в чате\n"
        "3. Скопируйте полученный ID",
        parse_mode="HTML",
    )
    await state.set_state(GroupStates.waiting_for_chats)


@menu_router.message(GroupStates.waiting_for_chats)
async def group_chats_received(
    message: types.Message, state: FSMContext, db: "Database"
):
    """Получение списка чатов"""
    try:
        text = message.text.strip()
        chat_ids = parse_chat_ids(text)

        if not chat_ids:
            await message.answer(
                "❌ Не удалось распознать ID чатов.\n"
                "Убедитесь, что используете правильный формат:\n"
                "<code>-1001234567890, -1009876543210</code>",
                parse_mode="HTML",
            )
            return

        if len(chat_ids) > 50:
            await message.answer(
                "❌ Слишком много чатов! "
                "Максимум 50 чатов в группе.\n"
                "Попробуйте еще раз:"
            )
            return

        # Сохраняем группу - теперь db передается через middleware!
        data = await state.get_data()
        group = await db.create_chat_group(name=data["name"], chat_ids=chat_ids)

        success_text = f"✅ <b>Группа создана!</b>\n\n"
        success_text += f"👥 Название: {group.name}\n"
        success_text += f"📊 Количество чатов: {len(group.chat_ids)}\n"
        success_text += f"🕐 Создана: {group.created_at.strftime('%d.%m.%Y %H:%M')}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👥 К списку групп", callback_data="groups_list"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ Создать еще одну", callback_data="groups_new"
                    )
                ],
            ]
        )

        await message.answer(success_text, reply_markup=keyboard, parse_mode="HTML")
        await state.clear()

    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка при создании группы:</b>\n{str(e)}", parse_mode="HTML"
        )


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========


def parse_chat_ids(text: str) -> List[int]:
    """Парсинг ID чатов из текста"""
    chat_ids = []

    # Удаляем все символы кроме цифр, минусов и запятых
    cleaned_text = re.sub(r"[^\d\-,\s]", "", text)

    # Разделяем по запятым
    parts = cleaned_text.split(",")

    for part in parts:
        part = part.strip()
        if part:
            try:
                chat_id = int(part)
                if chat_id != 0:  # Исключаем нулевые ID
                    chat_ids.append(chat_id)
            except ValueError:
                continue

    return list(set(chat_ids))  # Удаляем дубликаты


# ========== ВОЗВРАТ В МЕНЮ ==========


@menu_router.callback_query(F.data == "back_to_menu")
async def handle_back_to_menu(
    callback: types.CallbackQuery, menu_manager: "MenuManager"
):
    """Обработчик возврата в главное меню"""
    await menu_manager.navigate_to("main", callback)


# ========== ФУНКЦИИ РЕГИСТРАЦИИ ==========


def register_menu_handlers(
    dp, menu_manager: "MenuManager", db: "Database", bot_menus: "BotMenus"
):
    """Регистрация всех обработчиков меню"""

    # Создаем middleware для внедрения зависимостей
    async def inject_dependencies(handler, event, data):
        """Middleware для внедрения зависимостей в обработчики"""
        # Добавляем все необходимые зависимости в контекст
        data.update({"menu_manager": menu_manager, "db": db, "bot_menus": bot_menus})
        return await handler(event, data)

    # Регистрируем middleware для сообщений и callback'ов
    menu_router.message.middleware.register(inject_dependencies)
    menu_router.callback_query.middleware.register(inject_dependencies)

    # Регистрируем роутер
    dp.include_router(menu_router)


def setup_menu_handlers():
    """Настройка обработчиков меню"""
    return menu_router
