"""
Обработчики для работы с группами чатов
Обновлено для новой архитектуры с использованием shared утилит
"""

import re
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import TYPE_CHECKING, List
from shared.pagination import PaginationHelper, ConfirmationHelper, MenuHelper

if TYPE_CHECKING:
    from database import Database
    from shared.menu_system import MenuManager

# Создаем роутер для обработчиков групп
group_router = Router()

# ========== FSM СОСТОЯНИЯ ==========


class GroupStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_chats = State()
    editing_name = State()
    editing_chats = State()
    adding_chats = State()


# ========== CALLBACK ОБРАБОТЧИКИ ==========


@group_router.callback_query(F.data == "groups_list")
async def show_groups_list(
    callback: types.CallbackQuery, database: "Database", menu_manager: "MenuManager"
):
    """Показать список групп чатов"""
    try:
        groups = await database.get_chat_groups()

        if not groups:
            text = """👥 <b>Группы чатов</b>

❌ <i>Группы не найдены</i>

Создайте первую группу для организации чатов по категориям."""

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ Создать группу", callback_data="group_create"
                        )
                    ],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_groups")],
                ]
            )
        else:
            text = f"""👥 <b>Группы чатов</b>

📊 <i>Найдено групп: {len(groups)}</i>

Выберите группу для просмотра или редактирования:"""

            # Используем PaginationHelper для создания списка
            def group_text_func(group):
                chat_count = len(group.chat_ids) if group.chat_ids else 0
                return f"{group.name} ({chat_count} чатов)"

            def group_callback_func(group):
                return f"group_view_{group.id}"

            additional_buttons = [
                [
                    InlineKeyboardButton(
                        text="➕ Создать группу", callback_data="group_create"
                    )
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_groups")],
            ]

            keyboard = PaginationHelper.create_simple_list_keyboard(
                items=groups,
                item_text_func=group_text_func,
                item_callback_func=group_callback_func,
                item_icon="👥",
                additional_buttons=additional_buttons,
            )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@group_router.callback_query(F.data == "group_create")
async def start_group_creation(callback: types.CallbackQuery, state: FSMContext):
    """Начать создание новой группы"""
    text = """➕ <b>Создание группы чатов</b>

📝 Введите название группы:

<i>Например: "Оптовые клиенты", "Розничные магазины", "VIP покупатели"</i>

💡 <b>Совет:</b> Используйте понятные названия для удобной организации рассылок."""

    keyboard = ConfirmationHelper.create_back_keyboard(
        back_text="❌ Отмена", back_callback="groups_list"
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(GroupStates.waiting_for_name)
    await callback.answer()


@group_router.callback_query(F.data.startswith("group_view_"))
async def view_group(callback: types.CallbackQuery, database: "Database"):
    """Просмотр конкретной группы"""
    try:
        group_id = int(callback.data.split("_")[-1])
        group = await database.get_chat_group(group_id)

        if not group:
            await callback.answer("❌ Группа не найдена", show_alert=True)
            return

        # Формируем информацию о группе
        chat_count = len(group.chat_ids) if group.chat_ids else 0
        created_date = group.created_at.strftime("%d.%m.%Y %H:%M")

        # Формируем список чатов
        chat_list = ""
        if group.chat_ids:
            for i, chat_id in enumerate(group.chat_ids[:10], 1):  # Показываем первые 10
                chat_list += f"  {i}. <code>{chat_id}</code>\n"

            if len(group.chat_ids) > 10:
                chat_list += f"  ... и еще {len(group.chat_ids) - 10} чатов\n"
        else:
            chat_list = "  <i>Чаты не добавлены</i>\n"

        text = f"""👥 <b>Группа: {group.name}</b>

📊 <b>Количество чатов:</b> {chat_count}
📅 <b>Создана:</b> {created_date}
🔢 <b>ID:</b> {group.id}

📋 <b>Список чатов:</b>
{chat_list}

💡 <i>Чтобы получить ID чата, отправьте команду /id в нужном чате</i>"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✏️ Редактировать", callback_data=f"group_edit_{group.id}"
                    ),
                    InlineKeyboardButton(
                        text="🗑️ Удалить", callback_data=f"group_delete_{group.id}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="➕ Добавить чаты",
                        callback_data=f"group_add_chats_{group.id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🧪 Тест рассылки", callback_data=f"group_test_{group.id}"
                    )
                ],
                [InlineKeyboardButton(text="◀️ К списку", callback_data="groups_list")],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except ValueError:
        await callback.answer("❌ Неверный ID группы", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@group_router.callback_query(F.data.startswith("group_delete_"))
async def confirm_group_deletion(callback: types.CallbackQuery):
    """Подтверждение удаления группы"""
    group_id = callback.data.split("_")[-1]

    text = """🗑️ <b>Удаление группы</b>

⚠️ <b>Внимание!</b> Это действие нельзя отменить.

Группа будет удалена со всеми настройками. Активные рассылки, использующие эту группу, могут быть нарушены.

Вы уверены, что хотите удалить эту группу?"""

    keyboard = ConfirmationHelper.create_confirmation_keyboard(
        confirm_text="✅ Да, удалить",
        cancel_text="❌ Отмена",
        confirm_callback=f"group_delete_confirm_{group_id}",
        cancel_callback=f"group_view_{group_id}",
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@group_router.callback_query(F.data.startswith("group_delete_confirm_"))
async def delete_group(callback: types.CallbackQuery, database: "Database"):
    """Удаление группы"""
    try:
        group_id = int(callback.data.split("_")[-1])
        success = await database.delete_chat_group(group_id)

        if success:
            await callback.answer("✅ Группа удалена", show_alert=True)
            # Возвращаемся к списку групп
            await show_groups_list(callback, database, None)
        else:
            await callback.answer("❌ Ошибка удаления", show_alert=True)

    except ValueError:
        await callback.answer("❌ Неверный ID группы", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@group_router.callback_query(F.data.startswith("group_test_"))
async def test_group_broadcast(callback: types.CallbackQuery, database: "Database"):
    """Тестовая рассылка по группе"""
    try:
        group_id = int(callback.data.split("_")[-1])
        group = await database.get_chat_group(group_id)

        if not group or not group.chat_ids:
            await callback.answer("❌ Группа пуста или не найдена", show_alert=True)
            return

        # Отправляем тестовое сообщение в каждый чат группы
        test_message = """🧪 <b>ТЕСТОВОЕ СООБЩЕНИЕ</b>

Это тестовая рассылка для проверки работы бота в вашем чате.

✅ Если вы видите это сообщение, значит бот корректно настроен для рассылки в этот чат.

🤖 <i>Сообщение отправлено автоматически</i>"""

        success_count = 0
        error_count = 0

        for chat_id in group.chat_ids:
            try:
                await callback.message.bot.send_message(chat_id, test_message)
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Ошибка отправки в чат {chat_id}: {e}")

        result_text = f"""📊 <b>Результат тестовой рассылки:</b>

✅ Успешно: {success_count}
❌ Ошибок: {error_count}
📊 Всего чатов: {len(group.chat_ids)}"""

        await callback.message.answer(result_text)
        await callback.answer("✅ Тестовая рассылка завершена")

    except ValueError:
        await callback.answer("❌ Неверный ID группы", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка рассылки: {e}", show_alert=True)


# ========== MESSAGE ОБРАБОТЧИКИ ==========


@group_router.message(GroupStates.waiting_for_name)
async def process_group_name(message: types.Message, state: FSMContext):
    """Обработка названия группы"""
    name = message.text.strip()

    if len(name) < 3:
        await message.answer(
            "❌ Название слишком короткое. Минимум 3 символа.\n\n" "Попробуйте еще раз:"
        )
        return

    if len(name) > 50:
        await message.answer(
            "❌ Название слишком длинное. Максимум 50 символов.\n\n"
            "Попробуйте еще раз:"
        )
        return

    # Сохраняем название в состоянии
    await state.update_data(group_name=name)

    text = f"""✅ <b>Название принято:</b> {name}

📋 Теперь введите ID чатов через запятую:

<i>Примеры ID:
• -1001234567890 (супергруппа)
• -987654321 (обычная группа)
• 123456789 (приватный чат)</i>

💡 <b>Как получить ID чата:</b>
1. Добавьте бота в чат как администратора
2. Отправьте команду /id в чате
3. Скопируйте полученный ID

<b>Формат ввода:</b>
-1001234567890, -1009876543210, 123456789"""

    keyboard = ConfirmationHelper.create_back_keyboard(
        back_text="❌ Отмена", back_callback="groups_list"
    )

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(GroupStates.waiting_for_chats)


@group_router.message(GroupStates.waiting_for_chats)
async def process_group_chats(
    message: types.Message, state: FSMContext, database: "Database"
):
    """Обработка списка чатов группы"""
    try:
        chat_ids_text = message.text.strip()

        # Парсим ID чатов
        chat_ids = parse_chat_ids(chat_ids_text)

        if not chat_ids:
            await message.answer(
                "❌ Не удалось распознать ID чатов.\n\n"
                "Убедитесь, что вы вводите числа через запятую:\n"
                "<code>-1001234567890, -1009876543210</code>\n\n"
                "Попробуйте еще раз:"
            )
            return

        if len(chat_ids) > 100:
            await message.answer(
                "❌ Слишком много чатов. Максимум 100 чатов в группе.\n\n"
                "Попробуйте еще раз с меньшим количеством:"
            )
            return

        # Проверяем доступность некоторых чатов
        await message.answer("🔍 Проверяем доступность чатов...")

        valid_chats, invalid_chats = await validate_chat_ids(message.bot, chat_ids)

        # Получаем данные из состояния
        data = await state.get_data()
        group_name = data.get("group_name")

        if not group_name:
            await message.answer("❌ Ошибка: название группы не найдено")
            await state.clear()
            return

        # Создаем группу в БД
        group = await database.create_chat_group(name=group_name, chat_ids=valid_chats)

        if group:
            validation_info = ""
            if invalid_chats:
                validation_info = f"\n\n⚠️ <b>Недоступные чаты:</b> {len(invalid_chats)}\n<i>Проверьте права доступа бота</i>"

            success_text = f"""✅ <b>Группа создана успешно!</b>

👥 <b>Название:</b> {group_name}
📊 <b>Чатов добавлено:</b> {len(valid_chats)}
🔢 <b>ID группы:</b> {group.id}{validation_info}"""

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👥 К списку групп", callback_data="groups_list"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🏠 Главное меню", callback_data="menu_main"
                        )
                    ],
                ]
            )

            await message.answer(success_text, reply_markup=keyboard)
        else:
            await message.answer("❌ Ошибка создания группы")

        # Очищаем состояние
        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Ошибка при создании группы: {e}")
        await state.clear()


# ========== РЕДАКТИРОВАНИЕ ГРУПП ==========


@group_router.callback_query(F.data.startswith("group_edit_"))
async def edit_group_menu(callback: types.CallbackQuery, database: "Database"):
    """Меню редактирования группы"""
    try:
        group_id = int(callback.data.split("_")[-1])
        group = await database.get_chat_group(group_id)

        if not group:
            await callback.answer("❌ Группа не найдена", show_alert=True)
            return

        text = f"""✏️ <b>Редактирование группы</b>

👥 <b>Текущее название:</b> {group.name}
📊 <b>Чатов в группе:</b> {len(group.chat_ids) if group.chat_ids else 0}

Что вы хотите изменить?"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📝 Название", callback_data=f"group_edit_name_{group_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Список чатов",
                        callback_data=f"group_edit_chats_{group_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ Назад", callback_data=f"group_view_{group_id}"
                    )
                ],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except ValueError:
        await callback.answer("❌ Неверный ID группы", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@group_router.callback_query(F.data.startswith("group_edit_name_"))
async def start_group_name_editing(callback: types.CallbackQuery, state: FSMContext):
    """Начать редактирование названия группы"""
    group_id = callback.data.split("_")[-1]

    text = """✏️ <b>Изменение названия группы</b>

📝 Введите новое название группы:

<i>Например: "Премиум клиенты", "Региональные партнеры"</i>"""

    keyboard = ConfirmationHelper.create_back_keyboard(
        back_text="❌ Отмена", back_callback=f"group_edit_{group_id}"
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(GroupStates.editing_name)
    await state.update_data(editing_group_id=group_id)
    await callback.answer()


@group_router.message(GroupStates.editing_name)
async def process_group_name_edit(
    message: types.Message, state: FSMContext, database: "Database"
):
    """Обработка нового названия группы"""
    try:
        new_name = message.text.strip()

        if len(new_name) < 3:
            await message.answer("❌ Название слишком короткое. Минимум 3 символа.")
            return

        if len(new_name) > 50:
            await message.answer("❌ Название слишком длинное. Максимум 50 символов.")
            return

        data = await state.get_data()
        group_id = int(data.get("editing_group_id"))

        success = await database.update_chat_group_name(group_id, new_name)

        if success:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👥 К группе", callback_data=f"group_view_{group_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="📋 К списку", callback_data="groups_list"
                        )
                    ],
                ]
            )

            await message.answer(
                f"✅ <b>Название изменено!</b>\n\n"
                f"👥 <b>Новое название:</b> {new_name}",
                reply_markup=keyboard,
            )
        else:
            await message.answer("❌ Ошибка при изменении названия")

        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()


