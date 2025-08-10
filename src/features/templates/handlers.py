from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from shared.pagination import MenuHelper, ConfirmationHelper, PaginationHelper

from .constants import *
from .services import *
from .models import *
from .keyboards import *


class TemplateStates(StatesGroup):
    waiting_name = State()
    waiting_text = State()
    waiting_file = State()


class TemplateStates(StatesGroup):
    waiting_name = State()
    waiting_text = State()
    waiting_file = State()


class TemplateHandlers:
    """Обработчики для работы с шаблонами"""

    def __init__(self, template_service: TemplateService):
        self.template_service = template_service
        self.router = Router()
        self._setup_handlers()

    def _setup_handlers(self):
        """Настройка обработчиков"""
        # Основные действия
        self.router.callback_query(F.data == "templates")(self.show_templates_menu)
        self.router.callback_query(F.data == "template_create")(self.start_create)
        self.router.callback_query(F.data == "template_list")(self.show_list)
        self.router.callback_query(F.data.startswith("template_view_"))(
            self.view_template
        )
        self.router.callback_query(F.data.startswith("template_delete_"))(
            self.delete_template
        )
        self.router.callback_query(F.data == "template_skip_file")(self.skip_file)

        # FSM состояния
        self.router.message(TemplateStates.waiting_name)(self.process_name)
        self.router.message(TemplateStates.waiting_text)(self.process_text)
        self.router.message(TemplateStates.waiting_file)(self.process_file)

    async def show_templates_menu(self, callback: types.CallbackQuery):
        """Показать меню шаблонов"""
        await callback.message.edit_text(
            TemplateTexts.menu_description(),
            reply_markup=TemplateKeyboards.main_menu(),
            parse_mode="HTML",
        )
        await callback.answer()

    async def start_create(self, callback: types.CallbackQuery, state: FSMContext):
        """Начать создание шаблона"""
        await callback.message.edit_text(
            TemplateTexts.create_name_prompt(),
            reply_markup=TemplateKeyboards.create_flow(),
            parse_mode="HTML",
        )
        await state.set_state(TemplateStates.waiting_name)
        await callback.answer()

    async def process_name(self, message: types.Message, state: FSMContext):
        """Обработка названия шаблона"""
        name = message.text.strip()

        # Быстрая валидация на UI уровне
        if len(name) < TemplateConstraints.MIN_NAME_LENGTH:
            await message.answer(TemplateMessages.NAME_TOO_SHORT)
            return

        if len(name) > TemplateConstraints.MAX_NAME_LENGTH:
            await message.answer(TemplateMessages.NAME_TOO_LONG)
            return

        await state.update_data(name=name)

        await message.answer(
            TemplateTexts.create_text_prompt(name),
            reply_markup=TemplateKeyboards.create_flow(),
            parse_mode="HTML",
        )
        await state.set_state(TemplateStates.waiting_text)

    async def process_text(self, message: types.Message, state: FSMContext):
        """Обработка текста шаблона"""
        text = message.text or message.caption or ""

        # Быстрая валидация на UI уровне
        if len(text.strip()) < TemplateConstraints.MIN_TEXT_LENGTH:
            await message.answer(TemplateMessages.TEXT_TOO_SHORT)
            return

        if len(text) > TemplateConstraints.MAX_TEXT_LENGTH:
            await message.answer(TemplateMessages.TEXT_TOO_LONG)
            return

        await state.update_data(text=text)

        await message.answer(
            TemplateTexts.create_file_prompt(),
            reply_markup=TemplateKeyboards.file_options(),
            parse_mode="HTML",
        )
        await state.set_state(TemplateStates.waiting_file)

    async def process_file(self, message: types.Message, state: FSMContext):
        """Обработка файла шаблона"""
        file_id = None
        file_type = None
        file_size = 0

        if message.document:
            file_id = message.document.file_id
            file_type = "document"
            file_size = message.document.file_size or 0
        elif message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
            file_size = message.photo[-1].file_size or 0
        else:
            await message.answer(TemplateMessages.UNSUPPORTED_FILE)
            return

        # Проверка размера файла
        if not TemplateValidator.validate_file_size(file_size):
            await message.answer(TemplateMessages.FILE_TOO_LARGE)
            return

        await self._create_template(message, state, file_id, file_type)

    async def skip_file(self, callback: types.CallbackQuery, state: FSMContext):
        """Пропустить файл и создать шаблон"""
        await self._create_template(callback.message, state)
        await callback.answer()

    async def _create_template(
        self,
        message: types.Message,
        state: FSMContext,
        file_id: str = None,
        file_type: str = None,
    ):
        """Создать шаблон"""
        data = await state.get_data()

        try:
            template_data = CreateTemplateData(
                name=data["name"],
                text=data["text"],
                file_id=file_id,
                file_type=file_type,
            )

            template = await self.template_service.create_template(template_data)

            await message.answer(
                TemplateTexts.template_created(template),
                reply_markup=TemplateKeyboards.create_flow(),
                parse_mode="HTML",
            )

        except TemplateValidationError as e:
            await message.answer(f"❌ Ошибка валидации: {e}")
        except Exception as e:
            await message.answer(f"❌ Ошибка создания: {e}")

        await state.clear()

    async def show_list(self, callback: types.CallbackQuery):
        """Показать список шаблонов"""
        try:
            templates = await self.template_service.get_templates()

            if not templates:
                await callback.message.edit_text(
                    TemplateTexts.empty_list(),
                    reply_markup=TemplateKeyboards.empty_list(),
                    parse_mode="HTML",
                )
                await callback.answer()
                return

            await callback.message.edit_text(
                TemplateTexts.list_header(len(templates)),
                reply_markup=TemplateKeyboards.template_list(templates),
                parse_mode="HTML",
            )
            await callback.answer()

        except Exception as e:
            await callback.answer(f"❌ Ошибка: {e}", show_alert=True)

    async def view_template(self, callback: types.CallbackQuery):
        """Просмотр шаблона"""
        try:
            template_id = int(callback.data.split("_")[-1])
            template = await self.template_service.get_template(template_id)

            if not template:
                await callback.answer(TemplateMessages.NOT_FOUND, show_alert=True)
                return

            await callback.message.edit_text(
                TemplateTexts.template_details(template),
                reply_markup=TemplateKeyboards.template_view(template.id),
                parse_mode="HTML",
            )
            await callback.answer()

        except ValueError:
            await callback.answer("❌ Неверный ID шаблона", show_alert=True)
        except Exception as e:
            await callback.answer(f"❌ Ошибка: {e}", show_alert=True)

    async def delete_template(self, callback: types.CallbackQuery):
        """Удалить шаблон"""
        try:
            template_id = int(callback.data.split("_")[-1])
            success = await self.template_service.delete_template(template_id)

            if success:
                await callback.answer(TemplateMessages.DELETED_SUCCESS, show_alert=True)
                await self.show_list(callback)  # Возвращаемся к списку
            else:
                await callback.answer(TemplateMessages.DELETE_ERROR, show_alert=True)

        except ValueError:
            await callback.answer("❌ Неверный ID шаблона", show_alert=True)
        except Exception as e:
            await callback.answer(f"❌ Ошибка: {e}", show_alert=True)

    async def process_file(self, message: types.Message, state: FSMContext):
        """Обработка файла шаблона"""
        file_id = None
        file_type = None

        if message.document:
            file_id = message.document.file_id
            file_type = "document"
        elif message.photo:
            file_id = message.photo[-1].file_id
            file_type = "photo"
        else:
            await message.answer(
                "❌ Неподдерживаемый тип файла.\n" "Отправьте фото или документ:"
            )
            return

        await self._create_template(message, state, file_id, file_type)

    async def skip_file(self, callback: types.CallbackQuery, state: FSMContext):
        """Пропустить файл и создать шаблон"""
        await self._create_template(callback.message, state)
        await callback.answer()

    async def _create_template(
        self,
        message: types.Message,
        state: FSMContext,
        file_id: str = None,
        file_type: str = None,
    ):
        """Создать шаблон"""
        data = await state.get_data()

        try:
            template_data = TemplateData(
                name=data["name"],
                text=data["text"],
                file_id=file_id,
                file_type=file_type,
            )

            template = await self.template_service.create_template(template_data)

            file_info = ""
            if file_id:
                file_info = f"\n📎 <b>Файл:</b> {'Фото' if file_type == 'photo' else 'Документ'}"

            await message.answer(
                f"✅ <b>Шаблон создан!</b>\n\n"
                f"🔢 <b>ID:</b> {template.id}\n"
                f"📝 <b>Название:</b> {template.name}{file_info}",
                reply_markup=ConfirmationHelper.create_back_keyboard("templates"),
                parse_mode="HTML",
            )

        except ValidationError as e:
            await message.answer(f"❌ Ошибка валидации: {e}")
        except Exception as e:
            await message.answer(f"❌ Ошибка создания: {e}")

        await state.clear()

    async def show_list(self, callback: types.CallbackQuery):
        """Показать список шаблонов"""
        try:
            templates = await self.template_service.get_templates()

            if not templates:
                await callback.message.edit_text(
                    "📄 <b>Список шаблонов</b>\n\n"
                    "❌ Шаблоны не найдены\n\n"
                    "Создайте первый шаблон для начала работы.",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="➕ Создать", callback_data="template_create"
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    text="◀️ Назад", callback_data="templates"
                                )
                            ],
                        ]
                    ),
                    parse_mode="HTML",
                )
                await callback.answer()
                return

            # Создаем кнопки для каждого шаблона
            buttons = []
            for template in templates:
                icon = "📎" if template.file_id else "📄"
                name = (
                    template.name[:30] + "..."
                    if len(template.name) > 30
                    else template.name
                )
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{icon} {name}",
                            callback_data=f"template_view_{template.id}",
                        )
                    ]
                )

            buttons.extend(
                [
                    [
                        InlineKeyboardButton(
                            text="➕ Создать", callback_data="template_create"
                        )
                    ],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="templates")],
                ]
            )

            await callback.message.edit_text(
                f"📄 <b>Список шаблонов</b>\n\n"
                f"📊 Найдено: {len(templates)}\n\n"
                "Выберите шаблон для просмотра:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                parse_mode="HTML",
            )
            await callback.answer()

        except Exception as e:
            await callback.answer(f"❌ Ошибка: {e}", show_alert=True)

    async def view_template(self, callback: types.CallbackQuery):
        """Просмотр шаблона"""
        try:
            template_id = int(callback.data.split("_")[-1])
            template = await self.template_service.get_template(template_id)

            if not template:
                await callback.answer("❌ Шаблон не найден", show_alert=True)
                return

            file_info = ""
            if template.file_id:
                file_type_text = "Фото" if template.file_type == "photo" else "Документ"
                file_info = f"\n📎 <b>Файл:</b> {file_type_text}"

            text_preview = (
                template.text[:200] + "..."
                if len(template.text) > 200
                else template.text
            )

            await callback.message.edit_text(
                f"📄 <b>Шаблон #{template.id}</b>\n\n"
                f"📝 <b>Название:</b> {template.name}\n\n"
                f"📄 <b>Текст:</b>\n{text_preview}{file_info}\n\n"
                f"📅 <b>Создан:</b> {template.created_at.strftime('%d.%m.%Y %H:%M')}",
                reply_markup=ConfirmationHelper.create_template_view_keyboard(
                    template.id
                ),
                parse_mode="HTML",
            )
            await callback.answer()

        except ValueError:
            await callback.answer("❌ Неверный ID шаблона", show_alert=True)
        except Exception as e:
            await callback.answer(f"❌ Ошибка: {e}", show_alert=True)

    async def delete_template(self, callback: types.CallbackQuery):
        """Удалить шаблон"""
        try:
            template_id = int(callback.data.split("_")[-1])
            success = await self.template_service.delete_template(template_id)

            if success:
                await callback.answer("✅ Шаблон удален", show_alert=True)
                await self.show_list(callback)  # Возвращаемся к списку
            else:
                await callback.answer("❌ Ошибка удаления", show_alert=True)

        except ValueError:
            await callback.answer("❌ Неверный ID шаблона", show_alert=True)
        except Exception as e:
            await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
