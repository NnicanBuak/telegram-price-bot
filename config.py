"""
Конфигурация приложения
"""

import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Класс конфигурации"""

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

        # База данных
        db_type = os.getenv("DB_TYPE", "sqlite").lower()

        if db_type == "postgresql":
            # PostgreSQL
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "telegram_price_bot")

            self.database_url = (
                f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            )
        else:
            # SQLite (по умолчанию для простоты)
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
        Database: {self.database_url.split('://')[0]}
        Log Level: {self.log_level}
        """
