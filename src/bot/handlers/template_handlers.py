import os
import json
import time
from typing import TYPE_CHECKING, Optional, List

from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
    MessageEntity,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

if TYPE_CHECKING:
    from database import Database
    from menu_system import MenuManager

# Роутер
template_router = Router()

# Конфиги
TEMPLATE_FILES_DIR = "files/templates"
EXPORTS_DIR = "files/exports"
PAGE_SIZE = 8  # для пагинации списка шаблонов
os.makedirs(TEMPLATE_FILES_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)


# ===== FSM СОСТОЯНИЯ =====
class TemplateStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_text = State()
    waiting_for_file = State()
    editing_name = State()
    editing_text = State()
    editing_file = State()
    send_template_chat_id = State()
    import_waiting_file = State()
    list_pagination = State()  # опционально для сложной логики пагинации


# ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======
def entities_to_dicts(entities: Optional[List[MessageEntity]]) -> Optional[List[dict]]:
    """Преобразовать MessageEntity -> list[dict] для хранения"""
    if not entities:
        return None
    out = []
    for ent in entities:
        d = {
            "type": ent.type,
            "offset": ent.offset,
            "length": ent.length,
            # не все поля всегда есть
            "url": getattr(ent, "url", None),
            "user": None,
            "language": getattr(ent, "language", None),
        }
        # user может быть объектом
        if getattr(ent, "user", None):
            try:
                out_user = {
                    "id": ent.user.id,
                    "is_bot": ent.user.is_bot,
                    "first_name": ent.user.first_name,
                    "username": getattr(ent.user, "username", None),
                    "language_code": getattr(ent.user, "language_code", None),
                }
                d["user"] = out_user
            except Exception:
                d["user"] = None
        out.append(d)
    return out


def dicts_to_entities(dicts: Optional[List[dict]]) -> Optional[List[MessageEntity]]:
    """Преобразовать list[dict] -> list[MessageEntity] для отправки"""
    if not dicts:
        return None
    ents = []
    for d in dicts:
        # создаём MessageEntity с основными полями
        try:
            ent = MessageEntity(
                type=d.get("type"),
                offset=int(d.get("offset", 0)),
                length=int(d.get("length", 0)),
                url=d.get("url"),
                language=d.get("language"),
            )
            # поле user оставляем None (Telegram API принимает только user объект в определённых типах,
            # но обычно покупать не нужно). Если потребуется — можно восстановить User.
            ents.append(ent)
        except Exception:
            continue
    return ents


def build_template_keyboard_for_view(template, include_preview=True):
    """Построить клавиатуру для просмотра шаблона (view)"""
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="✏️ Редактировать", callback_data=f"template_edit_{template.id}"
        ),
        InlineKeyboardButton(
            text="🗑️ Удалить", callback_data=f"template_delete_{template.id}"
        ),
    )
    # расширенные кнопки
    kb.row(
        InlineKeyboardButton(
            text="🖊 Название", callback_data=f"template_edit_name_{template.id}"
        ),
        InlineKeyboardButton(
            text="📝 Текст", callback_data=f"template_edit_text_{template.id}"
        ),
    )
    kb.row(
        InlineKeyboardButton(
            text="📎 Файл", callback_data=f"template_edit_file_{template.id}"
        ),
        InlineKeyboardButton(
            text="🗑️ Удалить файл", callback_data=f"template_remove_file_{template.id}"
        ),
    )
    if include_preview:
        kb.row(
            InlineKeyboardButton(
                text="👁 Предпросмотр", callback_data=f"template_preview_{template.id}"
            ),
            InlineKeyboardButton(
                text="📤 Отправить", callback_data=f"template_sendto_{template.id}"
            ),
        )
    kb.row(InlineKeyboardButton(text="◀️ К списку", callback_data="templates_list"))
    return kb.as_markup()


def build_pagination_keyboard(total: int, page: int, prefix: str = "templates_page_"):
    """Пагинация: total items, page index (0-based)"""
    kb = InlineKeyboardMarkup(row_width=5)
    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    buttons = []
    if pages <= 1:
        buttons.append(
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_templates")]
        )
        kb.inline_keyboard = buttons
        return kb

    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}{page-1}")
        )
    nav_row.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav_row.append(
            InlineKeyboardButton(text="➡️", callback_data=f"{prefix}{page+1}")
        )
    kb.inline_keyboard.append(nav_row)
    # добавляем кнопку "Создать новый" и "Назад"
    kb.inline_keyboard.append(
        [
            InlineKeyboardButton(
                text="➕ Создать новый", callback_data="templates_new"
            ),
            InlineKeyboardButton(text="◀️ Назад", callback_data="menu_templates"),
        ]
    )
    return kb


