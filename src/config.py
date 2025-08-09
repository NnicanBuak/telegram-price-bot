"""
Упрощенная конфигурация приложения
Только SQLite, сохраняем совместимость с оригинальным кодом
"""

import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Упрощенный класс конфигурации"""

    def __init__(self):
        # Telegram Bot
        self.bot_token = os.getenv("BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("BOT_TOKEN не установлен в .env файле")

        # Администраторы (ID пользователей Telegram)
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        self.admin_ids = [
            int(id.strip()) for id in admin_ids_str.split(",") if id.strip()
        ]
        if not self.admin_ids:
            raise ValueError("ADMIN_IDS не установлен в .env файле")

        # База данных (только SQLite)
        db_path = os.getenv("DB_PATH", "bot_database.db")
        self.database_url = f"sqlite:///{db_path}"

        # Логирование
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Настройки рассылки
        self.mailing_delay = float(
            os.getenv("MAILING_DELAY", "0.1")
        )  # Задержка между сообщениями
        self.batch_size = int(
            os.getenv("BATCH_SIZE", "30")
        )  # Размер пакета для рассылки

    def __str__(self):
        """Вывод конфигурации (для отладки)"""
        return f"""
        Bot Token: {'*' * 10}{self.bot_token[-5:] if self.bot_token else 'NOT SET'}
        Admin IDs: {self.admin_ids}
        Database: SQLite ({self.database_url.split('///')[-1]})
        Log Level: {self.log_level}
        """
