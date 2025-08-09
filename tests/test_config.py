"""
Тесты для умной конфигурации
"""

import pytest
import os
from unittest.mock import patch

from src.config import Config


class TestSmartConfig:
    """Тесты умной конфигурации"""

    def test_automatic_test_mode_detection(self):
        """Тест автоматического определения тестового режима"""
        config = Config()

        # В тестах должен автоматически определиться тестовый режим
        assert config.is_testing is True
        assert config.environment == "testing"
        print(f"✅ Тестовый режим определен автоматически: {config.get_test_summary()}")

    def test_test_token_usage(self):
        """Тест использования тестового токена"""
        # Устанавливаем тестовый токен
        with patch.dict(
            os.environ,
            {
                "BOT_TOKEN": "prod_token",
                "TEST_BOT_TOKEN": "test_token",
                "ENVIRONMENT": "testing",
            },
        ):
            config = Config()

            # В тестах должен использоваться TEST_BOT_TOKEN
            assert config.bot_token == "test_token"
            assert config.is_testing is True

    def test_production_token_usage(self):
        """Тест использования продакшн токена"""
        with patch.dict(
            os.environ,
            {
                "BOT_TOKEN": "prod_token",
                "TEST_BOT_TOKEN": "test_token",
                "ENVIRONMENT": "production",
            },
        ):
            config = Config()

            # В продакшене должен использоваться BOT_TOKEN
            assert config.bot_token == "prod_token"
            assert config.is_testing is False
            assert config.is_production is True

    def test_fallback_to_main_token(self):
        """Тест fallback на основной токен если нет тестового"""
        with patch.dict(
            os.environ,
            {"BOT_TOKEN": "main_token", "ENVIRONMENT": "testing"},
            clear=False,
        ):
            # Удаляем TEST_BOT_TOKEN если он есть
            if "TEST_BOT_TOKEN" in os.environ:
                del os.environ["TEST_BOT_TOKEN"]

            config = Config()

            # Должен использоваться основной токен
            assert config.bot_token == "main_token"
            assert config.is_testing is True

    def test_test_admin_ids(self):
        """Тест использования тестовых админов"""
        with patch.dict(
            os.environ,
            {
                "ADMIN_IDS": "111,222",
                "TEST_ADMIN_IDS": "333,444",
                "ENVIRONMENT": "testing",
            },
        ):
            config = Config()

            # В тестах должны использоваться TEST_ADMIN_IDS
            assert config.admin_ids == [333, 444]

    def test_test_database_settings(self):
        """Тест настроек БД для тестов"""
        config = Config()

        # В тестах должна использоваться in-memory БД
        assert ":memory:" in config.database_url
        assert config.is_testing is True

    def test_test_mailing_settings(self):
        """Тест настроек рассылки для тестов"""
        config = Config()

        # В тестах рассылка должна быть ускорена
        assert config.mailing_delay == 0.0  # Без задержки
        assert config.batch_size <= 10  # Маленькие пакеты
        assert config.max_retries <= 2  # Меньше попыток

    def test_environment_detection_methods(self):
        """Тест методов определения окружения"""
        # Тестовое окружение
        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}):
            config = Config()
            assert config.is_testing is True
            assert config.is_development is False
            assert config.is_production is False
            assert config.debug_mode is True

        # Продакшн окружение
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "DEBUG": "false"}):
            config = Config()
            assert config.is_testing is False
            assert config.is_development is False
            assert config.is_production is True
            assert config.debug_mode is False

        # Разработка
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            config = Config()
            assert config.is_testing is False
            assert config.is_development is True
            assert config.is_production is False
            assert config.debug_mode is True

    def test_pytest_detection(self):
        """Тест определения pytest окружения"""
        # Pytest обычно устанавливает эти переменные
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_something"}):
            config = Config()
            assert config.is_testing is True

    def test_config_string_representation(self):
        """Тест строкового представления"""
        config = Config()
        config_str = str(config)

        # Токен должен быть замаскирован
        assert "***" in config_str
        assert config.bot_token not in config_str

        # Должна быть информация о том, какие переменные используются
        if config.using_test_token:
            assert "(TEST)" in config_str

        # Админы должны быть видны
        assert str(config.admin_ids) in config_str

    def test_missing_tokens_error(self):
        """Тест ошибки при отсутствии токенов"""
        with patch.dict(os.environ, {}, clear=True):
            # Удаляем все токены
            with pytest.raises(ValueError, match="BOT_TOKEN или TEST_BOT_TOKEN"):
                Config()

    def test_missing_admin_ids_error(self):
        """Тест ошибки при отсутствии admin IDs"""
        with patch.dict(os.environ, {"BOT_TOKEN": "some_token"}, clear=True):
            # Есть токен, но нет админов
            with pytest.raises(ValueError, match="ADMIN_IDS или TEST_ADMIN_IDS"):
                Config()