@group_router.callback_query(F.data.startswith("group_add_chats_"))
async def start_adding_chats(callback: types.CallbackQuery, state: FSMContext):
    """Начать добавление чатов в группу"""
    group_id = callback.data.split("_")[-1]

    text = """➕ <b>Добавление чатов в группу</b>

📋 Введите ID новых чатов через запятую:

<i>Примеры:
-1001234567890, -1009876543210</i>

💡 <b>Совет:</b> Чтобы получить ID чата, отправьте /id в нужном чате"""

    keyboard = ConfirmationHelper.create_back_keyboard(
        back_text="❌ Отмена", back_callback=f"group_view_{group_id}"
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(GroupStates.adding_chats)
    await state.update_data(adding_to_group_id=group_id)
    await callback.answer()


@group_router.message(GroupStates.adding_chats)
async def process_adding_chats(
    message: types.Message, state: FSMContext, database: "Database"
):
    """Обработка добавления новых чатов"""
    try:
        chat_ids_text = message.text.strip()
        new_chat_ids = parse_chat_ids(chat_ids_text)

        if not new_chat_ids:
            await message.answer(
                "❌ Не удалось распознать ID чатов. Попробуйте еще раз:"
            )
            return

        data = await state.get_data()
        group_id = int(data.get("adding_to_group_id"))

        # Получаем текущую группу
        group = await database.get_chat_group(group_id)
        if not group:
            await message.answer("❌ Группа не найдена")
            await state.clear()
            return

        # Объединяем существующие и новые чаты
        existing_chat_ids = group.chat_ids or []
        all_chat_ids = list(set(existing_chat_ids + new_chat_ids))

        if len(all_chat_ids) > 100:
            await message.answer(
                f"❌ Превышен лимит чатов в группе (100).\n"
                f"Текущих чатов: {len(existing_chat_ids)}\n"
                f"Новых чатов: {len(new_chat_ids)}\n"
                f"Итого будет: {len(all_chat_ids)}"
            )
            return

        # Обновляем группу
        success = await database.update_chat_group_chats(group_id, all_chat_ids)

        if success:
            added_count = len(all_chat_ids) - len(existing_chat_ids)
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👥 К группе", callback_data=f"group_view_{group_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="📋 К списку", callback_data="groups_list"
                        )
                    ],
                ]
            )

            await message.answer(
                f"✅ <b>Чаты добавлены!</b>\n\n"
                f"➕ <b>Добавлено:</b> {added_count}\n"
                f"📊 <b>Всего в группе:</b> {len(all_chat_ids)}",
                reply_markup=keyboard,
            )
        else:
            await message.answer("❌ Ошибка при добавлении чатов")

        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()


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


async def validate_chat_ids(bot, chat_ids: List[int]) -> tuple[List[int], List[int]]:
    """Проверка доступности чатов"""
    valid_chats = []
    invalid_chats = []

    for chat_id in chat_ids[:10]:  # Проверяем только первые 10 для экономии времени
        try:
            await bot.get_chat(chat_id)
            valid_chats.append(chat_id)
        except Exception:
            invalid_chats.append(chat_id)

    # Остальные чаты добавляем без проверки
    if len(chat_ids) > 10:
        valid_chats.extend(chat_ids[10:])

    return valid_chats, invalid_chats
