"""
Обработчики меню для Telegram Price Bot
"""

from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from menu_system import MenuManager
    from database import Database
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
<b>📚 Доступные команды:</b>

/start - Главное меню
/help - Эта справка
/templates - Управление шаблонами
/groups - Управление группами чатов
/mailing - Создать рассылку
/history - История рассылок
/id - Получить ID чата

<b>💡 Как пользоваться:</b>
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


@menu_router.callback_query(F.data == "mailing_start")
async def handle_mailing_start(
    callback: types.CallbackQuery,
    menu_manager: "MenuManager",
    db: "Database",
    bot_menus: "BotMenus",
):
    """Обработчик начала рассылки"""
    await bot_menus.create_mailing_template_selection_menu(db)
    await menu_manager.navigate_to("mailing_template_selection", callback)


@menu_router.callback_query(F.data == "history_recent")
async def handle_history_recent(
    callback: types.CallbackQuery,
    menu_manager: "MenuManager",
    db: "Database",
    bot_menus: "BotMenus",
):
    """Обработчик истории рассылок"""
    await bot_menus.create_history_list_menu(db)
    await menu_manager.navigate_to("history_list", callback)


# ========== РАБОТА С ШАБЛОНАМИ ==========


@menu_router.callback_query(F.data.startswith("template_view_"))
async def handle_template_view(callback: types.CallbackQuery, db: "Database"):
    """Обработчик просмотра шаблона"""
    template_id = int(callback.data.replace("template_view_", ""))
    template = await db.get_template(template_id)

    if not template:
        await callback.answer("Шаблон не найден", show_alert=True)
        return

    text = f"📄 <b>{template.name}</b>\n\n"
    text += f"<i>Текст шаблона:</i>\n{template.text}\n\n"

    if template.file_id:
        file_type = (
            "📎 Документ" if template.file_type == "document" else "🖼 Изображение"
        )
        text += f"{file_type}: Прикреплен\n\n"

    text += f"📅 Создан: {template.created_at.strftime('%d.%m.%Y %H:%M')}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать", callback_data=f"template_edit_{template_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить", callback_data=f"template_delete_{template_id}"
                ),
            ],
            [InlineKeyboardButton(text="🔙 К списку", callback_data="templates_list")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@menu_router.callback_query(F.data == "templates_new")
async def handle_new_template(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик создания нового шаблона"""
    await callback.message.edit_text(
        "📝 <b>Создание нового шаблона</b>\n\n" "Введите название для нового шаблона:",
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
            "❌ Название слишком длинное. Максимум 100 символов.\n"
            "Попробуйте еще раз:"
        )
        return

    await state.update_data(name=message.text)
    await message.answer(
        "✏️ <b>Введите текст шаблона:</b>\n\n"
        "<i>Поддерживается HTML разметка:</i>\n"
        "• <code>&lt;b&gt;жирный&lt;/b&gt;</code>\n"
        "• <code>&lt;i&gt;курсив&lt;/i&gt;</code>\n"
        "• <code>&lt;u&gt;подчеркнутый&lt;/u&gt;</code>\n"
        "• <code>&lt;code&gt;моноширинный&lt;/code&gt;</code>",
        parse_mode="HTML",
    )
    await state.set_state(TemplateStates.waiting_for_text)


@menu_router.message(TemplateStates.waiting_for_text)
async def template_text_received(message: types.Message, state: FSMContext):
    """Получение текста шаблона"""
    if len(message.text) > 4000:
        await message.answer(
            "❌ Текст слишком длинный. Максимум 4000 символов.\n" "Попробуйте еще раз:"
        )
        return

    await state.update_data(text=message.text)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📎 Прикрепить файл", callback_data="template_attach_file"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💾 Сохранить без файла", callback_data="template_save"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="templates_list")],
        ]
    )

    await message.answer(
        "📎 <b>Хотите прикрепить файл к шаблону?</b>\n\n"
        "Вы можете прикрепить документ или изображение, "
        "которые будут отправляться вместе с текстом.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@menu_router.callback_query(F.data == "template_attach_file")
async def request_template_file(callback: types.CallbackQuery, state: FSMContext):
    """Запрос файла для шаблона"""
    await callback.message.edit_text(
        "📎 <b>Отправьте файл</b>\n\n"
        "Поддерживаются:\n"
        "• 📄 Документы (PDF, DOC, XLS, etc.)\n"
        "• 🖼 Изображения (JPG, PNG, etc.)\n\n"
        "Максимальный размер: 50 МБ",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="template_save")]
            ]
        ),
        parse_mode="HTML",
    )
    await state.set_state(TemplateStates.waiting_for_file)
    await callback.answer()


@menu_router.message(TemplateStates.waiting_for_file, F.document | F.photo)
async def template_file_received(message: types.Message, state: FSMContext):
    """Получение файла для шаблона"""
    if message.document:
        file_id = message.document.file_id
        file_type = "document"
        file_name = message.document.file_name or "Документ"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
        file_name = "Изображение"

    await state.update_data(file_id=file_id, file_type=file_type, file_name=file_name)
    await save_template_to_db(message, state)


@menu_router.callback_query(F.data == "template_save")
async def save_template_callback(callback: types.CallbackQuery, state: FSMContext):
    """Сохранение шаблона без файла"""
    await save_template_to_db(callback.message, state)
    await callback.answer()


async def save_template_to_db(message: types.Message, state: FSMContext):
    """Сохранение шаблона в БД"""
    from main import db  # Импорт из main

    data = await state.get_data()

    try:
        template = await db.create_template(
            name=data["name"],
            text=data["text"],
            file_id=data.get("file_id"),
            file_type=data.get("file_type"),
        )

        success_text = f"✅ <b>Шаблон создан!</b>\n\n"
        success_text += f"📄 Название: {template.name}\n"
        success_text += f"📝 Символов в тексте: {len(template.text)}\n"

        if template.file_id:
            file_name = data.get("file_name", "файл")
            success_text += f"📎 Прикреплен: {file_name}\n"

        success_text += f"🕐 Создан: {template.created_at.strftime('%d.%m.%Y %H:%M')}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 К списку шаблонов", callback_data="templates_list"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="➕ Создать еще один", callback_data="templates_new"
                    )
                ],
            ]
        )

        await message.answer(success_text, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        await message.answer(
            f"❌ <b>Ошибка при создании шаблона:</b>\n{str(e)}", parse_mode="HTML"
        )

    await state.clear()


@menu_router.callback_query(F.data.startswith("template_delete_"))
async def handle_template_delete(callback: types.CallbackQuery, db: "Database"):
    """Обработчик удаления шаблона"""
    template_id = int(callback.data.replace("template_delete_", ""))
    template = await db.get_template(template_id)

    if not template:
        await callback.answer("Шаблон не найден", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Да, удалить",
                    callback_data=f"template_confirm_delete_{template_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data=f"template_view_{template_id}"
                ),
            ]
        ]
    )

    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"Вы действительно хотите удалить шаблон?\n\n"
        f"📄 <b>{template.name}</b>\n\n"
        f"<i>Это действие нельзя отменить!</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@menu_router.callback_query(F.data.startswith("template_confirm_delete_"))
async def confirm_template_delete(callback: types.CallbackQuery, db: "Database"):
    """Подтверждение удаления шаблона"""
    template_id = int(callback.data.replace("template_confirm_delete_", ""))

    success = await db.delete_template(template_id)

    if success:
        await callback.message.edit_text(
            "✅ <b>Шаблон удален</b>\n\n" "Шаблон успешно удален из базы данных.",
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
            "❌ Название слишком длинное. Максимум 100 символов.\n"
            "Попробуйте еще раз:"
        )
        return

    await state.update_data(name=message.text)
    await message.answer(
        "💬 <b>Введите ID чатов</b>\n\n"
        "Введите ID чатов через запятую или каждый с новой строки.\n\n"
        "<i>Для получения ID чата добавьте бота в чат "
        "и отправьте команду /id</i>\n\n"
        "<b>Пример:</b>\n"
        "<code>-1001234567890, -1009876543210</code>\n"
        "или\n"
        "<code>-1001234567890\n-1009876543210</code>",
        parse_mode="HTML",
    )
    await state.set_state(GroupStates.waiting_for_chats)


@menu_router.message(GroupStates.waiting_for_chats)
async def group_chats_received(message: types.Message, state: FSMContext):
    """Получение ID чатов для группы"""
    try:
        # Парсим ID чатов
        chat_ids_text = message.text.replace("\n", ",")
        chat_ids_raw = [id.strip() for id in chat_ids_text.split(",") if id.strip()]

        chat_ids = []
        for chat_id_str in chat_ids_raw:
            try:
                chat_id = int(chat_id_str)
                if chat_id >= 0:
                    await message.answer(
                        f"❌ Некорректный ID чата: {chat_id}\n"
                        "ID чатов должны быть отрицательными числами.\n\n"
                        "Попробуйте еще раз:"
                    )
                    return
                chat_ids.append(chat_id)
            except ValueError:
                await message.answer(
                    f"❌ Некорректный ID чата: {chat_id_str}\n"
                    "ID должен быть числом.\n\n"
                    "Попробуйте еще раз:"
                )
                return

        if not chat_ids:
            await message.answer(
                "❌ Не указано ни одного ID чата.\n" "Попробуйте еще раз:"
            )
            return

        if len(chat_ids) > 50:
            await message.answer(
                "❌ Слишком много чатов. Максимум 50 чатов в группе.\n"
                "Попробуйте еще раз:"
            )
            return

        # Сохраняем группу
        from main import db

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
    # Добавляем зависимости в middleware
    menu_router.message.middleware.register(
        lambda h, e, d: d.update(
            {"menu_manager": menu_manager, "db": db, "bot_menus": bot_menus}
        )
        or h(e, d)
    )

    menu_router.callback_query.middleware.register(
        lambda h, e, d: d.update(
            {"menu_manager": menu_manager, "db": db, "bot_menus": bot_menus}
        )
        or h(e, d)
    )

    # Регистрируем роутер
    dp.include_router(menu_router)


def setup_menu_handlers():
    """Настройка обработчиков меню"""
    return menu_router
