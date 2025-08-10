from typing import Optional
from dataclasses import dataclass
from pydantic import BaseModel, validator


class ValidationError(Exception):
    """Ошибка валидации (для обратной совместимости)"""

    pass


class TemplateValidationError(ValidationError):
    """Ошибка валидации шаблона"""

    pass


@dataclass
class TemplateData:
    """DTO для создания шаблона (совместимость с оригиналом)"""

    name: str
    text: str
    file_id: Optional[str] = None
    file_type: Optional[str] = None


# Алиас для нового API
CreateTemplateData = TemplateData


@dataclass
class UpdateTemplateData:
    """DTO для обновления шаблона"""

    name: Optional[str] = None
    text: Optional[str] = None
    file_id: Optional[str] = None
    file_type: Optional[str] = None


class TemplateCreateRequest(BaseModel):
    """Pydantic модель для валидации создания шаблона"""

    name: str
    text: str
    file_id: Optional[str] = None
    file_type: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError("Название должно быть не менее 3 символов")
        if len(v) > 100:
            raise ValueError("Название должно быть не более 100 символов")
        return v.strip()

    @validator("text")
    def validate_text(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Текст должен быть не менее 10 символов")
        if len(v) > 4000:
            raise ValueError("Текст должен быть не более 4000 символов")
        return v.strip()

    @validator("file_type")
    def validate_file_type(cls, v, values):
        if v and "file_id" not in values:
            raise ValueError("Если указан тип файла, должен быть указан file_id")
        if v and v not in ["photo", "document"]:
            raise ValueError("Тип файла должен быть photo или document")
        return v


class TemplateResponse(BaseModel):
    """Модель ответа с данными шаблона"""

    id: int
    name: str
    text: str
    file_id: Optional[str] = None
    file_type: Optional[str] = None
    has_file: bool = False
    created_at: str

    def __init__(self, **data):
        # Вычисляем has_file на основе file_id
        data["has_file"] = bool(data.get("file_id"))
        super().__init__(**data)