# ====== ОРИГИНАЛЬНЫЕ ОБРАБОТЧИКИ (создание / список / просмотр / удаление / тест) ======
# Я оставляю в основном оригинальную логику, но немного расширяю показ и пагинацию.


@template_router.callback_query(F.data == "templates_list")
async def show_templates_list(
    callback: types.CallbackQuery, database: "Database", menu_manager: "MenuManager"
):
    """Показать список шаблонов с пагинацией (страница 0)"""
    await show_templates_list_page(callback, database, menu_manager, page=0)


@template_router.callback_query(F.data.startswith("templates_page_"))
async def templates_list_page_callback(
    callback: types.CallbackQuery, database: "Database", menu_manager: "MenuManager"
):
    """Обработчик навигации по страницам"""
    try:
        page = int(callback.data.split("_")[-1])
    except Exception:
        page = 0
    await show_templates_list_page(callback, database, menu_manager, page=page)


async def show_templates_list_page(
    callback: types.CallbackQuery,
    database: "Database",
    menu_manager: "MenuManager",
    page: int = 0,
):
    """Рендер списка шаблонов постранично"""
    try:
        templates = await database.get_templates()
        total = len(templates)

        if total == 0:
            text = """📋 <b>Список шаблонов</b>

❌ <i>Шаблоны не найдены</i>

Создайте первый шаблон, нажав кнопку ниже."""
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ Создать новый", callback_data="templates_new"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="◀️ Назад", callback_data="menu_templates"
                        )
                    ],
                ]
            )
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
            return

        # сортируем по id (или по created_at если нужно)
        templates = sorted(templates, key=lambda t: getattr(t, "id", 0))
        pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
        if page < 0:
            page = 0
        if page >= pages:
            page = pages - 1

        start = page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_items = templates[start:end]

        text = f"📋 <b>Список шаблонов</b>\n\n📊 <i>Найдено шаблонов: {total}</i>\n\nВыберите шаблон:"
        # Строим клавиатуру
        kb = InlineKeyboardMarkup(row_width=1)
        for tpl in page_items:
            icon = "📄" if not getattr(tpl, "file_path", None) else "📎"
            display_name = tpl.name if len(tpl.name) <= 40 else tpl.name[:37] + "..."
            kb.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"{icon} {display_name}",
                        callback_data=f"template_view_{tpl.id}",
                    )
                ]
            )

        # пагинация и кнопки
        pag_kb = build_pagination_keyboard(total, page)
        # объединяем: сначала наши элементы, затем пагинация
        kb.inline_keyboard.extend(pag_kb.inline_keyboard)

        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@template_router.callback_query(F.data == "templates_new")
async def start_template_creation(callback: types.CallbackQuery, state: FSMContext):
    """Начать создание нового шаблона"""
    text = """➕ <b>Создание нового шаблона</b>

📝 Введите название шаблона:

<i>Например: "Прайс-лист Декабрь 2024" или "Акция недели"</i>"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="templates_list")]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(TemplateStates.waiting_for_name)
    await callback.answer()


@template_router.message(TemplateStates.waiting_for_name)
async def process_template_name(message: types.Message, state: FSMContext):
    """Обработка названия шаблона"""
    name = (message.text or "").strip()

    if len(name) < 3:
        await message.answer(
            "❌ Название слишком короткое. Минимум 3 символа.\n\nПопробуйте еще раз:"
        )
        return

    if len(name) > 100:
        await message.answer(
            "❌ Название слишком длинное. Максимум 100 символов.\n\nПопробуйте еще раз:"
        )
        return

    # Сохраняем название в состоянии
    await state.update_data(template_name=name)

    text = f"""✅ <b>Название принято:</b> {name}

📝 Теперь введите текст шаблона:

<i>Вы можете использовать встроенное форматирование Telegram (жирный, курсив, ссылки, код и т.д.).</i>"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="templates_list")]
        ]
    )

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(TemplateStates.waiting_for_text)


