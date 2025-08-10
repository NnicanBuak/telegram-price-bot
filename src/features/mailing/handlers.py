"""
Обработчики для рассылки сообщений
Основной функционал бота - создание и выполнение рассылок по группам чатов
"""

import asyncio
import os
from datetime import datetime
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from typing import TYPE_CHECKING, List, Dict
from shared.pagination import MenuHelper, ConfirmationHelper, PaginationHelper

if TYPE_CHECKING:
    from database import Database
    from shared.menu_system import MenuManager

# Создаем роутер для обработчиков рассылки
mailing_router = Router()

# ========== FSM СОСТОЯНИЯ ==========


class MailingStates(StatesGroup):
    selecting_template = State()
    selecting_groups = State()
    confirming = State()
    schedule_date = State()
    schedule_time = State()


# ========== CALLBACK ОБРАБОТЧИКИ ==========


@mailing_router.callback_query(F.data == "mailing_create")
async def start_mailing_creation(
    callback: types.CallbackQuery, database: "Database", state: FSMContext
):
    """Начать создание рассылки"""
    try:
        # Проверяем наличие шаблонов
        templates = await database.get_templates()
        if not templates:
            text = """📮 <b>Создание рассылки</b>

❌ <i>Нет доступных шаблонов</i>

Для создания рассылки сначала необходимо создать хотя бы один шаблон сообщения."""

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📋 Создать шаблон", callback_data="template_create"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад", callback_data="menu_mailing"
                        )
                    ],
                ]
            )

            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
            return

        # Проверяем наличие групп
        groups = await database.get_chat_groups()
        if not groups:
            text = """📮 <b>Создание рассылки</b>

❌ <i>Нет доступных групп чатов</i>

Для создания рассылки необходимо создать хотя бы одну группу чатов."""

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👥 Создать группу", callback_data="group_create"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад", callback_data="menu_mailing"
                        )
                    ],
                ]
            )

            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
            return

        # Показываем список шаблонов для выбора
        text = """📮 <b>Создание рассылки</b>

1️⃣ <b>Шаг 1:</b> Выберите шаблон сообщения

📋 <i>Доступные шаблоны:</i>"""

        keyboard_buttons = []
        for template in templates:
            icon = "📄" if not template.file_path else "📎"
            text_preview = (
                template.text[:30] + "..." if len(template.text) > 30 else template.text
            )
            button_text = f"{icon} {template.name}"

            keyboard_buttons.append(
                [
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"mailing_select_template_{template.id}",
                    )
                ]
            )

        keyboard_buttons.append(
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu_mailing")]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.set_state(MailingStates.selecting_template)
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@mailing_router.callback_query(F.data.startswith("mailing_select_template_"))
async def select_template_for_mailing(
    callback: types.CallbackQuery, database: "Database", state: FSMContext
):
    """Выбор шаблона для рассылки"""
    try:
        template_id = int(callback.data.split("_")[-1])
        template = await database.get_template(template_id)

        if not template:
            await callback.answer("❌ Шаблон не найден", show_alert=True)
            return

        # Сохраняем выбранный шаблон
        await state.update_data(selected_template_id=template_id)

        # Получаем группы для выбора
        groups = await database.get_chat_groups()

        text = f"""📮 <b>Создание рассылки</b>

✅ <b>Шаг 1 завершен:</b> Выбран шаблон "{template.name}"

2️⃣ <b>Шаг 2:</b> Выберите группы чатов для рассылки

👥 <i>Доступные группы:</i>"""

        keyboard_buttons = []
        for group in groups:
            chat_count = len(group.chat_ids) if group.chat_ids else 0
            if chat_count > 0:  # Показываем только непустые группы
                button_text = f"👥 {group.name} ({chat_count} чатов)"
                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            text=button_text,
                            callback_data=f"mailing_toggle_group_{group.id}",
                        )
                    ]
                )

        if not keyboard_buttons:
            await callback.message.edit_text(
                "❌ Нет групп с чатами для рассылки.\n\n"
                "Добавьте чаты в группы перед созданием рассылки.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="👥 Управление группами",
                                callback_data="groups_list",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="❌ Отмена", callback_data="menu_mailing"
                            )
                        ],
                    ]
                ),
            )
            await callback.answer()
            return

        keyboard_buttons.extend(
            [
                [
                    InlineKeyboardButton(
                        text="✅ Продолжить", callback_data="mailing_confirm_groups"
                    )
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="mailing_create")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="menu_mailing")],
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.set_state(MailingStates.selecting_groups)
        await state.update_data(
            selected_groups=[]
        )  # Инициализируем список выбранных групп
        await callback.answer()

    except ValueError:
        await callback.answer("❌ Неверный ID шаблона", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@mailing_router.callback_query(F.data.startswith("mailing_toggle_group_"))
async def toggle_group_selection(
    callback: types.CallbackQuery, database: "Database", state: FSMContext
):
    """Переключение выбора группы"""
    try:
        group_id = int(callback.data.split("_")[-1])

        # Получаем текущий список выбранных групп
        data = await state.get_data()
        selected_groups = data.get("selected_groups", [])

        # Переключаем выбор группы
        if group_id in selected_groups:
            selected_groups.remove(group_id)
        else:
            selected_groups.append(group_id)

        await state.update_data(selected_groups=selected_groups)

        # Обновляем клавиатуру с отметками выбранных групп
        groups = await database.get_chat_groups()
        template_id = data.get("selected_template_id")
        template = await database.get_template(template_id)

        text = f"""📮 <b>Создание рассылки</b>

✅ <b>Шаблон:</b> {template.name}

2️⃣ <b>Выберите группы:</b> ({len(selected_groups)} выбрано)

👥 <i>Доступные группы:</i>"""

        keyboard_buttons = []
        total_chats = 0

        for group in groups:
            chat_count = len(group.chat_ids) if group.chat_ids else 0
            if chat_count > 0:
                is_selected = group.id in selected_groups
                icon = "✅" if is_selected else "👥"
                button_text = f"{icon} {group.name} ({chat_count} чатов)"

                if is_selected:
                    total_chats += chat_count

                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            text=button_text,
                            callback_data=f"mailing_toggle_group_{group.id}",
                        )
                    ]
                )

        # Обновляем текст с информацией о выбранных группах
        if selected_groups:
            text += f"\n\n📊 <b>Будет отправлено в {total_chats} чатов</b>"

        keyboard_buttons.extend(
            [
                (
                    [
                        InlineKeyboardButton(
                            text=f"✅ Продолжить ({len(selected_groups)} групп)",
                            callback_data="mailing_confirm_groups",
                        )
                    ]
                    if selected_groups
                    else []
                ),
                [InlineKeyboardButton(text="◀️ Назад", callback_data="mailing_create")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="menu_mailing")],
            ]
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except ValueError:
        await callback.answer("❌ Неверный ID группы", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@mailing_router.callback_query(F.data == "mailing_confirm_groups")
async def confirm_mailing_creation(
    callback: types.CallbackQuery, database: "Database", state: FSMContext
):
    """Подтверждение создания рассылки"""
    try:
        data = await state.get_data()
        template_id = data.get("selected_template_id")
        selected_groups = data.get("selected_groups", [])

        if not selected_groups:
            await callback.answer("❌ Выберите хотя бы одну группу", show_alert=True)
            return

        # Получаем данные для подтверждения
        template = await database.get_template(template_id)
        groups = await database.get_chat_groups()
        selected_group_objects = [g for g in groups if g.id in selected_groups]

        # Подсчитываем общее количество чатов
        total_chats = sum(len(g.chat_ids) for g in selected_group_objects if g.chat_ids)

        # Формируем текст подтверждения
        text = f"""📮 <b>Подтверждение рассылки</b>

📋 <b>Шаблон:</b> {template.name}
📄 <b>Файл:</b> {"✅ Есть" if template.file_path else "❌ Нет"}

👥 <b>Группы для рассылки:</b>"""

        for group in selected_group_objects:
            chat_count = len(group.chat_ids) if group.chat_ids else 0
            text += f"\n  • {group.name} ({chat_count} чатов)"

        text += f"""

📊 <b>Итого чатов:</b> {total_chats}
⏱️ <b>Примерное время:</b> {estimate_mailing_time(total_chats)}

⚠️ <b>Внимание:</b> Отменить рассылку после запуска будет невозможно!"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🚀 Начать рассылку", callback_data="mailing_execute_now"
                    ),
                    InlineKeyboardButton(
                        text="⏰ Запланировать", callback_data="mailing_schedule"
                    ),
                ],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="mailing_create")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="menu_mailing")],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.set_state(MailingStates.confirming)
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@mailing_router.callback_query(F.data == "mailing_execute_now")
async def execute_mailing_now(
    callback: types.CallbackQuery, database: "Database", state: FSMContext
):
    """Немедленное выполнение рассылки"""
    try:
        data = await state.get_data()
        template_id = data.get("selected_template_id")
        selected_groups = data.get("selected_groups", [])

        # Создаем запись о рассылке в БД
        groups = await database.get_chat_groups()
        selected_group_objects = [g for g in groups if g.id in selected_groups]
        total_chats = sum(len(g.chat_ids) for g in selected_group_objects if g.chat_ids)

        mailing = await database.create_mailing(
            template_id=template_id, group_ids=selected_groups, total_chats=total_chats
        )

        await callback.message.edit_text(
            "🚀 <b>Рассылка запущена!</b>\n\n"
            f"📊 <b>ID рассылки:</b> {mailing.id}\n"
            f"📮 <b>Чатов для обработки:</b> {total_chats}\n\n"
            "📈 <i>Прогресс будет отображаться в реальном времени...</i>"
        )

        # Запускаем рассылку в фоне
        asyncio.create_task(
            execute_mailing_task(
                callback.message.bot,
                callback.message.chat.id,
                mailing.id,
                template_id,
                selected_group_objects,
                database,
            )
        )

        await state.clear()
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Ошибка запуска рассылки: {e}", show_alert=True)


# ========== ВЫПОЛНЕНИЕ РАССЫЛКИ ==========


async def execute_mailing_task(
    bot,
    admin_chat_id: int,
    mailing_id: int,
    template_id: int,
    groups: List,
    database: "Database",
):
    """Асинхронная задача выполнения рассылки"""
    try:
        # Получаем шаблон
        template = await database.get_template(template_id)
        if not template:
            await bot.send_message(admin_chat_id, "❌ Шаблон не найден")
            return

        # Собираем все chat_ids
        all_chat_ids = []
        for group in groups:
            if group.chat_ids:
                all_chat_ids.extend(group.chat_ids)

        # Удаляем дубликаты
        unique_chat_ids = list(set(all_chat_ids))

        sent_count = 0
        failed_count = 0

        # Отправляем прогресс каждые 10 сообщений
        progress_interval = max(1, len(unique_chat_ids) // 20)

        for i, chat_id in enumerate(unique_chat_ids, 1):
            try:
                # Отправляем сообщение
                if template.file_path and os.path.exists(template.file_path):
                    # Отправляем с файлом
                    with open(template.file_path, "rb") as file:
                        await bot.send_document(
                            chat_id=chat_id,
                            document=BufferedInputFile(
                                file.read(),
                                filename=os.path.basename(template.file_path),
                            ),
                            caption=template.text,
                        )
                else:
                    # Отправляем только текст
                    await bot.send_message(chat_id, template.text)

                sent_count += 1

                # Отправляем обновление прогресса
                if i % progress_interval == 0 or i == len(unique_chat_ids):
                    progress_text = f"""📈 <b>Прогресс рассылки #{mailing_id}</b>

✅ <b>Отправлено:</b> {sent_count}
❌ <b>Ошибок:</b> {failed_count}
📊 <b>Обработано:</b> {i} из {len(unique_chat_ids)}
📈 <b>Прогресс:</b> {i / len(unique_chat_ids) * 100:.1f}%"""

                    try:
                        await bot.send_message(admin_chat_id, progress_text)
                    except:
                        pass  # Игнорируем ошибки отправки прогресса

                # Задержка между отправками
                await asyncio.sleep(0.1)

            except Exception as e:
                failed_count += 1
                print(f"Ошибка отправки в чат {chat_id}: {e}")

                # Увеличиваем задержку при ошибках
                await asyncio.sleep(0.5)

        # Обновляем статистику в БД
        await database.update_mailing_stats(mailing_id, sent_count, failed_count)

        # Отправляем финальный отчет
        success_rate = (
            (sent_count / len(unique_chat_ids) * 100) if unique_chat_ids else 0
        )

        final_text = f"""✅ <b>Рассылка #{mailing_id} завершена!</b>

📊 <b>Статистика:</b>
✅ Успешно: {sent_count}
❌ Ошибок: {failed_count}
📈 Успешность: {success_rate:.1f}%

⏱️ <b>Время завершения:</b> {datetime.now().strftime('%H:%M:%S')}"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📊 История рассылок", callback_data="mailings_history"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏠 Главное меню", callback_data="menu_main"
                    )
                ],
            ]
        )

        await bot.send_message(admin_chat_id, final_text, reply_markup=keyboard)

    except Exception as e:
        error_text = f"""❌ <b>Ошибка рассылки #{mailing_id}</b>

🔍 <b>Детали:</b> {str(e)}

Рассылка была прервана."""

        await bot.send_message(admin_chat_id, error_text)
        await database.update_mailing_stats(
            mailing_id, sent_count, failed_count, status="failed"
        )


