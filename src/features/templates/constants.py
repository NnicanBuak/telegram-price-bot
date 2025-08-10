from enum import Enum


class TemplateConstraints:
    """Ограничения для шаблонов"""

    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 100
    MIN_TEXT_LENGTH = 10
    MAX_TEXT_LENGTH = 4000
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class FileType(Enum):
    """Типы файлов для шаблонов"""

    PHOTO = "photo"
    DOCUMENT = "document"


class TemplateMessages:
    """Сообщения для пользователя"""

    # Успешные операции
    CREATED_SUCCESS = "✅ <b>Шаблон создан!</b>"
    DELETED_SUCCESS = "✅ Шаблон удален"

    # Ошибки валидации
    NAME_TOO_SHORT = f"❌ Название слишком короткое (минимум {TemplateConstraints.MIN_NAME_LENGTH} символов)"
    NAME_TOO_LONG = f"❌ Название слишком длинное (максимум {TemplateConstraints.MAX_NAME_LENGTH} символов)"
    TEXT_TOO_SHORT = f"❌ Текст слишком короткий (минимум {TemplateConstraints.MIN_TEXT_LENGTH} символов)"
    TEXT_TOO_LONG = f"❌ Текст слишком длинный (максимум {TemplateConstraints.MAX_TEXT_LENGTH} символов)"

    # Ошибки операций
    NOT_FOUND = "❌ Шаблон не найден"
    DELETE_ERROR = "❌ Ошибка удаления"
    UNSUPPORTED_FILE = "❌ Неподдерживаемый тип файла"
    FILE_TOO_LARGE = f"❌ Файл слишком большой (максимум {TemplateConstraints.MAX_FILE_SIZE // 1024 // 1024} МБ)"

    # Информационные сообщения
    NO_TEMPLATES = "❌ Шаблоны не найдены\n\nСоздайте первый шаблон для начала работы."

    # Заголовки
    MENU_TITLE = "📄 <b>Управление шаблонами</b>"
    LIST_TITLE = "📄 <b>Список шаблонов</b>"
    CREATE_TITLE = "➕ <b>Создание шаблона</b>"

    # Подсказки
    NAME_HINT = '<i>Например: "Прайс-лист Декабрь" или "Акция недели"</i>'
    TEXT_HINT = "<i>Поддерживается форматирование Telegram</i>"
    ID_HINT = "<i>Для получения ID чата отправьте /id в нужном чате</i>"


class TemplateActions:
    """Callback data для действий с шаблонами"""

    MENU = "templates"
    CREATE = "template_create"
    LIST = "template_list"
    VIEW = "template_view_{}"
    DELETE = "template_delete_{}"
    SKIP_FILE = "template_skip_file"
