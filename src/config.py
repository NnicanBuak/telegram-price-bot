"""
Умная конфигурация приложения
Автоматически использует TEST_ переменные если они указаны
Исправленная версия для прохождения тестов
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
        self.is_testing = self._detect_testing_environment()

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

    def _detect_testing_environment(self) -> bool:
        """Определение тестового окружения"""
        return (
            self.environment == "testing"
            or "pytest" in os.environ.get("_", "")
            or "PYTEST_CURRENT_TEST" in os.environ
            or "pytest" in str(os.environ.get("PYTEST_CURRENT_TEST", ""))
            or any("pytest" in str(val) for val in os.environ.values())
        )

    def _setup_bot_token(self):
        """Настройка токена бота: TEST_BOT_TOKEN если есть, иначе BOT_TOKEN"""
        # В тестах приоритет TEST_ переменным
        if self.is_testing:
            self.bot_token = os.getenv("TEST_BOT_TOKEN") or os.getenv("BOT_TOKEN")
        else:
            # В продакшне приоритет основным переменным
            self.bot_token = os.getenv("BOT_TOKEN") or os.getenv("TEST_BOT_TOKEN")

        if not self.bot_token:
            raise ValueError(
                "BOT_TOKEN или TEST_BOT_TOKEN должен быть установлен в .env файле"
            )

    def _setup_admin_ids(self):
        """Настройка ID администраторов: TEST_ADMIN_IDS если есть, иначе ADMIN_IDS"""
        # В тестах приоритет TEST_ переменным
        if self.is_testing:
            admin_ids_str = os.getenv("TEST_ADMIN_IDS") or os.getenv("ADMIN_IDS", "")
        else:
            # В продакшне приоритет основным переменным
            admin_ids_str = os.getenv("ADMIN_IDS") or os.getenv("TEST_ADMIN_IDS", "")

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
            # В тестах всегда используем in-memory БД
            self.database_url = "sqlite+aiosqlite:///:memory:"
        else:
            # В продакшне используем настройки из переменных
            self.database_url = os.getenv(
                "DATABASE_URL", "sqlite+aiosqlite:///bot_database.db"
            )

        # Альтернативные настройки БД
        self.db_path = os.getenv("DB_PATH", "bot_database.db")
        if self.is_testing and self.db_path != ":memory:":
            self.db_path = ":memory:"

    def _setup_logging(self):
        """Настройка логирования"""
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_format = os.getenv(
            "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # В тестах уменьшаем детализность логов
        if self.is_testing:
            self.log_level = "WARNING"

    def _setup_mailing(self):
        """Настройки рассылки"""
        # Задержка между сообщениями (секунды)
        default_delay = "0.1" if self.is_testing else "1.0"
        self.mailing_delay = float(os.getenv("MAILING_DELAY", default_delay))

        # Размер пачки для рассылки
        default_batch_size = "10" if self.is_testing else "5"
        self.mailing_batch_size = int(
            os.getenv("MAILING_BATCH_SIZE", default_batch_size)
        )

        # Максимальное количество попыток
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))

        # Таймаут для запросов
        default_timeout = "5" if self.is_testing else "30"
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", default_timeout))

    # ========== МЕТОДЫ ДЛЯ ТЕСТОВ ==========

    def get_test_token(self) -> str:
        """Получить тестовый токен (для тестов)"""
        return os.getenv("TEST_BOT_TOKEN", "")

    def get_prod_token(self) -> str:
        """Получить продакшн токен (для тестов)"""
        return os.getenv("BOT_TOKEN", "")

    def force_testing_mode(self):
        """Принудительно включить тестовый режим"""
        self.is_testing = True
        self.environment = "testing"
        self.database_url = "sqlite+aiosqlite:///:memory:"
        self.db_path = ":memory:"
        self.mailing_delay = 0.0  # Убираем задержки в тестах
        self.log_level = "WARNING"

    def force_production_mode(self):
        """Принудительно включить продакшн режим"""
        self.is_testing = False
        self.environment = "production"
        self._setup_database()  # Пересчитываем настройки БД
        self._setup_mailing()  # Пересчитываем настройки рассылки

    # ========== ВАЛИДАЦИЯ КОНФИГУРАЦИИ ==========

    def validate(self) -> List[str]:
        """Валидация конфигурации, возвращает список ошибок"""
        errors = []

        # Проверка токена
        if not self.bot_token:
            errors.append("BOT_TOKEN не установлен")
        elif not self._is_valid_bot_token(self.bot_token):
            errors.append("BOT_TOKEN имеет неверный формат")

        # Проверка админов
        if not self.admin_ids:
            errors.append("ADMIN_IDS не установлен")

        # Проверка БД
        if not self.database_url:
            errors.append("DATABASE_URL не установлен")

        return errors

    def _is_valid_bot_token(self, token: str) -> bool:
        """Проверка формата токена бота"""
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

        # Вторая часть должна быть не пустой
        return len(parts[1]) > 0

    def is_valid(self) -> bool:
        """Проверка валидности конфигурации"""
        return len(self.validate()) == 0

    # ========== ИНФОРМАЦИЯ О КОНФИГУРАЦИИ ==========

    def get_config_info(self) -> dict:
        """Получить информацию о текущей конфигурации"""
        return {
            "environment": self.environment,
            "is_testing": self.is_testing,
            "database_url": self.database_url,
            "admin_count": len(self.admin_ids),
            "mailing_delay": self.mailing_delay,
            "mailing_batch_size": self.mailing_batch_size,
            "log_level": self.log_level,
            "bot_token_set": bool(self.bot_token),
            "bot_token_valid": self._is_valid_bot_token(self.bot_token),
        }

    def __str__(self) -> str:
        """Строковое представление конфигурации"""
        return f"Config(environment={self.environment}, testing={self.is_testing})"

    def __repr__(self) -> str:
        """Детальное представление конфигурации"""
        return (
            f"Config("
            f"environment='{self.environment}', "
            f"is_testing={self.is_testing}, "
            f"admin_count={len(self.admin_ids)}, "
            f"valid={self.is_valid()}"
            f")"
        )