# ========== ИСТОРИЯ РАССЫЛОК ==========


@mailing_router.callback_query(F.data == "mailings_history")
async def show_mailings_history(callback: types.CallbackQuery, database: "Database"):
    """Показать историю рассылок"""
    try:
        mailings = await database.get_mailings_history(limit=10)

        if not mailings:
            text = """📊 <b>История рассылок</b>

❌ <i>Рассылки не найдены</i>

Создайте первую рассылку для отображения статистики."""

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📮 Создать рассылку", callback_data="mailing_create"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад", callback_data="menu_mailing"
                        )
                    ],
                ]
            )

        else:
            text = f"""📊 <b>История рассылок</b>

📈 <i>Последние {len(mailings)} рассылок:</i>

"""

            for mailing in mailings:
                created_date = mailing.created_at.strftime("%d.%m %H:%M")
                success_rate = 0
                if mailing.total_chats > 0:
                    success_rate = mailing.sent_count / mailing.total_chats * 100

                status_icon = {
                    "pending": "⏳",
                    "running": "🚀",
                    "completed": "✅",
                    "failed": "❌",
                }.get(mailing.status, "❓")

                text += f"""🔸 <b>#{mailing.id}</b> - {created_date} {status_icon}
   📊 {mailing.sent_count}/{mailing.total_chats} ({success_rate:.0f}%)
   ❌ Ошибок: {mailing.failed_count}

"""

            keyboard_buttons = []
            for mailing in mailings[:5]:  # Показываем кнопки для первых 5
                button_text = (
                    f"📊 #{mailing.id} ({mailing.created_at.strftime('%d.%m')})"
                )
                keyboard_buttons.append(
                    [
                        InlineKeyboardButton(
                            text=button_text,
                            callback_data=f"mailing_details_{mailing.id}",
                        )
                    ]
                )

            keyboard_buttons.extend(
                [
                    [
                        InlineKeyboardButton(
                            text="📮 Новая рассылка", callback_data="mailing_create"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад", callback_data="menu_mailing"
                        )
                    ],
                ]
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@mailing_router.callback_query(F.data.startswith("mailing_details_"))
async def show_mailing_details(callback: types.CallbackQuery, database: "Database"):
    """Показать детали конкретной рассылки"""
    try:
        mailing_id = int(callback.data.split("_")[-1])
        mailing = await database.get_mailing(mailing_id)

        if not mailing:
            await callback.answer("❌ Рассылка не найдена", show_alert=True)
            return

        # Получаем шаблон и группы
        template = await database.get_template(mailing.template_id)

        # Подсчитываем статистику
        success_rate = 0
        if mailing.total_chats > 0:
            success_rate = mailing.sent_count / mailing.total_chats * 100

        status_text = {
            "pending": "⏳ Ожидает",
            "running": "🚀 Выполняется",
            "completed": "✅ Завершена",
            "failed": "❌ Ошибка",
        }.get(mailing.status, "❓ Неизвестно")

        created_date = mailing.created_at.strftime("%d.%m.%Y %H:%M:%S")

        text = f"""📊 <b>Детали рассылки #{mailing.id}</b>

📋 <b>Шаблон:</b> {template.name if template else "Удален"}
📅 <b>Создана:</b> {created_date}
🎯 <b>Статус:</b> {status_text}

📈 <b>Статистика:</b>
✅ Отправлено: {mailing.sent_count}
❌ Ошибок: {mailing.failed_count}
📊 Всего чатов: {mailing.total_chats}
📈 Успешность: {success_rate:.1f}%

📄 <b>Детали ошибок:</b>"""

        if mailing.failed_count > 0:
            text += f"\n• Недоступные чаты: ~{mailing.failed_count}"
            text += "\n• Возможные причины: бот не админ, чат удален"
        else:
            text += "\n• Ошибок не обнаружено"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Повторить рассылку",
                        callback_data=f"mailing_repeat_{mailing.id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ К истории", callback_data="mailings_history"
                    )
                ],
            ]
        )

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except ValueError:
        await callback.answer("❌ Неверный ID рассылки", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========


def estimate_mailing_time(chat_count: int) -> str:
    """Оценка времени выполнения рассылки"""
    # Примерно 0.1 секунды на сообщение + запас
    estimated_seconds = chat_count * 0.15

    if estimated_seconds < 60:
        return f"~{int(estimated_seconds)} сек"
    elif estimated_seconds < 3600:
        return f"~{int(estimated_seconds / 60)} мин"
    else:
        hours = int(estimated_seconds / 3600)
        minutes = int((estimated_seconds % 3600) / 60)
        return f"~{hours}ч {minutes}м"


# ========== ПЛАНИРОВАНИЕ РАССЫЛОК ==========


@mailing_router.callback_query(F.data == "mailing_schedule")
async def schedule_mailing(callback: types.CallbackQuery, state: FSMContext):
    """Планирование рассылки на определенное время"""
    text = """⏰ <b>Планирование рассылки</b>

🗓️ Введите дату отправки в формате ДД.ММ.ГГГГ:

<i>Примеры:
• 15.12.2024
• 01.01.2025</i>

💡 <b>Примечание:</b> Дата должна быть не раньше сегодняшнего дня."""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад", callback_data="mailing_confirm_groups"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="menu_mailing")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(MailingStates.schedule_date)
    await callback.answer()


@mailing_router.message(MailingStates.schedule_date)
async def process_schedule_date(message: types.Message, state: FSMContext):
    """Обработка даты планирования"""
    try:
        date_text = message.text.strip()

        # Парсим дату
        try:
            scheduled_date = datetime.strptime(date_text, "%d.%m.%Y")

            # Проверяем, что дата не в прошлом
            if scheduled_date.date() < datetime.now().date():
                await message.answer(
                    "❌ Дата не может быть в прошлом. Попробуйте еще раз:"
                )
                return

        except ValueError:
            await message.answer(
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ\n\n"
                "Попробуйте еще раз:"
            )
            return

        await state.update_data(scheduled_date=scheduled_date)

        text = f"""⏰ <b>Планирование рассылки</b>

✅ <b>Дата:</b> {scheduled_date.strftime('%d.%m.%Y')}

🕐 Теперь введите время в формате ЧЧ:ММ:

<i>Примеры:
• 09:00
• 15:30
• 23:45</i>"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="menu_mailing")]
            ]
        )

        await message.answer(text, reply_markup=keyboard)
        await state.set_state(MailingStates.schedule_time)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@mailing_router.message(MailingStates.schedule_time)
async def process_schedule_time(
    message: types.Message, state: FSMContext, database: "Database"
):
    """Обработка времени планирования"""
    try:
        time_text = message.text.strip()

        # Парсим время
        try:
            time_obj = datetime.strptime(time_text, "%H:%M").time()
        except ValueError:
            await message.answer(
                "❌ Неверный формат времени. Используйте ЧЧ:ММ\n\n"
                "Попробуйте еще раз:"
            )
            return

        # Получаем данные из состояния
        data = await state.get_data()
        scheduled_date = data.get("scheduled_date")

        # Объединяем дату и время
        scheduled_datetime = datetime.combine(scheduled_date.date(), time_obj)

        # Проверяем, что время не в прошлом
        if scheduled_datetime <= datetime.now():
            await message.answer(
                "❌ Время не может быть в прошлом. Попробуйте еще раз:"
            )
            return

        # Сохраняем запланированную рассылку (здесь можно добавить в БД)
        await message.answer(
            f"⏰ <b>Рассылка запланирована!</b>\n\n"
            f"📅 <b>Дата и время:</b> {scheduled_datetime.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📝 <i>Функция планирования будет добавлена в следующих версиях.\n"
            f"Пока что используйте немедленную отправку.</i>",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🚀 Отправить сейчас",
                            callback_data="mailing_execute_now",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🏠 Главное меню", callback_data="menu_main"
                        )
                    ],
                ]
            ),
        )

        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()
