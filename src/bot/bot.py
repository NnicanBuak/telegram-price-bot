"""
Создание и настройка бота
Обновленная версия для aiogram 3.7.0+ с использованием DefaultBotProperties
"""

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from typing import Optional


def create_bot(token: str, parse_mode: str = "HTML", **kwargs) -> Bot:
    """
    Создание экземпляра бота с новым API aiogram 3.7.0+

    Args:
        token: Токен бота
        parse_mode: Режим парсинга сообщений (HTML/MARKDOWN/MARKDOWN_V2)
        **kwargs: Дополнительные параметры для DefaultBotProperties

    Returns:
        Bot: Настроенный экземпляр бота
    """
    # Определяем режим парсинга
    if parse_mode.upper() == "MARKDOWN":
        mode = ParseMode.MARKDOWN_V2
    elif parse_mode.upper() == "MARKDOWN_V2":
        mode = ParseMode.MARKDOWN_V2
    elif parse_mode.upper() == "HTML":
        mode = ParseMode.HTML
    else:
        mode = ParseMode.HTML  # По умолчанию

    # Настройки по умолчанию для DefaultBotProperties
    default_properties = {
        "parse_mode": mode,
        "protect_content": kwargs.get("protect_content", False),
        "allow_sending_without_reply": kwargs.get("allow_sending_without_reply", True),
        "disable_web_page_preview": kwargs.get("disable_web_page_preview", False),
    }

    # Обновляем дополнительными параметрами
    default_properties.update(kwargs)

    return Bot(token=token, default=DefaultBotProperties(**default_properties))


def create_test_bot(token: Optional[str] = None) -> Bot:
    """
    Создание тестового бота с минимальными настройками

    Args:
        token: Токен бота (если не указан, используется тестовый)

    Returns:
        Bot: Тестовый экземпляр бота
    """
    test_token = token or "1234567890:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPP-TEST"

    return Bot(
        token=test_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            protect_content=False,
            allow_sending_without_reply=True,
        ),
    )


def validate_bot_token(token: str) -> bool:
    """
    Валидация формата токена бота

    Args:
        token: Токен для проверки

    Returns:
        bool: True если формат корректный
    """
    if not token:
        return False

    # Базовая проверка формата: число:строка
    parts = token.split(":")
    if len(parts) != 2:
        return False

    # Первая часть должна быть числом
    try:
        int(parts[0])
    except ValueError:
        return False

    # Вторая часть должна быть строкой минимум 35 символов
    if len(parts[1]) < 35:
        return False

    return True


async def test_bot_connection(bot: Bot) -> tuple[bool, Optional[str], Optional[dict]]:
    """
    Тестирование подключения к Telegram API

    Args:
        bot: Экземпляр бота

    Returns:
        tuple: (успех, ошибка, информация о боте)
    """
    try:
        bot_info = await bot.get_me()

        return (
            True,
            None,
            {
                "id": bot_info.id,
                "username": bot_info.username,
                "first_name": bot_info.first_name,
                "is_bot": bot_info.is_bot,
                "can_join_groups": bot_info.can_join_groups,
                "can_read_all_group_messages": bot_info.can_read_all_group_messages,
                "supports_inline_queries": bot_info.supports_inline_queries,
            },
        )

    except Exception as e:
        return False, str(e), None


class BotManager:
    """
    Менеджер для управления ботом и его настройками
    """

    def __init__(self, token: str, parse_mode: str = "HTML"):
        self.token = token
        self.parse_mode = parse_mode
        self._bot: Optional[Bot] = None
        self._bot_info: Optional[dict] = None

    @property
    def bot(self) -> Bot:
        """Получить экземпляр бота"""
        if self._bot is None:
            self._bot = create_bot(self.token, self.parse_mode)
        return self._bot

    async def initialize(self) -> bool:
        """
        Инициализация бота с проверкой подключения

        Returns:
            bool: True если инициализация успешна
        """
        # Валидируем токен
        if not validate_bot_token(self.token):
            raise ValueError("Неверный формат токена бота")

        # Тестируем подключение
        success, error, bot_info = await test_bot_connection(self.bot)

        if not success:
            raise ConnectionError(f"Ошибка подключения к Telegram API: {error}")

        self._bot_info = bot_info
        return True

    @property
    def bot_info(self) -> Optional[dict]:
        """Получить информацию о боте"""
        return self._bot_info

    async def close(self):
        """Закрыть сессию бота"""
        if self._bot and self._bot.session:
            await self._bot.session.close()

    def __str__(self) -> str:
        if self._bot_info:
            return f"Bot @{self._bot_info['username']} (ID: {self._bot_info['id']})"
        return f"Bot (токен: {self.token[:10]}...)"


# Для обратной совместимости
def get_bot_instance(token: str, parse_mode: str = "HTML") -> Bot:
    """
    Устаревшая функция - используйте create_bot()
    """
    import warnings

    warnings.warn(
        "get_bot_instance() устарела, используйте create_bot()",
        DeprecationWarning,
        stacklevel=2,
    )
    return create_bot(token, parse_mode)