@template_router.message(TemplateStates.waiting_for_text)
async def process_template_text(message: types.Message, state: FSMContext):
    """Обработка текста шаблона (с сохранением entities)"""
    # Сохраняем текст и entities
    text = message.text or message.caption or ""
    entities = (
        getattr(message, "entities", None)
        or getattr(message, "caption_entities", None)
        or None
    )

    if len(text.strip()) < 10:
        await message.answer(
            "❌ Текст слишком короткий. Минимум 10 символов.\n\nПопробуйте еще раз:"
        )
        return

    if len(text) > 4000:
        await message.answer(
            "❌ Текст слишком длинный. Максимум 4000 символов.\n\nПопробуйте еще раз:"
        )
        return

    await state.update_data(template_text=text)
    await state.update_data(template_entities=entities_to_dicts(entities))

    file_text = """✅ <b>Текст принят!</b>

📎 Хотите прикрепить файл к шаблону?

<i>Поддерживаемые форматы:
• 📄 Документы (PDF, DOCX, XLSX, TXT)
• 🖼️ Изображения (JPG, PNG, GIF)
Максимальный размер: 20 МБ</i>"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📎 Прикрепить файл", callback_data="template_attach_file"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Создать без файла", callback_data="template_create_finish"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="templates_list")],
        ]
    )

    await message.answer(file_text, reply_markup=keyboard)


@template_router.callback_query(F.data == "template_attach_file")
async def request_file_upload(callback: types.CallbackQuery, state: FSMContext):
    """Запрос загрузки файла"""
    text = """📎 <b>Загрузка файла</b>

Отправьте файл, который хотите прикрепить к шаблону.

⚠️ Максимальный размер: 20 МБ"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Создать без файла", callback_data="template_create_finish"
                )
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="templates_list")],
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await state.set_state(TemplateStates.waiting_for_file)
    await callback.answer()


@template_router.message(TemplateStates.waiting_for_file)
async def process_template_file(
    message: types.Message, state: FSMContext, database: "Database"
):
    """Обработка файла при создании шаблона"""
    file = None
    file_name = None
    file_size = 0

    # Определяем тип файла
    if message.document:
        file = message.document
        file_name = file.file_name
        file_size = file.file_size
    elif message.photo:
        file = message.photo[-1]  # Берем самое большое фото
        file_name = f"image_{file.file_id}.jpg"
        file_size = file.file_size
    else:
        await message.answer(
            "❌ Неподдерживаемый тип файла.\n\nОтправьте документ или изображение:"
        )
        return

    # Проверяем размер файла
    if file_size > 20 * 1024 * 1024:  # 20 МБ
        await message.answer(
            "❌ Файл слишком большой. Максимальный размер: 20 МБ.\n\n"
            "Отправьте файл меньшего размера:"
        )
        return

    try:
        # Загружаем файл
        bot = message.bot
        file_info = await bot.get_file(file.file_id)
        file_path = f"{TEMPLATE_FILES_DIR}/{file.file_id}_{file_name}"

        await bot.download_file(file_info.file_path, file_path)

        # Сохраняем путь к файлу в состоянии
        await state.update_data(template_file_path=file_path)

        await message.answer(
            f"✅ <b>Файл загружен:</b> {file_name}\n"
            f"📊 <b>Размер:</b> {file_size // 1024} КБ\n\n"
            "Создаем шаблон..."
        )

        # Автоматически завершаем создание
        await finish_template_creation(message, state, database)

    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки файла: {e}")


@template_router.callback_query(F.data == "template_create_finish")
async def finish_template_creation_callback(
    callback: types.CallbackQuery, state: FSMContext, database: "Database"
):
    """Завершение создания шаблона через callback"""
    await finish_template_creation(callback.message, state, database)
    await callback.answer()


async def finish_template_creation(
    message: types.Message, state: FSMContext, database: "Database"
):
    """Завершение создания шаблона"""
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        template_name = data.get("template_name")
        template_text = data.get("template_text")
        template_file_path = data.get("template_file_path")
        template_entities = data.get("template_entities")  # list[dict] или None

        if not template_name or not template_text:
            await message.answer("❌ Ошибка: отсутствуют обязательные данные")
            await state.clear()
            return

        # Создаём запись. Передаём entities если БД поддерживает.
        # Если ваша БД не принимает `entities`, просто удалите параметр entities=template_entities.
        template = await database.create_template(
            name=template_name,
            text=template_text,
            file_path=template_file_path,
            entities=template_entities,
        )

        if template:
            file_info = ""
            if template_file_path:
                file_info = f"\n📎 <b>Файл:</b> {os.path.basename(template_file_path)}"

            success_text = f"""✅ <b>Шаблон создан успешно!</b>

📄 <b>Название:</b> {template_name}
📝 <b>Текст:</b> {template_text[:100]}{'...' if len(template_text) > 100 else ''}
🔢 <b>ID:</b> {template.id}{file_info}"""

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📋 К списку шаблонов", callback_data="templates_list"
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
            await message.answer("❌ Ошибка создания шаблона")

        # Очищаем состояние
        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Ошибка при создании шаблона: {e}")
        await state.clear()


