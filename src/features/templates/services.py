from typing import List, Optional
from datetime import datetime

from database import Database, Template
from .models import (
    TemplateData,  # Используем оригинальное имя для совместимости
    UpdateTemplateData,
    TemplateResponse,
    TemplateCreateRequest,
    ValidationError,  # Оригинальное исключение
    TemplateValidationError,
)
from .constants import TemplateConstraints


class TemplateService:
    """Сервис для работы с шаблонами"""

    # Константы для совместимости с оригинальным API
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 100
    MIN_TEXT_LENGTH = 10
    MAX_TEXT_LENGTH = 4000

    def __init__(self, database: Database):
        self.db = database

    async def create_template(self, data: TemplateData) -> Template:
        """Создать новый шаблон с валидацией (совместимость с оригиналом)"""
        # Валидация как в оригинале
        self._validate_template_data(data)

        # Создание в БД
        template = await self.db.create_template(
            name=data.name,
            text=data.text,
            file_id=data.file_id,
            file_type=data.file_type,
        )

        return template

    async def create_template_with_response(
        self, data: TemplateData
    ) -> TemplateResponse:
        """Создать шаблон и вернуть DTO ответа"""
        template = await self.create_template(data)
        return self._template_to_response(template)

    async def get_templates(self) -> List[Template]:
        """Получить все шаблоны (оригинальный API)"""
        return await self.db.get_templates()

    async def get_templates_as_response(self) -> List[TemplateResponse]:
        """Получить все шаблоны как DTO"""
        templates = await self.db.get_templates()
        return [self._template_to_response(t) for t in templates]

    async def get_template(self, template_id: int) -> Optional[Template]:
        """Получить шаблон по ID (оригинальный API)"""
        return await self.db.get_template(template_id)

    async def get_template_as_response(
        self, template_id: int
    ) -> Optional[TemplateResponse]:
        """Получить шаблон как DTO"""
        template = await self.db.get_template(template_id)
        if not template:
            return None
        return self._template_to_response(template)

    async def update_template(
        self, template_id: int, data: UpdateTemplateData
    ) -> Optional[TemplateResponse]:
        """Обновить шаблон"""
        # Проверяем существование
        existing = await self.db.get_template(template_id)
        if not existing:
            return None

        # Валидация изменений
        if data.name is not None:
            self._validate_name(data.name)
        if data.text is not None:
            self._validate_text(data.text)

        # Обновление в БД
        success = await self.db.update_template(
            template_id=template_id,
            name=data.name,
            text=data.text,
            file_id=data.file_id,
            file_type=data.file_type,
        )

        if not success:
            return None

        # Возвращаем обновленный
        updated = await self.db.get_template(template_id)
        return self._template_to_response(updated)

    async def delete_template(self, template_id: int) -> bool:
        """Удалить шаблон (оригинальный API)"""
        return await self.db.delete_template(template_id)

    async def get_templates_count(self) -> int:
        """Получить количество шаблонов"""
        templates = await self.db.get_templates()
        return len(templates)

    async def search_templates(self, query: str) -> List[TemplateResponse]:
        """Поиск шаблонов по названию"""
        templates = await self.db.get_templates()
        query_lower = query.lower()

        filtered = [
            t
            for t in templates
            if query_lower in t.name.lower() or query_lower in t.text.lower()
        ]

        return [self._template_to_response(t) for t in filtered]

    def _validate_template_data(self, data: TemplateData):
        """Валидация данных шаблона (как в оригинале)"""
        if not data.name or len(data.name) < self.MIN_NAME_LENGTH:
            raise ValidationError(
                f"Название должно быть не менее {self.MIN_NAME_LENGTH} символов"
            )

        if len(data.name) > self.MAX_NAME_LENGTH:
            raise ValidationError(
                f"Название должно быть не более {self.MAX_NAME_LENGTH} символов"
            )

        if not data.text or len(data.text) < self.MIN_TEXT_LENGTH:
            raise ValidationError(
                f"Текст должен быть не менее {self.MIN_TEXT_LENGTH} символов"
            )

        if len(data.text) > self.MAX_TEXT_LENGTH:
            raise ValidationError(
                f"Текст должен быть не более {self.MAX_TEXT_LENGTH} символов"
            )

    def _template_to_response(self, template: Template) -> TemplateResponse:
        """Преобразование модели БД в DTO"""
        return TemplateResponse(
            id=template.id,
            name=template.name,
            text=template.text,
            file_id=template.file_id,
            file_type=template.file_type,
            created_at=template.created_at.strftime("%d.%m.%Y %H:%M"),
        )

    def _validate_name(self, name: str):
        """Валидация названия"""
        if not name or len(name.strip()) < self.MIN_NAME_LENGTH:
            raise ValidationError(
                f"Название должно быть не менее {self.MIN_NAME_LENGTH} символов"
            )

        if len(name) > self.MAX_NAME_LENGTH:
            raise ValidationError(
                f"Название должно быть не более {self.MAX_NAME_LENGTH} символов"
            )

    def _validate_text(self, text: str):
        """Валидация текста"""
        if not text or len(text.strip()) < self.MIN_TEXT_LENGTH:
            raise ValidationError(
                f"Текст должен быть не менее {self.MIN_TEXT_LENGTH} символов"
            )

        if len(text) > self.MAX_TEXT_LENGTH:
            raise ValidationError(
                f"Текст должен быть не более {self.MAX_TEXT_LENGTH} символов"
            )


class TemplateValidator:
    """Дополнительные валидаторы для шаблонов"""

    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Проверка размера файла"""
        return file_size <= TemplateConstraints.MAX_FILE_SIZE

    @staticmethod
    def validate_file_type(file_type: str) -> bool:
        """Проверка типа файла"""
        from .constants import FileType

        return file_type in [ft.value for ft in FileType]

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Очистка и подготовка текста"""
        # Удаляем лишние пробелы
        cleaned = " ".join(text.split())

        # Ограничиваем длину
        if len(cleaned) > TemplateConstraints.MAX_TEXT_LENGTH:
            cleaned = cleaned[: TemplateConstraints.MAX_TEXT_LENGTH - 3] + "..."

        return cleaned

    @staticmethod
    def extract_preview(text: str, max_length: int = 100) -> str:
        """Извлечение превью текста"""
        if len(text) <= max_length:
            return text

        # Обрезаем по словам
        words = text[:max_length].split()
        if len(words) > 1:
            words = words[:-1]  # Удаляем последнее неполное слово

        preview = " ".join(words)
        return preview + "..." if preview else text[:max_length] + "..."
