#!/usr/bin/env python3
"""
Telegram бот для рассылки прайс-листов по группам
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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile, BufferedInputFile

from config import Config
from database import Database, Template, ChatGroup, Mailing
from menu_system import MenuManager, MenuMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Состояния для FSM
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

# Команды бота
@dp.message(CommandStart())
async def cmd_start(message: types.Message, menu_manager: MenuManager):
    """Приветственное сообщение"""
    user_id = message.from_user.id
    
    # Проверка доступа уже выполнена в middleware
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

# Работа с шаблонами
@dp.message(Command("templates"))
@dp.callback_query(F.data == "templates")
@admin_only
async def show_templates(update: types.Message | types.CallbackQuery):
    """Показать список шаблонов"""
    message = update if isinstance(update, types.Message) else update.message
    
    templates = await db.get_templates()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📄 {t.name}", callback_data=f"template_{t.id}")]
        for t in templates
    ] + [
        [InlineKeyboardButton(text="➕ Создать новый", callback_data="new_template")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    
    text = "📋 <b>Шаблоны сообщений:</b>\n\n" if templates else "📋 <b>Шаблоны не найдены</b>\n\n"
    
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
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="templates")]
        ])
    )
    await state.set_state(TemplateStates.waiting_for_name)
    await callback.answer()

@dp.message(TemplateStates.waiting_for_name)
async def template_name_received(message: types.Message, state: FSMContext):
    """Получение названия шаблона"""
    await state.update_data(name=message.text)
    await message.answer(
        "✏️ Теперь введите текст шаблона:\n\n"
        "<i>Поддерживается HTML разметка</i>",
        parse_mode="HTML"
    )
    await state.set_state(TemplateStates.waiting_for_text)

@dp.message(TemplateStates.waiting_for_text)
async def template_text_received(message: types.Message, state: FSMContext):
    """Получение текста шаблона"""
    await state.update_data(text=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📎 Да, прикрепить файл", callback_data="attach_file")],
        [InlineKeyboardButton(text="💾 Сохранить без файла", callback_data="save_template")]
    ])
    
    await message.answer(
        "Хотите прикрепить файл к шаблону?",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "attach_file")
async def request_file(callback: types.CallbackQuery, state: FSMContext):
    """Запрос файла для шаблона"""
    await callback.message.edit_text(
        "📎 Отправьте файл (документ или изображение):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="save_template")]
        ])
    )
    await state.set_state(TemplateStates.waiting_for_file)
    await callback.answer()

@dp.message(TemplateStates.waiting_for_file, F.document | F.photo)
async def file_received(message: types.Message, state: FSMContext):
    """Получение файла для шаблона"""
    if message.document:
        file_id = message.document.file_id
        file_type = 'document'
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    
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
        name=data['name'],
        text=data['text'],
        file_id=data.get('file_id'),
        file_type=data.get('file_type')
    )
    
    await message.answer(
        f"✅ Шаблон «{template.name}» успешно создан!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 К списку шаблонов", callback_data="templates")]
        ])
    )
    await state.clear()

# Работа с группами чатов
@dp.message(Command("groups"))
@dp.callback_query(F.data == "groups")
@admin_only
async def show_groups(update: types.Message | types.CallbackQuery):
    """Показать список групп чатов"""
    message = update if isinstance(update, types.Message) else update.message
    
    groups = await db.get_chat_groups()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👥 {g.name} ({len(g.chat_ids)} чатов)", 
                            callback_data=f"group_{g.id}")]
        for g in groups
    ] + [
        [InlineKeyboardButton(text="➕ Создать новую", callback_data="new_group")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    
    text = "👥 <b>Группы чатов:</b>\n\n" if groups else "👥 <b>Группы не найдены</b>\n\n"
    
    if isinstance(update, types.CallbackQuery):
        await update.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await update.answer()
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "new_group")
async def new_group(callback: types.CallbackQuery, state: FSMContext):
    """Создание новой группы"""
    await callback.message.edit_text(
        "📝 Введите название для новой группы чатов:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="groups")]
        ])
    )
    await state.set_state(GroupStates.waiting_for_name)
    await callback.answer()

@dp.message(GroupStates.waiting_for_name)
async def group_name_received(message: types.Message, state: FSMContext):
    """Получение названия группы"""
    await state.update_data(name=message.text)
    await message.answer(
        "📝 Теперь введите ID чатов через запятую:\n\n"
        "<i>Пример: -1001234567890, -1009876543210</i>\n\n"
        "<b>Как получить ID чата:</b>\n"
        "1. Добавьте бота в чат как администратора\n"
        "2. Напишите в чат команду /id\n"
        "3. Или перешлите сообщение из чата боту @userinfobot",
        parse_mode="HTML"
    )
    await state.set_state(GroupStates.waiting_for_chats)

@dp.message(GroupStates.waiting_for_chats)
async def group_chats_received(message: types.Message, state: FSMContext):
    """Получение списка чатов"""
    try:
        chat_ids = [int(chat_id.strip()) for chat_id in message.text.split(',')]
        
        data = await state.get_data()
        group = await db.create_chat_group(
            name=data['name'],
            chat_ids=chat_ids
        )
        
        await message.answer(
            f"✅ Группа «{group.name}» создана!\n"
            f"Добавлено чатов: {len(chat_ids)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👥 К списку групп", callback_data="groups")]
            ])
        )
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Ошибка! Проверьте формат ID чатов.\n"
            "Попробуйте еще раз:"
        )

# Создание рассылки
@dp.message(Command("mailing"))
@dp.callback_query(F.data == "create_mailing")
@admin_only
async def create_mailing(update: types.Message | types.CallbackQuery, state: FSMContext):
    """Начало создания рассылки"""
    message = update if isinstance(update, types.Message) else update.message
    
    templates = await db.get_templates()
    
    if not templates:
        text = "❌ Сначала создайте хотя бы один шаблон!"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Создать шаблон", callback_data="new_template")]
        ])
    else:
        text = "📮 <b>Создание рассылки</b>\n\nВыберите шаблон:"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📄 {t.name}", callback_data=f"mailing_template_{t.id}")]
            for t in templates
        ] + [
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")]
        ])
        await state.set_state(MailingStates.selecting_template)
    
    if isinstance(update, types.CallbackQuery):
        await update.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await update.answer()
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data.startswith("mailing_template_"))
async def mailing_template_selected(callback: types.CallbackQuery, state: FSMContext):
    """Выбор шаблона для рассылки"""
    template_id = int(callback.data.split("_")[2])
    await state.update_data(template_id=template_id)
    
    groups = await db.get_chat_groups()
    
    if not groups:
        await callback.message.edit_text(
            "❌ Сначала создайте хотя бы одну группу чатов!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👥 Создать группу", callback_data="new_group")]
            ])
        )
    else:
        await callback.message.edit_text(
            "👥 Выберите группы для рассылки:\n\n"
            "<i>Можно выбрать несколько групп</i>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{'✅' if False else '⬜'} {g.name} ({len(g.chat_ids)} чатов)",
                    callback_data=f"toggle_group_{g.id}"
                )]
                for g in groups
            ] + [
                [InlineKeyboardButton(text="✅ Выбрать все", callback_data="select_all_groups")],
                [InlineKeyboardButton(text="➡️ Далее", callback_data="confirm_mailing")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")]
            ]),
            parse_mode="HTML"
        )
        await state.update_data(selected_groups=[])
        await state.set_state(MailingStates.selecting_groups)
    
    await callback.answer()

@dp.callback_query(F.data.startswith("toggle_group_"))
async def toggle_group(callback: types.CallbackQuery, state: FSMContext):
    """Переключение выбора группы"""
    group_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    selected_groups = data.get('selected_groups', [])
    
    if group_id in selected_groups:
        selected_groups.remove(group_id)
    else:
        selected_groups.append(group_id)
    
    await state.update_data(selected_groups=selected_groups)
    
    # Обновляем клавиатуру
    groups = await db.get_chat_groups()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'✅' if g.id in selected_groups else '⬜'} {g.name} ({len(g.chat_ids)} чатов)",
            callback_data=f"toggle_group_{g.id}"
        )]
        for g in groups
    ] + [
        [InlineKeyboardButton(text="✅ Выбрать все", callback_data="select_all_groups")],
        [InlineKeyboardButton(text="➡️ Далее", callback_data="confirm_mailing")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(f"Выбрано групп: {len(selected_groups)}")

@dp.callback_query(F.data == "select_all_groups")
async def select_all_groups(callback: types.CallbackQuery, state: FSMContext):
    """Выбрать все группы"""
    groups = await db.get_chat_groups()
    all_group_ids = [g.id for g in groups]
    await state.update_data(selected_groups=all_group_ids)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"✅ {g.name} ({len(g.chat_ids)} чатов)",
            callback_data=f"toggle_group_{g.id}"
        )]
        for g in groups
    ] + [
        [InlineKeyboardButton(text="⬜ Снять все", callback_data="deselect_all_groups")],
        [InlineKeyboardButton(text="➡️ Далее", callback_data="confirm_mailing")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("Все группы выбраны")

@dp.callback_query(F.data == "confirm_mailing")
async def confirm_mailing(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение рассылки"""
    data = await state.get_data()
    
    if not data.get('selected_groups'):
        await callback.answer("⚠️ Выберите хотя бы одну группу!", show_alert=True)
        return
    
    template = await db.get_template(data['template_id'])
    groups = await db.get_chat_groups_by_ids(data['selected_groups'])
    
    total_chats = sum(len(g.chat_ids) for g in groups)
    
    # Предпросмотр
    preview_text = f"<b>📮 Подтверждение рассылки</b>\n\n"
    preview_text += f"📄 Шаблон: {template.name}\n"
    preview_text += f"👥 Групп: {len(groups)}\n"
    preview_text += f"💬 Всего чатов: {total_chats}\n\n"
    preview_text += f"<b>Текст сообщения:</b>\n{template.text[:500]}"
    
    if template.file_id:
        preview_text += f"\n\n📎 <i>+ прикрепленный файл</i>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="send_mailing")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        preview_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MailingStates.confirming)
    await callback.answer()