@template_router.callback_query(F.data.startswith("template_view_"))
async def view_template(callback: types.CallbackQuery, database: "Database"):
    """Просмотр конкретного шаблона"""
    try:
        template_id = int(callback.data.split("_")[-1])
        template = await database.get_template(template_id)

        if not template:
            await callback.answer("❌ Шаблон не найден", show_alert=True)
            return

        # Формируем информацию о шаблоне
        file_info = (
            "❌ Нет"
            if not getattr(template, "file_path", None)
            else f"✅ {os.path.basename(template.file_path)}"
        )
        created_date = getattr(template, "created_at", None)
        created_str = created_date.strftime("%d.%m.%Y %H:%M") if created_date else "—"

        text = f"""📄 <b>Шаблон: {template.name}</b>

📝 <b>Текст:</b>
{template.text if template.text else '—'}

📎 <b>Файл:</b> {file_info}
📅 <b>Создан:</b> {created_str}
🔢 <b>ID:</b> {template.id}"""

        keyboard = build_template_keyboard_for_view(template, include_preview=True)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except ValueError:
        await callback.answer("❌ Неверный ID шаблона", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@template_router.callback_query(F.data.startswith("template_delete_"))
async def confirm_template_deletion(callback: types.CallbackQuery):
    """Подтверждение удаления шаблона"""
    template_id = callback.data.split("_")[-1]

    text = """🗑️ <b>Удаление шаблона</b>

⚠️ <b>Внимание!</b> Это действие нельзя отменить.

Вы уверены, что хотите удалить этот шаблон?"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=f"template_delete_confirm_{template_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data=f"template_view_{template_id}"
                ),
            ]
        ]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@template_router.callback_query(F.data.startswith("template_delete_confirm_"))
async def delete_template(callback: types.CallbackQuery, database: "Database"):
    """Удаление шаблона"""
    try:
        template_id = int(callback.data.split("_")[-1])
        success = await database.delete_template(template_id)

        if success:
            await callback.answer("✅ Шаблон удален", show_alert=True)
            # Возвращаемся к списку шаблонов (страница 0)
            await show_templates_list(callback, database, None)
        else:
            await callback.answer("❌ Ошибка удаления", show_alert=True)

    except ValueError:
        await callback.answer("❌ Неверный ID шаблона", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


@template_router.callback_query(F.data.startswith("template_test_"))
async def test_template(callback: types.CallbackQuery, database: "Database"):
    """Тестовая отправка шаблона админу (в чат где был вызов)"""
    try:
        template_id = int(callback.data.split("_")[-1])
        template = await database.get_template(template_id)

        if not template:
            await callback.answer("❌ Шаблон не найден", show_alert=True)
            return

        # используем entities из шаблона если есть
        entities = getattr(template, "entities", None)
        entities_objs = dicts_to_entities(entities)

        test_text = f"🧪 <b>ТЕСТ ШАБЛОНА</b>\n\n{template.text}"

        if getattr(template, "file_path", None) and os.path.exists(template.file_path):
            with open(template.file_path, "rb") as file:
                await callback.message.answer_document(
                    document=BufferedInputFile(
                        file.read(), filename=os.path.basename(template.file_path)
                    ),
                    caption=test_text,
                    parse_mode=None,  # entities used instead
                    caption_entities=entities_objs if entities_objs else None,
                )
        else:
            await callback.message.answer(test_text, entities=entities_objs)

        await callback.answer("✅ Тестовое сообщение отправлено")

    except ValueError:
        await callback.answer("❌ Неверный ID шаблона", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка отправки: {e}", show_alert=True)


# ====== РЕДАКТИРОВАНИЕ НАЗВАНИЯ ======
@template_router.callback_query(F.data.startswith("template_edit_name_"))
async def start_edit_name(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования названия шаблона"""
    try:
        template_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return

    await state.update_data(edit_template_id=template_id)
    await state.set_state(TemplateStates.editing_name)

    await callback.message.edit_text(
        "📝 Введите новое название для шаблона:\n\n<i>Минимум 3 символа, максимум 100</i>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data=f"template_view_{template_id}"
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@template_router.message(TemplateStates.editing_name)
async def process_edit_name(
    message: types.Message, state: FSMContext, database: "Database"
):
    name = (message.text or "").strip()
    if len(name) < 3:
        await message.answer(
            "❌ Слишком короткое название (мин. 3 символа). Попробуйте снова:"
        )
        return
    if len(name) > 100:
        await message.answer(
            "❌ Слишком длинное название (макс. 100 символов). Попробуйте снова:"
        )
        return

    data = await state.get_data()
    template_id = data.get("edit_template_id")
    if template_id is None:
        await message.answer("❌ Внутренняя ошибка: отсутствует ID шаблона")
        await state.clear()
        return

    success = await database.update_template(template_id, name=name, entities=None)
    if success:
        await message.answer(f"✅ Название шаблона изменено на: <b>{name}</b>")
        # возвращаемся к просмотру шаблона
        # попытка отредактировать сообщение с view: если нужно, можно отправить view
    else:
        await message.answer("❌ Ошибка при изменении названия")

    await state.clear()


# ====== РЕДАКТИРОВАНИЕ ТЕКСТА (с сохранением entities) ======
@template_router.callback_query(F.data.startswith("template_edit_text_"))
async def start_edit_text(
    callback: types.CallbackQuery, state: FSMContext, database: "Database"
):
    try:
        template_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return

    template = await database.get_template(template_id)
    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return

    await state.update_data(edit_template_id=template_id)
    await state.set_state(TemplateStates.editing_text)

    # Показываем текущее содержимое как подсказку
    preview = template.text if getattr(template, "text", None) else ""
    await callback.message.edit_text(
        f"✏️ <b>Редактирование текста</b>\n\nТекущее содержимое:\n{preview}\n\nОтправьте новый текст (поддерживается форматирование):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data=f"template_view_{template_id}"
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@template_router.message(TemplateStates.editing_text)
async def process_edit_text(
    message: types.Message, state: FSMContext, database: "Database"
):
    text = message.text or message.caption or ""
    entities = (
        getattr(message, "entities", None)
        or getattr(message, "caption_entities", None)
        or None
    )

    if len(text.strip()) < 10:
        await message.answer(
            "❌ Текст слишком короткий (мин. 10 символов). Попробуйте снова:"
        )
        return
    if len(text) > 4000:
        await message.answer(
            "❌ Текст слишком длинный (макс. 4000 символов). Попробуйте снова:"
        )
        return

    data = await state.get_data()
    template_id = data.get("edit_template_id")
    if template_id is None:
        await message.answer("❌ Внутренняя ошибка: отсутствует ID шаблона")
        await state.clear()
        return

    success = await database.update_template(
        template_id, text=text, entities=entities_to_dicts(entities)
    )
    if success:
        await message.answer("✅ Текст шаблона успешно изменён")
    else:
        await message.answer("❌ Ошибка при изменении текста")

    await state.clear()


# ====== РЕДАКТИРОВАНИЕ ФАЙЛА ======
@template_router.callback_query(F.data.startswith("template_edit_file_"))
async def start_edit_file(
    callback: types.CallbackQuery, state: FSMContext, database: "Database"
):
    try:
        template_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return

    template = await database.get_template(template_id)
    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return

    await state.update_data(edit_template_id=template_id)
    await state.set_state(TemplateStates.editing_file)

    await callback.message.edit_text(
        "📎 Отправьте новый файл для шаблона (или нажмите «Удалить файл»):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🗑️ Удалить файл",
                        callback_data=f"template_remove_file_{template_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data=f"template_view_{template_id}"
                    )
                ],
            ]
        ),
    )
    await callback.answer()


