"""
Создание и настройка бота
"""

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


def create_bot(token: str, parse_mode: str = "HTML") -> Bot:
    """
    Создание экземпляра бота

    Args:
        token: Токен бота
        parse_mode: Режим парсинга сообщений

    Returns:
        Bot: Настроенный экземпляр бота
    """
    # Определяем режим парсинга
    if parse_mode.upper() == "MARKDOWN":
        mode = ParseMode.MARKDOWN_V2
    elif parse_mode.upper() == "HTML":
        mode = ParseMode.HTML
    else:
        mode = ParseMode.HTML  # По умолчанию

    return Bot(token=token, default=DefaultBotProperties(parse_mode=mode))