@dp.callback_query(F.data == "send_mailing")
async def send_mailing(callback: types.CallbackQuery, state: FSMContext):
    """Отправка рассылки"""
    await callback.message.edit_text("⏳ Начинаю рассылку...")
    
    data = await state.get_data()
    template = await db.get_template(data['template_id'])
    groups = await db.get_chat_groups_by_ids(data['selected_groups'])
    
    # Собираем все чаты
    all_chat_ids = []
    for group in groups:
        all_chat_ids.extend(group.chat_ids)
    
    # Убираем дубликаты
    all_chat_ids = list(set(all_chat_ids))
    
    # Создаем запись о рассылке
    mailing = await db.create_mailing(
        template_id=template.id,
        group_ids=data['selected_groups'],
        total_chats=len(all_chat_ids)
    )
    
    # Счетчики
    sent = 0
    failed = 0
    
    # Отправляем сообщения
    for chat_id in all_chat_ids:
        try:
            if template.file_id:
                if template.file_type == 'photo':
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=template.file_id,
                        caption=template.text,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_document(
                        chat_id=chat_id,
                        document=template.file_id,
                        caption=template.text,
                        parse_mode="HTML"
                    )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=template.text,
                    parse_mode="HTML"
                )
            
            sent += 1
            
            # Обновляем прогресс каждые 10 сообщений
            if sent % 10 == 0:
                await callback.message.edit_text(
                    f"⏳ Отправка...\n\n"
                    f"✅ Отправлено: {sent}/{len(all_chat_ids)}\n"
                    f"❌ Ошибок: {failed}"
                )
            
            # Задержка между сообщениями
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Ошибка отправки в чат {chat_id}: {e}")
            failed += 1
    
    # Обновляем статистику рассылки
    await db.update_mailing_stats(mailing.id, sent, failed)
    
    # Финальное сообщение
    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Статистика:\n"
        f"✅ Успешно: {sent}\n"
        f"❌ Ошибок: {failed}\n"
        f"📋 Шаблон: {template.name}\n"
        f"🕐 Время: {datetime.now().strftime('%H:%M')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 История", callback_data="history")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_menu")]
        ]),
        parse_mode="HTML"
    )
    
    await state.clear()
    await callback.answer()