@template_router.message(TemplateStates.editing_file)
async def process_edit_file(
    message: types.Message, state: FSMContext, database: "Database"
):
    file = None
    file_name = None
    file_size = 0

    if message.document:
        file = message.document
        file_name = file.file_name
        file_size = file.file_size
    elif message.photo:
        file = message.photo[-1]
        file_name = f"image_{file.file_id}.jpg"
        file_size = file.file_size
    else:
        await message.answer(
            "❌ Неподдерживаемый тип файла. Отправьте документ или изображение:"
        )
        return

    if file_size > 20 * 1024 * 1024:
        await message.answer("❌ Файл слишком большой (макс. 20 МБ). Отправьте другой:")
        return

    try:
        bot = message.bot
        file_info = await bot.get_file(file.file_id)
        file_path = f"{TEMPLATE_FILES_DIR}/{file.file_id}_{file_name}"
        await bot.download_file(file_info.file_path, file_path)

        data = await state.get_data()
        template_id = data.get("edit_template_id")
        if template_id is None:
            await message.answer("❌ Внутренняя ошибка: отсутствует ID шаблона")
            await state.clear()
            return

        success = await database.update_template(template_id, file_path=file_path)

        if success:
            await message.answer(f"✅ Файл шаблона обновлён: {file_name}")
        else:
            await message.answer("❌ Ошибка при сохранении файла")

    except Exception as e:
        await message.answer(f"❌ Ошибка загрузки файла: {e}")

    await state.clear()


