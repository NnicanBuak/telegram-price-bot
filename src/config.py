"""
Умная конфигурация приложения
Автоматически использует TEST_ переменные если они указаны
"""

import os
from typing import List
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Умный класс конфигурации с поддержкой тестовых переменных"""

    def __init__(self):
        # Определяем окружение
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.is_testing = (
            self.environment == "testing"
            or "pytest" in os.environ.get("_", "")
            or "PYTEST_CURRENT_TEST" in os.environ
        )

        # Настройка токена бота
        self._setup_bot_token()

        # Администраторы
        self._setup_admin_ids()

        # База данных
        self._setup_database()

        # Логирование
        self._setup_logging()

        # Настройки рассылки
        self._setup_mailing()

    def _setup_bot_token(self):
        """Настройка токена бота: TEST_BOT_TOKEN если есть, иначе BOT_TOKEN"""
        self.bot_token = os.getenv("TEST_BOT_TOKEN") or os.getenv("BOT_TOKEN")

        if not self.bot_token:
            raise ValueError(
                "BOT_TOKEN или TEST_BOT_TOKEN должен быть установлен в .env файле"
            )

    def _setup_admin_ids(self):
        """Настройка ID администраторов: TEST_ADMIN_IDS если есть, иначе ADMIN_IDS"""
        admin_ids_str = os.getenv("TEST_ADMIN_IDS") or os.getenv("ADMIN_IDS", "")

        self.admin_ids = [
            int(id.strip()) for id in admin_ids_str.split(",") if id.strip()
        ]

        if not self.admin_ids:
            raise ValueError(
                "ADMIN_IDS или TEST_ADMIN_IDS должен быть установлен в .env файле"
            )

    def _setup_database(self):
        """Настройка базы данных"""
        if self.is_testing:
            # В тестах всегда используем in-memory базу
            db_path = ":memory:"
        else:
            db_path = os.getenv("DB_PATH", "bot_database.db")

        self.database_url = f"sqlite+aiosqlite:///{db_path}"
        self.db_echo = os.getenv("DB_ECHO", "false").lower() == "true"

    def _setup_logging(self):
        """Настройка логирования"""
        if self.is_testing:
            # В тестах используем DEBUG если не указано иное
            self.log_level = os.getenv("LOG_LEVEL", "DEBUG")
        else:
            self.log_level = os.getenv("LOG_LEVEL", "INFO")

        self.log_file = os.getenv("LOG_FILE", "")
        self.log_max_bytes = int(os.getenv("LOG_MAX_BYTES", "10485760"))
        self.log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    def _setup_mailing(self):
        """Настройка рассылки"""
        if self.is_testing:
            # В тестах ускоряем рассылку
            self.mailing_delay = float(os.getenv("MAILING_DELAY", "0.0"))
            self.batch_size = int(os.getenv("MAILING_BATCH_SIZE", "5"))
            self.max_retries = int(os.getenv("MAILING_MAX_RETRIES", "1"))
            self.retry_delay = float(os.getenv("MAILING_RETRY_DELAY", "0.1"))
        else:
            # В продакшене используем безопасные значения
            self.mailing_delay = float(os.getenv("MAILING_DELAY", "0.1"))
            self.batch_size = int(os.getenv("MAILING_BATCH_SIZE", "30"))
            self.max_retries = int(os.getenv("MAILING_MAX_RETRIES", "3"))
            self.retry_delay = float(os.getenv("MAILING_RETRY_DELAY", "1.0"))

        # Общие настройки
        self.parse_mode = os.getenv("PARSE_MODE", "HTML")
        self.http_timeout = int(os.getenv("HTTP_TIMEOUT", "30"))

    @property
    def is_development(self) -> bool:
        """Проверка режима разработки"""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Проверка продакшн режима"""
        return self.environment == "production"

    @property
    def debug_mode(self) -> bool:
        """Режим отладки"""
        return (
            os.getenv("DEBUG", "false").lower() == "true"
            or self.is_testing
            or self.is_development
        )

    @property
    def using_test_token(self) -> bool:
        """Проверка использования тестового токена"""
        return bool(os.getenv("TEST_BOT_TOKEN"))

    @property
    def using_test_admins(self) -> bool:
        """Проверка использования тестовых админов"""
        return bool(os.getenv("TEST_ADMIN_IDS"))

    def __str__(self):
        """Безопасное строковое представление конфигурации"""
        masked_token = (
            f"{'*' * 10}{self.bot_token[-5:]}" if self.bot_token else "NOT SET"
        )

        return f"""
Telegram Price Bot Configuration:
  Environment: {self.environment}
  Testing Mode: {self.is_testing}
  Debug Mode: {self.debug_mode}
  
  Bot Token: {masked_token} {'(TEST)' if self.using_test_token else '(PROD)'}
  Admin IDs: {self.admin_ids} {'(TEST)' if self.using_test_admins else '(PROD)'}
  
  Database: {self.database_url.replace('sqlite+aiosqlite:///', 'SQLite: ')}
  
  Log Level: {self.log_level}
  Mailing Delay: {self.mailing_delay}s
  Batch Size: {self.batch_size}
        """.strip()

    def get_test_summary(self) -> str:
        """Краткая информация для тестов"""
        test_indicators = []
        if self.using_test_token:
            test_indicators.append("TEST_TOKEN")
        if self.using_test_admins:
            test_indicators.append("TEST_ADMINS")

        test_info = f" ({', '.join(test_indicators)})" if test_indicators else ""
        return f"Environment: {self.environment}, Testing: {self.is_testing}{test_info}"
