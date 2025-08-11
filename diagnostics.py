#!/usr/bin/env python3
"""
Скрипт диагностики системы Telegram Price Bot
Проверяет конфигурацию, зависимости, права доступа и подключения
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from config import Config
    from database import Database
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что вы запускаете скрипт из корня проекта")
    sys.exit(1)


class SystemChecker:
    """Проверка системы"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def log_error(self, message: str):
        """Добавить ошибку"""
        self.errors.append(message)
        print(f"❌ {message}")

    def log_warning(self, message: str):
        """Добавить предупреждение"""
        self.warnings.append(message)
        print(f"⚠️ {message}")

    def log_info(self, message: str):
        """Добавить информацию"""
        self.info.append(message)
        print(f"ℹ️ {message}")

    def log_success(self, message: str):
        """Добавить успешную проверку"""
        print(f"✅ {message}")

    def check_python_version(self):
        """Проверка версии Python"""
        print("\n🐍 Проверка Python:")

        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            self.log_success(f"Python {version.major}.{version.minor}.{version.micro}")
        elif version.major == 3:
            self.log_warning(
                f"Python {version.major}.{version.minor}.{version.micro} (рекомендуется 3.8+)"
            )
        else:
            self.log_error(
                f"Python {version.major}.{version.minor}.{version.micro} (требуется 3.8+)"
            )

    def check_dependencies(self):
        """Проверка зависимостей"""
        print("\n📦 Проверка зависимостей:")

        required_packages = {
            "aiogram": "3.4.0",
            "sqlalchemy": "2.0.0",
            "aiosqlite": "0.19.0",
            "python-dotenv": "1.0.0",
            "psutil": "5.9.0",
        }

        for package, min_version in required_packages.items():
            try:
                __import__(package)
                # Пытаемся получить версию
                try:
                    module = __import__(package)
                    version = getattr(module, "__version__", "unknown")
                    self.log_success(f"{package} {version}")
                except:
                    self.log_success(f"{package} (версия неизвестна)")
            except ImportError:
                self.log_error(f"{package} не установлен")

    def check_env_file(self):
        """Проверка .env файла"""
        print("\n📝 Проверка .env файла:")

        env_path = Path(".env")
        if not env_path.exists():
            self.log_error(".env файл не найден")
            return

        self.log_success(".env файл существует")

        # Проверяем права доступа
        stat = env_path.stat()
        if oct(stat.st_mode)[-3:] != "600":
            self.log_warning(
                f"Права доступа к .env: {oct(stat.st_mode)[-3:]} (рекомендуется 600)"
            )

        # Проверяем размер
        if stat.st_size == 0:
            self.log_error(".env файл пустой")
        else:
            self.log_info(f"Размер .env файла: {stat.st_size} байт")

    def check_config(self):
        """Проверка конфигурации"""
        print("\n⚙️ Проверка конфигурации:")

        try:
            config = Config()
            self.log_success("Конфигурация загружена")

            # Валидация
            errors = config.validate_config()
            if errors:
                for error in errors:
                    self.log_error(error)
            else:
                self.log_success("Конфигурация валидна")

            # Информация о конфигурации
            self.log_info(f"Администраторов: {len(config.admin_ids)}")
            self.log_info(f"База данных: {config.get_database_info()['type']}")
            self.log_info(f"Режим отладки: {config.debug}")

        except Exception as e:
            self.log_error(f"Ошибка загрузки конфигурации: {e}")

    def check_directories(self):
        """Проверка директорий"""
        print("\n📁 Проверка директорий:")

        try:
            config = Config()

            directories = {
                "data": config.data_dir,
                "db": config.db_dir,
                "logs": config.log_dir,
                "temp": config.temp_dir,
            }

            for name, path in directories.items():
                if path.exists():
                    if path.is_dir():
                        # Проверяем права записи
                        if os.access(path, os.W_OK):
                            self.log_success(f"Директория {name}/ доступна для записи")
                        else:
                            self.log_error(f"Директория {name}/ недоступна для записи")
                    else:
                        self.log_error(f"{name}/ существует, но это не директория")
                else:
                    self.log_warning(f"Директория {name}/ не существует")

        except Exception as e:
            self.log_error(f"Ошибка проверки директорий: {e}")

    async def check_database(self):
        """Проверка базы данных"""
        print("\n💾 Проверка базы данных:")

        try:
            config = Config()
            database = Database(config.database_url)

            # Попытка подключения
            await database.init()
            self.log_success("Подключение к базе данных")

            # Проверяем таблицы
            async with database.session() as session:
                result = await session.execute("SELECT 1")
                self.log_success("Выполнение SQL запросов")

            # Проверяем статистику
            try:
                templates = await database.get_templates()
                groups = await database.get_chat_groups()
                mailings = await database.get_mailings_history(limit=10)

                self.log_info(f"Шаблонов в БД: {len(templates)}")
                self.log_info(f"Групп в БД: {len(groups)}")
                self.log_info(f"Рассылок в БД: {len(mailings)}")

            except Exception as e:
                self.log_warning(f"Ошибка получения статистики: {e}")

            await database.close()

        except Exception as e:
            self.log_error(f"Ошибка базы данных: {e}")

    async def check_bot_token(self):
        """Проверка токена бота"""
        print("\n🤖 Проверка токена бота:")

        try:
            from aiogram import Bot

            config = Config()

            bot = Bot(token=config.bot_token)

            # Получаем информацию о боте
            bot_info = await bot.get_me()
            self.log_success(f"Бот @{bot_info.username} ({bot_info.first_name})")
            self.log_info(f"ID бота: {bot_info.id}")

            if bot_info.can_join_groups:
                self.log_success("Бот может быть добавлен в группы")
            else:
                self.log_warning("Бот не может быть добавлен в группы")

            await bot.session.close()

        except Exception as e:
            self.log_error(f"Ошибка проверки токена: {e}")

    def check_system_resources(self):
        """Проверка системных ресурсов"""
        print("\n💻 Проверка системных ресурсов:")

        try:
            import psutil

            # Память
            memory = psutil.virtual_memory()
            if memory.percent < 80:
                self.log_success(f"Память: {memory.percent:.1f}% используется")
            else:
                self.log_warning(
                    f"Память: {memory.percent:.1f}% используется (высокая нагрузка)"
                )

            # Диск
            disk = psutil.disk_usage(".")
            if disk.percent < 90:
                self.log_success(f"Диск: {disk.percent:.1f}% используется")
            else:
                self.log_warning(f"Диск: {disk.percent:.1f}% используется (мало места)")

            # CPU
            cpu = psutil.cpu_percent(interval=1)
            if cpu < 80:
                self.log_success(f"CPU: {cpu:.1f}% загрузка")
            else:
                self.log_warning(f"CPU: {cpu:.1f}% загрузка (высокая нагрузка)")

        except ImportError:
            self.log_warning("psutil не установлен, пропуск проверки ресурсов")
        except Exception as e:
            self.log_error(f"Ошибка проверки ресурсов: {e}")

    def check_log_files(self):
        """Проверка файлов логов"""
        print("\n📝 Проверка логов:")

        try:
            config = Config()
            log_file = Path(config.log_file)

            if log_file.exists():
                stat = log_file.stat()
                size_mb = stat.st_size / 1024 / 1024

                self.log_success(f"Файл логов существует ({size_mb:.1f} MB)")

                if size_mb > 100:
                    self.log_warning("Файл логов очень большой, рекомендуется ротация")

                # Проверяем последние строки
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            self.log_info(f"Последняя запись: {last_line[:100]}...")
                        else:
                            self.log_warning("Файл логов пустой")
                except:
                    self.log_warning("Не удалось прочитать файл логов")

            else:
                self.log_warning("Файл логов не существует")

        except Exception as e:
            self.log_error(f"Ошибка проверки логов: {e}")

    def generate_report(self):
        """Генерация отчета"""
        print("\n" + "=" * 50)
        print("📊 ОТЧЕТ О ДИАГНОСТИКЕ")
        print("=" * 50)

        if not self.errors and not self.warnings:
            print("🎉 Все проверки пройдены успешно!")
            print("Система готова к работе.")
        else:
            if self.errors:
                print(f"\n❌ Критические ошибки ({len(self.errors)}):")
                for error in self.errors:
                    print(f"  • {error}")

            if self.warnings:
                print(f"\n⚠️ Предупреждения ({len(self.warnings)}):")
                for warning in self.warnings:
                    print(f"  • {warning}")

            print(f"\nℹ️ Информация ({len(self.info)}):")
            for info in self.info:
                print(f"  • {info}")

        print("\n" + "=" * 50)

        # Рекомендации
        if self.errors:
            print("\n🔧 РЕКОМЕНДАЦИИ:")
            if any("BOT_TOKEN" in error for error in self.errors):
                print("  • Проверьте токен бота в .env файле")
            if any(
                "БД" in error or "database" in error.lower() for error in self.errors
            ):
                print("  • Проверьте настройки базы данных")
            if any("не установлен" in error for error in self.errors):
                print("  • Обновите зависимости: poetry update")
            print("  • Запустите setup.sh для автоматической настройки")

    async def run_all_checks(self):
        """Запуск всех проверок"""
        print("🔍 Диагностика системы Telegram Price Bot")
        print("=" * 50)

        self.check_python_version()
        self.check_dependencies()
        self.check_env_file()
        self.check_config()
        self.check_directories()
        self.check_log_files()
        self.check_system_resources()

        await self.check_database()
        await self.check_bot_token()

        self.generate_report()


async def main():
    """Главная функция"""
    checker = SystemChecker()

    try:
        await checker.run_all_checks()
    except KeyboardInterrupt:
        print("\n⚡ Диагностика прервана пользователем")
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        return 1

    # Возвращаем код ошибки если есть критические проблемы
    return 1 if checker.errors else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