# ====== УДАЛЕНИЕ ФАЙЛА ИЗ ШАБЛОНА ======
@template_router.callback_query(F.data.startswith("template_remove_file_"))
async def remove_file(callback: types.CallbackQuery, database: "Database"):
    try:
        template_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return

    # Получаем шаблон, чтобы удалить файл на диске и обновить БД
    tpl = await database.get_template(template_id)
    if not tpl:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return

    file_path = getattr(tpl, "file_path", None)
    success = await database.update_template(template_id, file_path=None)
    if success:
        # пытаемся удалить файл с диска
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        await callback.answer("✅ Файл удалён", show_alert=True)
        # обновить view
        await view_template(callback, database)
    else:
        await callback.answer("❌ Ошибка при удалении файла", show_alert=True)


# ====== ПРЕДПРОСМОТР ШАБЛОНА ======
@template_router.callback_query(F.data.startswith("template_preview_"))
async def preview_template(callback: types.CallbackQuery, database: "Database"):
    """Показать реальный превью (отправить сообщение с теми же entities)"""
    try:
        template_id = int(callback.data.split("_")[-1])
        template = await database.get_template(template_id)
        if not template:
            await callback.answer("❌ Шаблон не найден", show_alert=True)
            return

        entities = getattr(template, "entities", None)
        entities_objs = dicts_to_entities(entities)

        preview_text = f"👁 <b>ПРЕДПРОСМОТР</b>\n\n{template.text}"

        if getattr(template, "file_path", None) and os.path.exists(template.file_path):
            with open(template.file_path, "rb") as f:
                await callback.message.answer_document(
                    document=BufferedInputFile(
                        f.read(), filename=os.path.basename(template.file_path)
                    ),
                    caption=preview_text,
                    caption_entities=entities_objs if entities_objs else None,
                )
        else:
            await callback.message.answer(preview_text, entities=entities_objs)

        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка при предпросмотре: {e}", show_alert=True)


