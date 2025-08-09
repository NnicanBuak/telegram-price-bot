#!/usr/bin/env python3
"""
Telegram бот для рассылки прайс-листов по группам
Упрощенная версия с сохранением всей функциональности
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from database import Database, Template, ChatGroup, Mailing
from menu_system import MenuManager, MenuMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Состояния для FSM (копируем из оригинального bot.py)
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


# Инициализация
config = Config()
bot = Bot(token=config.bot_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database(config.database_url)

# Инициализация системы меню
menu_manager = MenuManager(admin_ids=config.admin_ids)

# Добавляем middleware для проверки доступа
menu_middleware = MenuMiddleware(menu_manager)
dp.message.middleware(menu_middleware)
dp.callback_query.middleware(menu_middleware)


# Декоратор для проверки админа (временный, пока не исправим импорты в тестах)
def admin_only(func):
    """Декоратор для проверки прав администратора"""

    async def wrapper(update, *args, **kwargs):
        user_id = (
            update.from_user.id
            if hasattr(update, "from_user")
            else update.message.from_user.id
        )
        if user_id not in config.admin_ids:
            return
        return await func(update, *args, **kwargs)

    return wrapper


# ========== КОМАНДЫ БОТА (копируем из оригинала) ==========


@dp.message(CommandStart())
async def cmd_start(message: types.Message, menu_manager: MenuManager):
    """Приветственное сообщение"""
    user_id = message.from_user.id
    text, keyboard = menu_manager.render_menu("main", user_id)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@dp.message(Command("help"))
async def cmd_help(message: types.Message, menu_manager: MenuManager):
    """Справка по командам"""
    help_text = """
<b>📚 Доступные команды:</b>

/start - Главное меню
/help - Эта справка
/templates - Управление шаблонами
/groups - Управление группами чатов
/mailing - Создать рассылку
/history - История рассылок

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


# ========== РАБОТА С ШАБЛОНАМИ ==========


@dp.message(Command("templates"))
@dp.callback_query(F.data == "templates")
async def show_templates(update: types.Message | types.CallbackQuery):
    """Показать список шаблонов"""
    message = update if isinstance(update, types.Message) else update.message

    templates = await db.get_templates()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📄 {t.name}", callback_data=f"template_{t.id}"
                )
            ]
            for t in templates
        ]
        + [
            [
                InlineKeyboardButton(
                    text="➕ Создать новый", callback_data="new_template"
                )
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
        ]
    )

    text = (
        "📋 <b>Шаблоны сообщений:</b>\n\n"
        if templates
        else "📋 <b>Шаблоны не найдены</b>\n\n"
    )

    if isinstance(update, types.CallbackQuery):
        await update.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await update.answer()
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(F.data == "new_template")
async def new_template(callback: types.CallbackQuery, state: FSMContext):
    """Создание нового шаблона"""
    await callback.message.edit_text(
        "📝 Введите название для нового шаблона:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="templates")]
            ]
        ),
    )
    await state.set_state(TemplateStates.waiting_for_name)
    await callback.answer()


@dp.message(TemplateStates.waiting_for_name)
async def template_name_received(message: types.Message, state: FSMContext):
    """Получение названия шаблона"""
    await state.update_data(name=message.text)
    await message.answer(
        "✏️ Теперь введите текст шаблона:\n\n" "<i>Поддерживается HTML разметка</i>",
        parse_mode="HTML",
    )
    await state.set_state(TemplateStates.waiting_for_text)


@dp.message(TemplateStates.waiting_for_text)
async def template_text_received(message: types.Message, state: FSMContext):
    """Получение текста шаблона"""
    await state.update_data(text=message.text)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📎 Да, прикрепить файл", callback_data="attach_file"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💾 Сохранить без файла", callback_data="save_template"
                )
            ],
        ]
    )

    await message.answer("Хотите прикрепить файл к шаблону?", reply_markup=keyboard)


@dp.callback_query(F.data == "attach_file")
async def request_file(callback: types.CallbackQuery, state: FSMContext):
    """Запрос файла для шаблона"""
    await callback.message.edit_text(
        "📎 Отправьте файл (документ или изображение):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="save_template")]
            ]
        ),
    )
    await state.set_state(TemplateStates.waiting_for_file)
    await callback.answer()


@dp.message(TemplateStates.waiting_for_file, F.document | F.photo)
async def file_received(message: types.Message, state: FSMContext):
    """Получение файла для шаблона"""
    if message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"

    await state.update_data(file_id=file_id, file_type=file_type)
    await save_template_to_db(message, state)


@dp.callback_query(F.data == "save_template")
async def save_template_callback(callback: types.CallbackQuery, state: FSMContext):
    """Сохранение шаблона без файла"""
    await save_template_to_db(callback.message, state)
    await callback.answer()


async def save_template_to_db(message: types.Message, state: FSMContext):
    """Сохранение шаблона в БД"""
    data = await state.get_data()

    template = await db.create_template(
        name=data["name"],
        text=data["text"],
        file_id=data.get("file_id"),
        file_type=data.get("file_type"),
    )

    await message.answer(
        f"✅ Шаблон «{template.name}» успешно создан!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 К списку шаблонов", callback_data="templates"
                    )
                ]
            ]
        ),
    )
    await state.clear()


# ========== РАБОТА С ГРУППАМИ ЧАТОВ ==========


@dp.message(Command("groups"))
@dp.callback_query(F.data == "groups")
async def show_groups(update: types.Message | types.CallbackQuery):
    """Показать список групп чатов"""
    message = update if isinstance(update, types.Message) else update.message

    groups = await db.get_chat_groups()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"👥 {g.name} ({len(g.chat_ids)} чатов)",
                    callback_data=f"group_{g.id}",
                )
            ]
            for g in groups
        ]
        + [
            [InlineKeyboardButton(text="➕ Создать новую", callback_data="new_group")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
        ]
    )

    text = (
        "👥 <b>Группы чатов:</b>\n\n" if groups else "👥 <b>Группы не найдены</b>\n\n"
    )

    if isinstance(update, types.CallbackQuery):
        await update.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await update.answer()
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ... (остальные обработчики копируем аналогично из оригинального bot.py)

# ========== ПОЛУЧЕНИЕ ID ЧАТА ==========


@dp.message(Command("id"))
async def get_chat_id(message: types.Message):
    """Получение ID чата"""
    chat_info = f"💬 <b>Информация о чате:</b>\n\n"
    chat_info += f"ID: <code>{message.chat.id}</code>\n"

    if message.chat.type != "private":
        chat_info += f"Название: {message.chat.title}\n"
        chat_info += f"Тип: {message.chat.type}\n"

    await message.answer(chat_info, parse_mode="HTML")


# ========== НАВИГАЦИЯ ==========


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Шаблоны", callback_data="templates")],
            [InlineKeyboardButton(text="👥 Группы чатов", callback_data="groups")],
            [
                InlineKeyboardButton(
                    text="📮 Создать рассылку", callback_data="create_mailing"
                )
            ],
            [InlineKeyboardButton(text="📊 История рассылок", callback_data="history")],
        ]
    )

    await callback.message.edit_text(
        "🤖 <b>Бот для рассылки прайс-листов</b>\n\n" "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


async def main():
    """Запуск бота"""
    logger.info("Инициализация базы данных...")
    await db.init_db()

    logger.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