# История рассылок
@dp.callback_query(F.data == "history")
async def show_history(callback: types.CallbackQuery):
    """Показать историю рассылок"""
    mailings = await db.get_mailings_history(limit=10)
    
    if not mailings:
        text = "📊 <b>История рассылок пуста</b>"
    else:
        text = "📊 <b>История рассылок:</b>\n\n"
        for m in mailings:
            template = await db.get_template(m.template_id)
            text += f"📅 {m.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"📄 Шаблон: {template.name}\n"
            text += f"✅ Отправлено: {m.sent_count}/{m.total_chats}\n"
            if m.failed_count:
                text += f"❌ Ошибок: {m.failed_count}\n"
            text += "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Навигация
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Шаблоны", callback_data="templates")],
        [InlineKeyboardButton(text="👥 Группы чатов", callback_data="groups")],
        [InlineKeyboardButton(text="📮 Создать рассылку", callback_data="create_mailing")],
        [InlineKeyboardButton(text="📊 История рассылок", callback_data="history")]
    ])
    
    await callback.message.edit_text(
        "🤖 <b>Бот для рассылки прайс-листов</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# Обработка команды /id в чатах
@dp.message(Command("id"))
async def get_chat_id(message: types.Message):
    """Получение ID чата"""
    chat_info = f"💬 <b>Информация о чате:</b>\n\n"
    chat_info += f"ID: <code>{message.chat.id}</code>\n"
    
    if message.chat.type != 'private':
        chat_info += f"Название: {message.chat.title}\n"
        chat_info += f"Тип: {message.chat.type}\n"
    
    await message.answer(chat_info, parse_mode="HTML")

# Просмотр деталей шаблона
@dp.callback_query(F.data.startswith("template_"))
async def show_template_details(callback: types.CallbackQuery):
    """Показать детали шаблона"""
    template_id = int(callback.data.split("_")[1])
    template = await db.get_template(template_id)
    
    if not template:
        await callback.answer("Шаблон не найден", show_alert=True)
        return
    
    text = f"📄 <b>{template.name}</b>\n\n"
    text += f"<b>Текст:</b>\n{template.text[:1000]}"
    
    if template.file_id:
        text += f"\n\n📎 <i>Есть прикрепленный файл ({template.file_type})</i>"
    
    text += f"\n\n📅 Создан: {template.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_template_{template_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="templates")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Просмотр деталей группы
@dp.callback_query(F.data.startswith("group_"))
async def show_group_details(callback: types.CallbackQuery):
    """Показать детали группы чатов"""
    if callback.data.startswith("group_"):
        group_id = int(callback.data.split("_")[1])
        group = await db.get_chat_group(group_id)
        
        if not group:
            await callback.answer("Группа не найдена", show_alert=True)
            return
        
        text = f"👥 <b>{group.name}</b>\n\n"
        text += f"💬 Количество чатов: {len(group.chat_ids)}\n\n"
        text += f"<b>ID чатов:</b>\n"
        
        for chat_id in group.chat_ids[:10]:  # Показываем первые 10
            text += f"• <code>{chat_id}</code>\n"
        
        if len(group.chat_ids) > 10:
            text += f"\n<i>... и еще {len(group.chat_ids) - 10} чатов</i>"
        
        text += f"\n\n📅 Создана: {group.created_at.strftime('%d.%m.%Y %H:%M')}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_group_{group_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="groups")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

# Удаление шаблона
@dp.callback_query(F.data.startswith("delete_template_"))
async def delete_template(callback: types.CallbackQuery):
    """Удаление шаблона"""
    template_id = int(callback.data.split("_")[2])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_template_{template_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"template_{template_id}")]
    ])
    
    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить этот шаблон?",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_delete_template_"))
async def confirm_delete_template(callback: types.CallbackQuery):
    """Подтверждение удаления шаблона"""
    template_id = int(callback.data.split("_")[3])
    
    await db.delete_template(template_id)
    
    await callback.message.edit_text(
        "✅ Шаблон успешно удален!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 К списку шаблонов", callback_data="templates")]
        ])
    )
    await callback.answer()

# Удаление группы
@dp.callback_query(F.data.startswith("delete_group_"))
async def delete_group(callback: types.CallbackQuery):
    """Удаление группы"""
    group_id = int(callback.data.split("_")[2])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_group_{group_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"group_{group_id}")]
    ])
    
    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить эту группу?",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_delete_group_"))
async def confirm_delete_group(callback: types.CallbackQuery):
    """Подтверждение удаления группы"""
    group_id = int(callback.data.split("_")[3])
    
    await db.delete_chat_group(group_id)
    
    await callback.message.edit_text(
        "✅ Группа успешно удалена!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 К списку групп", callback_data="groups")]
        ])
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