# ====== ОТПРАВКА ШАБЛОНА В УКАЗАННЫЙ ЧАТ ======
@template_router.callback_query(F.data.startswith("template_sendto_"))
async def start_send_to(callback: types.CallbackQuery, state: FSMContext):
    try:
        template_id = int(callback.data.split("_")[-1])
    except Exception:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return

    await state.update_data(send_template_id=template_id)
    await state.set_state(TemplateStates.send_template_chat_id)

    await callback.message.edit_text(
        "📤 Введите ID чата или пользователя, куда отправить шаблон:\n\n"
        "<i>Поддерживается: числовой ID (например -1001234567890) или username (@username)</i>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Отмена", callback_data=f"template_view_{template_id}"
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@template_router.message(TemplateStates.send_template_chat_id)
async def process_send_to(
    message: types.Message, state: FSMContext, database: "Database"
):
    chat_input = (message.text or "").strip()
    if not chat_input:
        await message.answer("❌ Пустой ввод. Введите ID чата или username:")
        return

    # поддерживаем username или числовный ID
    if chat_input.startswith("@"):
        chat_id = chat_input  # можно передать username боту
    elif chat_input.lstrip("-").isdigit():
        chat_id = int(chat_input)
    else:
        await message.answer(
            "❌ Некорректный ID/username. Введите числовой ID или @username:"
        )
        return

    data = await state.get_data()
    template_id = data.get("send_template_id")
    template = await database.get_template(template_id)
    if not template:
        await message.answer("❌ Шаблон не найден")
        await state.clear()
        return

    entities_objs = dicts_to_entities(getattr(template, "entities", None))
    try:
        bot = message.bot
        if getattr(template, "file_path", None) and os.path.exists(template.file_path):
            with open(template.file_path, "rb") as f:
                await bot.send_document(
                    chat_id=chat_id,
                    document=BufferedInputFile(
                        f.read(), filename=os.path.basename(template.file_path)
                    ),
                    caption=template.text,
                    caption_entities=entities_objs if entities_objs else None,
                )
        else:
            await bot.send_message(
                chat_id=chat_id, text=template.text, entities=entities_objs
            )

        await message.answer("✅ Шаблон успешно отправлен")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке: {e}")

    await state.clear()


# ====== ЭКСПОРТ / ИМПОРТ ШАБЛОНОВ ======
@template_router.callback_query(F.data == "template_export_all")
async def export_all_templates(callback: types.CallbackQuery, database: "Database"):
    """Экспорт всех шаблонов в JSON и отправка файла админу"""
    try:
        templates = await database.get_templates()
        data = []
        for t in templates:
            data.append(
                {
                    "id": getattr(t, "id", None),
                    "name": getattr(t, "name", None),
                    "text": getattr(t, "text", None),
                    "file_path": getattr(t, "file_path", None),
                    "entities": getattr(t, "entities", None),
                    "created_at": (
                        getattr(t, "created_at", None).isoformat()
                        if getattr(t, "created_at", None)
                        else None
                    ),
                }
            )
        filename = f"{EXPORTS_DIR}/templates_export_{int(time.time())}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # отправляем файл пользователю
        with open(filename, "rb") as f:
            await callback.message.answer_document(
                document=BufferedInputFile(
                    f.read(), filename=os.path.basename(filename)
                ),
                caption="✅ Экспорт шаблонов",
            )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка экспорта: {e}", show_alert=True)


@template_router.callback_query(F.data == "template_import")
async def start_import_templates(callback: types.CallbackQuery, state: FSMContext):
    """Запрос файла JSON для импорта"""
    await state.set_state(TemplateStates.import_waiting_file)
    await callback.message.edit_text(
        "📥 Отправьте JSON-файл с шаблонами для импорта.\n\n"
        "Формат: список объектов с полями name, text, optional file_path и entities.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="templates_list")]
            ]
        ),
    )
    await callback.answer()


@template_router.message(TemplateStates.import_waiting_file)
async def process_import_file(
    message: types.Message, state: FSMContext, database: "Database"
):
    """Приём JSON-файла и импорт шаблонов"""
    doc = message.document
    if not doc:
        await message.answer("❌ Отправьте JSON-файл (документ).")
        return

    if not doc.file_name.lower().endswith(".json"):
        await message.answer("❌ Файл должен быть в формате .json")
        return

    try:
        bot = message.bot
        file_info = await bot.get_file(doc.file_id)
        temp_path = f"{EXPORTS_DIR}/{doc.file_id}_{doc.file_name}"
        await bot.download_file(file_info.file_path, temp_path)

        with open(temp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported = 0
        for item in data:
            name = item.get("name")
            text = item.get("text")
            file_path = item.get("file_path")
            entities = item.get("entities")
            if not name or not text:
                continue
            # создаём шаблон. Если file_path указывает на локальный файл — можно попытаться скопировать,
            # но в общем случае просто сохраняем ссылку/путь.
            await database.create_template(
                name=name, text=text, file_path=file_path, entities=entities
            )
            imported += 1

        await message.answer(f"✅ Импортировано шаблонов: {imported}")
    except Exception as e:
        await message.answer(f"❌ Ошибка импорта: {e}")
    finally:
        await state.clear()


# Дополнительно: быстрые команды для меню (можно привязать в menus.py)
@template_router.callback_query(F.data == "menu_templates")
async def open_templates_menu(callback: types.CallbackQuery):
    """Обработчик нажатия 'menu_templates' — просто редирект на templates_list"""
    # Перенаправляем на список
    await show_templates_list(
        callback, callback.bot.get("db"), None
    )  # если у тебя db доступна в bot data
    # если нет — просто отвечаем
    await callback.answer()
