import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Упрощенная конфигурация"""

    def __init__(self):
        self.bot_token = self._get_required_env("BOT_TOKEN")
        self.admin_ids = self._parse_admin_ids()
        self.database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")

        # Настройки рассылки
        self.mailing_delay = float(os.getenv("MAILING_DELAY", "1.0"))
        self.max_file_size = 20 * 1024 * 1024  # 20MB

    def _get_required_env(self, key: str) -> str:
        """Получить обязательную переменную окружения"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Переменная окружения {key} обязательна")
        return value

    def _parse_admin_ids(self) -> List[int]:
        """Парсинг ID администраторов"""
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if not admin_ids_str:
            raise ValueError("ADMIN_IDS обязательна")

        try:
            return [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        except ValueError:
            raise ValueError("ADMIN_IDS должно содержать числа через запятую")

    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in self.admin_ids
