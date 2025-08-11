import os
import logging
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Полная конфигурация приложения"""

    def __init__(self):
        # === ОСНОВНЫЕ НАСТРОЙКИ ===
        self.bot_token = self._get_required_env("BOT_TOKEN")
        self.admin_ids = self._parse_admin_ids()

        # === НАСТРОЙКИ БАЗЫ ДАННЫХ ===
        self.database_url = self._build_database_url()

        # === НАСТРОЙКИ ФАЙЛОВОЙ СИСТЕМЫ ===
        self.setup_directories()

        # === НАСТРОЙКИ РАССЫЛКИ ===
        self.mailing_delay = float(os.getenv("MAILING_DELAY", "1.0"))
        self.max_file_size = self._parse_file_size(os.getenv("MAX_FILE_SIZE", "20MB"))
        self.max_mailings_per_hour = int(os.getenv("MAX_MAILINGS_PER_HOUR", "10"))

        # === НАСТРОЙКИ ЛОГИРОВАНИЯ ===
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_file = os.getenv("LOG_FILE", "logs/bot.log")
        self.log_max_size = self._parse_file_size(os.getenv("LOG_MAX_SIZE", "10MB"))
        self.log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

        # === НАСТРОЙКИ БЕЗОПАСНОСТИ ===
        self.webhook_secret = os.getenv("WEBHOOK_SECRET")
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))

        # === НАСТРОЙКИ TELEGRAM ===
        self.parse_mode = os.getenv("PARSE_MODE", "HTML")
        self.disable_web_page_preview = (
            os.getenv("DISABLE_WEB_PAGE_PREVIEW", "true").lower() == "true"
        )

        # === НАСТРОЙКИ РАЗВЕРТЫВАНИЯ ===
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.port = int(os.getenv("PORT", "8080"))
        self.host = os.getenv("HOST", "0.0.0.0")

    def _get_required_env(self, key: str) -> str:
        """Получить обязательную переменную окружения"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"❌ Переменная окружения {key} обязательна")
        return value

    def _parse_admin_ids(self) -> List[int]:
        """Парсинг ID администраторов"""
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if not admin_ids_str:
            raise ValueError("❌ ADMIN_IDS обязательна")

        try:
            admin_ids = []
            for id_str in admin_ids_str.split(","):
                id_str = id_str.strip()
                if id_str:
                    admin_ids.append(int(id_str))

            if not admin_ids:
                raise ValueError("❌ Список администраторов не может быть пустым")

            return admin_ids
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("❌ ADMIN_IDS должны быть числами через запятую")
            raise

    def _build_database_url(self) -> str:
        """Построение URL базы данных"""
        # Если задан готовый DATABASE_URL - используем его
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url

        # Иначе строим URL из компонентов
        db_type = os.getenv("DB_TYPE", "sqlite").lower()

        if db_type == "sqlite":
            db_path = os.getenv("DB_PATH", "db/bot.db")
            return f"sqlite+aiosqlite:///{db_path}"

        elif db_type == "postgresql":
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "telegram_price_bot")

            if not db_password:
                raise ValueError("❌ DB_PASSWORD обязателен для PostgreSQL")

            return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        else:
            raise ValueError(f"❌ Неподдерживаемый тип БД: {db_type}")

    def _parse_file_size(self, size_str: str) -> int:
        """Парсинг размера файла (например, '20MB', '1GB')"""
        size_str = size_str.upper().strip()

        if size_str.endswith("KB"):
            return int(float(size_str[:-2]) * 1024)
        elif size_str.endswith("MB"):
            return int(float(size_str[:-2]) * 1024 * 1024)
        elif size_str.endswith("GB"):
            return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
        else:
            # Предполагаем байты
            return int(size_str)

    def setup_directories(self):
        """Создание необходимых директорий"""
        # Основные директории
        self.data_dir = Path(os.getenv("DATA_DIR", "data"))
        self.db_dir = Path(os.getenv("DB_DIR", "db"))
        self.log_dir = Path(os.getenv("LOG_DIR", "logs"))
        self.temp_dir = Path(os.getenv("TEMP_DIR", "temp"))

        # Создаем директории если их нет
        for directory in [self.data_dir, self.db_dir, self.log_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """Настройка системы логирования"""
        from logging.handlers import RotatingFileHandler

        # Настройка форматирования
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Настройка root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level))

        # Очищаем существующие обработчики
        root_logger.handlers.clear()

        # Консольный вывод
        if self.debug or os.getenv("CONSOLE_LOG", "true").lower() == "true":
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            root_logger.addHandler(console_handler)

        # Обработчик для файла с ротацией, только если задан путь к файлу
        if self.log_file and self.log_file.strip():
            try:
                # Создаем папку для логов
                log_path = Path(self.log_file)
                log_dir = log_path.parent
                log_dir.mkdir(parents=True, exist_ok=True)

                file_handler = RotatingFileHandler(
                    filename=str(log_path),
                    maxBytes=self.log_max_size,
                    backupCount=self.log_backup_count,
                    encoding="utf-8",
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(getattr(logging, self.log_level))
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"Ошибка настройки файла логирования: {e}")
                print("Логи будут выводиться только в консоль.")

        # Отключаем избыточное логирование от aiogram
        logging.getLogger("aiogram").setLevel(logging.WARNING)
        logging.getLogger("aiohttp").setLevel(logging.WARNING)

    def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        return user_id in self.admin_ids

    def get_database_info(self) -> dict:
        """Получить информацию о настройках БД"""
        if self.database_url.startswith("sqlite"):
            return {
                "type": "SQLite",
                "path": self.database_url.split("///")[-1],
                "engine": "aiosqlite",
            }
        elif self.database_url.startswith("postgresql"):
            # Парсим URL для отображения
            url_parts = self.database_url.split("://")[1]
            if "@" in url_parts:
                auth, location = url_parts.split("@")
                user = auth.split(":")[0]
                host_db = location.split("/")
                host = host_db[0]
                database = host_db[1] if len(host_db) > 1 else "unknown"
                return {
                    "type": "PostgreSQL",
                    "host": host,
                    "database": database,
                    "user": user,
                    "engine": "asyncpg",
                }

        return {"type": "Unknown", "url": self.database_url}

    def validate_config(self) -> List[str]:
        """Валидация конфигурации, возвращает список ошибок"""
        errors = []

        # Проверка токена бота
        if not self.bot_token.startswith(("bot", "Bot")):
            if ":" not in self.bot_token:
                errors.append("❌ BOT_TOKEN имеет неверный формат")

        # Проверка администраторов
        if not self.admin_ids:
            errors.append("❌ Не указаны администраторы")

        # Проверка размера файлов
        if self.max_file_size > 50 * 1024 * 1024:  # 50MB
            errors.append("⚠️ MAX_FILE_SIZE превышает рекомендуемый лимит Telegram")

        # Проверка уровня логирования
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            errors.append(f"❌ Неверный LOG_LEVEL: {self.log_level}")

        return errors

    def get_config_summary(self) -> str:
        """Получить сводку конфигурации для отображения"""
        db_info = self.get_database_info()

        return f"""📋 **Конфигурация бота**

🤖 **Основные настройки:**
• Администраторы: {len(self.admin_ids)} чел.
• Режим отладки: {'Включен' if self.debug else 'Выключен'}
• Формат сообщений: {self.parse_mode}

💾 **База данных:**
• Тип: {db_info.get('type', 'Unknown')}
• Движок: {db_info.get('engine', 'Unknown')}
• Путь/Хост: {db_info.get('path') or db_info.get('host', 'Unknown')}

📮 **Рассылка:**
• Задержка: {self.mailing_delay}с
• Макс. файл: {self.max_file_size // 1024 // 1024}MB
• Лимит в час: {self.max_mailings_per_hour}

📝 **Логирование:**
• Уровень: {self.log_level}
• Файл: {self.log_file}
• Макс. размер: {self.log_max_size // 1024 // 1024}MB

📁 **Директории:**
• Данные: {self.data_dir}
• БД: {self.db_dir}
• Логи: {self.log_dir}
• Временные: {self.temp_dir}"""


# Глобальный экземпляр конфигурации
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Получить глобальный экземпляр конфигурации"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reload_config() -> Config:
    """Перезагрузить конфигурацию"""
    global _config_instance
    _config_instance = None
    load_dotenv(override=True)  # Перезагружаем .env
    return get_config()


if __name__ == "__main__":
    # Тестирование конфигурации
    try:
        config = Config()

        print("✅ Конфигурация загружена успешно!")
        print("\n" + config.get_config_summary())

        # Проверка валидации
        errors = config.validate_config()
        if errors:
            print(f"\n⚠️ Найдены проблемы конфигурации:")
            for error in errors:
                print(f"  {error}")
        else:
            print("\n✅ Все настройки корректны")

    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
