import logging
import psutil
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemService:
    """Сервис системного мониторинга и управления"""

    def __init__(self, database, config):
        self.database = database
        self.config = config
        self.start_time = datetime.utcnow()

    async def initialize(self):
        """Инициализация сервиса"""
        logger.info("🔧 Инициализация системного сервиса")

    async def cleanup(self):
        """Очистка ресурсов"""
        logger.info("🧹 Очистка системного сервиса")

    # === СИСТЕМНАЯ ИНФОРМАЦИЯ ===

    def get_system_status(self) -> Dict[str, Any]:
        """
        Получить статус системы

        Returns:
            Dict: Системная информация
        """
        try:
            # Информация о процессе
            process = psutil.Process()

            # Время работы
            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()

            # Использование памяти
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            # Использование CPU
            cpu_percent = process.cpu_percent()

            # Информация о дисках
            disk_usage = {}
            for path_name, path_obj in [
                ("data", self.config.data_dir),
                ("db", self.config.db_dir),
                ("logs", self.config.log_dir),
                ("temp", self.config.temp_dir),
            ]:
                try:
                    usage = psutil.disk_usage(str(path_obj))
                    disk_usage[path_name] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": round((usage.used / usage.total) * 100, 2),
                    }
                except Exception:
                    disk_usage[path_name] = {"error": "Недоступно"}

            return {
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": self._format_uptime(uptime_seconds),
                "memory": {
                    "rss": memory_info.rss,
                    "vms": memory_info.vms,
                    "percent": round(memory_percent, 2),
                    "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                },
                "cpu_percent": round(cpu_percent, 2),
                "disk_usage": disk_usage,
                "start_time": self.start_time,
                "current_time": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Ошибка получения статуса системы: {e}")
            return {"error": str(e)}

    def get_config_info(self) -> Dict[str, Any]:
        """Получить информацию о конфигурации"""
        try:
            return {
                "environment": self.config.environment,
                "debug": self.config.debug,
                "admin_count": len(self.config.admin_ids),
                "database": self.config.get_database_info(),
                "mailing": {
                    "delay": self.config.mailing_delay,
                    "max_file_size_mb": round(
                        self.config.max_file_size / 1024 / 1024, 2
                    ),
                    "max_per_hour": self.config.max_mailings_per_hour,
                },
                "logging": {
                    "level": self.config.log_level,
                    "file": self.config.log_file,
                    "max_size_mb": round(self.config.log_max_size / 1024 / 1024, 2),
                    "backup_count": self.config.log_backup_count,
                },
                "directories": {
                    "data": str(self.config.data_dir),
                    "db": str(self.config.db_dir),
                    "logs": str(self.config.log_dir),
                    "temp": str(self.config.temp_dir),
                },
            }
        except Exception as e:
            logger.error(f"Ошибка получения конфигурации: {e}")
            return {"error": str(e)}

    # === ЛОГИ ===

    def get_recent_logs(self, lines: int = 50) -> List[str]:
        """
        Получить последние строки логов

        Args:
            lines: Количество строк

        Returns:
            List[str]: Строки логов
        """
        try:
            log_path = Path(self.config.log_file)

            if not log_path.exists():
                return ["Файл логов не найден"]

            with open(log_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return [line.strip() for line in all_lines[-lines:]]

        except Exception as e:
            logger.error(f"Ошибка чтения логов: {e}")
            return [f"Ошибка чтения логов: {e}"]

    def get_log_stats(self) -> Dict[str, Any]:
        """Получить статистику логов"""
        try:
            log_path = Path(self.config.log_file)

            if not log_path.exists():
                return {"error": "Файл логов не найден"}

            stat = log_path.stat()

            # Анализируем последние записи
            recent_logs = self.get_recent_logs(1000)

            error_count = len([line for line in recent_logs if " ERROR " in line])
            warning_count = len([line for line in recent_logs if " WARNING " in line])
            info_count = len([line for line in recent_logs if " INFO " in line])

            return {
                "file_size": stat.st_size,
                "file_size_mb": round(stat.st_size / 1024 / 1024, 2),
                "last_modified": datetime.fromtimestamp(stat.st_mtime),
                "total_lines": len(recent_logs),
                "log_levels": {
                    "error": error_count,
                    "warning": warning_count,
                    "info": info_count,
                },
            }

        except Exception as e:
            logger.error(f"Ошибка анализа логов: {e}")
            return {"error": str(e)}

    # === БАЗА ДАННЫХ ===

    async def get_database_stats(self) -> Dict[str, Any]:
        """Получить статистику базы данных"""
        try:
            stats = {}

            # Статистика таблиц
            templates = await self.database.get_templates()
            groups = await self.database.get_chat_groups()
            mailings = await self.database.get_mailings_history(100)

            stats["tables"] = {
                "templates": len(templates),
                "groups": len(groups),
                "mailings": len(mailings),
            }

            # Статистика рассылок
            active_mailings = [
                m for m in mailings if m.status in ["pending", "running"]
            ]
            completed_mailings = [m for m in mailings if m.status == "completed"]
            failed_mailings = [m for m in mailings if m.status == "failed"]

            stats["mailings"] = {
                "active": len(active_mailings),
                "completed": len(completed_mailings),
                "failed": len(failed_mailings),
                "total_messages_sent": sum(m.sent_count for m in mailings),
            }

            # Статистика файлов базы данных (для SQLite)
            if self.config.database_url.startswith("sqlite"):
                db_path = self.config.database_url.split("///")[-1]
                if Path(db_path).exists():
                    db_stat = Path(db_path).stat()
                    stats["file"] = {
                        "size": db_stat.st_size,
                        "size_mb": round(db_stat.st_size / 1024 / 1024, 2),
                        "last_modified": datetime.fromtimestamp(db_stat.st_mtime),
                    }

            return stats

        except Exception as e:
            logger.error(f"Ошибка получения статистики БД: {e}")
            return {"error": str(e)}

    # === ОЧИСТКА И ОБСЛУЖИВАНИЕ ===

    async def cleanup_old_data(self, days: int = 30) -> Dict[str, Any]:
        """
        Очистка старых данных

        Args:
            days: Количество дней для хранения

        Returns:
            Dict: Результат очистки
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Получаем старые рассылки
            all_mailings = await self.database.get_mailings_history(1000)
            old_mailings = [
                m
                for m in all_mailings
                if m.created_at < cutoff_date and m.status in ["completed", "failed"]
            ]

            # В текущей реализации нет метода удаления рассылок
            # Это нужно будет добавить в database.py

            result = {
                "old_mailings_found": len(old_mailings),
                "deleted_mailings": 0,  # Пока что 0, так как нет метода удаления
                "message": f"Найдено {len(old_mailings)} старых рассылок (старше {days} дней)",
            }

            logger.info(f"🧹 Очистка данных: {result}")
            return result

        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")
            return {"error": str(e)}

    def cleanup_temp_files(self) -> Dict[str, Any]:
        """Очистка временных файлов"""
        try:
            temp_dir = self.config.temp_dir
            deleted_count = 0
            total_size = 0

            if temp_dir.exists():
                for file_path in temp_dir.iterdir():
                    if file_path.is_file():
                        try:
                            size = file_path.stat().st_size
                            file_path.unlink()
                            deleted_count += 1
                            total_size += size
                        except Exception as e:
                            logger.warning(f"Не удалось удалить файл {file_path}: {e}")

            result = {
                "deleted_files": deleted_count,
                "freed_space": total_size,
                "freed_space_mb": round(total_size / 1024 / 1024, 2),
            }

            logger.info(f"🧹 Очищено временных файлов: {result}")
            return result

        except Exception as e:
            logger.error(f"Ошибка очистки временных файлов: {e}")
            return {"error": str(e)}

    # === РЕЗЕРВНОЕ КОПИРОВАНИЕ ===

    async def create_backup(self) -> Dict[str, Any]:
        """Создать резервную копию данных"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.config.data_dir / "backups"
            backup_dir.mkdir(exist_ok=True)

            backup_data = {
                "timestamp": timestamp,
                "config_info": self.get_config_info(),
                "system_stats": self.get_system_status(),
            }

            # Экспортируем данные (нужно будет добавить методы экспорта в сервисы)
            # backup_data['templates'] = await template_service.export_templates()
            # backup_data['groups'] = await group_service.export_groups()

            backup_file = backup_dir / f"backup_{timestamp}.json"

            import json

            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)

            result = {
                "backup_file": str(backup_file),
                "file_size": backup_file.stat().st_size,
                "timestamp": timestamp,
            }

            logger.info(f"💾 Создана резервная копия: {result}")
            return result

        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return {"error": str(e)}

    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Получить список резервных копий"""
        try:
            backup_dir = self.config.data_dir / "backups"

            if not backup_dir.exists():
                return []

            backups = []
            for backup_file in backup_dir.glob("backup_*.json"):
                try:
                    stat = backup_file.stat()
                    backups.append(
                        {
                            "filename": backup_file.name,
                            "size": stat.st_size,
                            "size_mb": round(stat.st_size / 1024 / 1024, 2),
                            "created": datetime.fromtimestamp(stat.st_ctime),
                            "path": str(backup_file),
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"Ошибка чтения информации о файле {backup_file}: {e}"
                    )

            # Сортируем по дате создания (новые первыми)
            backups.sort(key=lambda x: x["created"], reverse=True)

            return backups

        except Exception as e:
            logger.error(f"Ошибка получения списка резервных копий: {e}")
            return []

    # === МОНИТОРИНГ ===

    async def get_health_check(self) -> Dict[str, Any]:
        """Проверка здоровья системы"""
        health = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.utcnow(),
        }

        try:
            # Проверка базы данных
            try:
                templates = await self.database.get_templates()
                health["checks"]["database"] = {
                    "status": "ok",
                    "message": f"Доступна, {len(templates)} шаблонов",
                }
            except Exception as e:
                health["checks"]["database"] = {
                    "status": "error",
                    "message": f"Ошибка подключения: {str(e)}",
                }
                health["status"] = "unhealthy"

            # Проверка памяти
            try:
                memory_percent = psutil.Process().memory_percent()
                if memory_percent > 80:
                    health["checks"]["memory"] = {
                        "status": "warning",
                        "message": f"Высокое использование памяти: {memory_percent:.1f}%",
                    }
                    if health["status"] == "healthy":
                        health["status"] = "warning"
                else:
                    health["checks"]["memory"] = {
                        "status": "ok",
                        "message": f"Использование памяти: {memory_percent:.1f}%",
                    }
            except Exception as e:
                health["checks"]["memory"] = {
                    "status": "error",
                    "message": f"Ошибка проверки памяти: {str(e)}",
                }

            # Проверка дискового пространства
            try:
                for path_name, path_obj in [
                    ("data", self.config.data_dir),
                    ("logs", self.config.log_dir),
                ]:
                    usage = psutil.disk_usage(str(path_obj))
                    percent_used = (usage.used / usage.total) * 100

                    if percent_used > 90:
                        health["checks"][f"disk_{path_name}"] = {
                            "status": "error",
                            "message": f"Критически мало места: {percent_used:.1f}%",
                        }
                        health["status"] = "unhealthy"
                    elif percent_used > 80:
                        health["checks"][f"disk_{path_name}"] = {
                            "status": "warning",
                            "message": f"Мало места: {percent_used:.1f}%",
                        }
                        if health["status"] == "healthy":
                            health["status"] = "warning"
                    else:
                        health["checks"][f"disk_{path_name}"] = {
                            "status": "ok",
                            "message": f"Свободно места: {percent_used:.1f}%",
                        }
            except Exception as e:
                health["checks"]["disk"] = {
                    "status": "error",
                    "message": f"Ошибка проверки диска: {str(e)}",
                }

            # Проверка логов
            try:
                log_stats = self.get_log_stats()
                if "error" not in log_stats:
                    error_count = log_stats.get("log_levels", {}).get("error", 0)
                    if error_count > 10:  # Много ошибок в последних 1000 записях
                        health["checks"]["logs"] = {
                            "status": "warning",
                            "message": f"Много ошибок в логах: {error_count}",
                        }
                        if health["status"] == "healthy":
                            health["status"] = "warning"
                    else:
                        health["checks"]["logs"] = {
                            "status": "ok",
                            "message": f"Ошибок в логах: {error_count}",
                        }
                else:
                    health["checks"]["logs"] = {
                        "status": "error",
                        "message": "Не удалось проверить логи",
                    }
            except Exception as e:
                health["checks"]["logs"] = {
                    "status": "error",
                    "message": f"Ошибка проверки логов: {str(e)}",
                }

        except Exception as e:
            logger.error(f"Ошибка проверки здоровья системы: {e}")
            health["status"] = "error"
            health["error"] = str(e)

        return health

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def _format_uptime(self, seconds: float) -> str:
        """Форматировать время работы"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"
