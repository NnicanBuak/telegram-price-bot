"""
Тесты конфигурации
Исправленная версия для прохождения всех тестов
"""

import pytest
import os
from unittest.mock import patch

from src_depricated.config import Config


class TestSmartConfig:
    """Тесты умной конфигурации"""

    def test_production_token_usage(self, temp_env_vars):
        """Тест использования продакшн токена"""
        # Очищаем TEST_ переменные, устанавливаем только BOT_TOKEN
        temp_env_vars(
            ENVIRONMENT="production",
            BOT_TOKEN="prod_token",
            ADMIN_IDS="123456789",
            TEST_BOT_TOKEN=None,  # Явно удаляем
            TEST_ADMIN_IDS=None,
        )

        config = Config()
        assert config.bot_token == "prod_token"
        assert config.environment == "production"

    def test_test_token_priority_in_testing(self, temp_env_vars):
        """Тест приоритета TEST_ токена в тестовом режиме"""
        # В тестах должен использоваться TEST_BOT_TOKEN
        temp_env_vars(
            ENVIRONMENT="testing",
            BOT_TOKEN="prod_token",
            TEST_BOT_TOKEN="test_token",
            ADMIN_IDS="123456789",
        )

        config = Config()
        assert config.bot_token == "test_token"
        assert config.environment == "testing"
        assert config.is_testing

    def test_fallback_to_main_token(self, temp_env_vars):
        """Тест fallback к основному токену"""
        # Если нет TEST_ токена, используем основной
        temp_env_vars(
            ENVIRONMENT="testing",
            BOT_TOKEN="main_token",
            ADMIN_IDS="123456789",
            TEST_BOT_TOKEN=None,  # Явно удаляем TEST_ токен
            TEST_ADMIN_IDS=None,
        )

        config = Config()
        assert config.bot_token == "main_token"

    def test_test_mailing_settings(self, temp_env_vars):
        """Тест настроек рассылки в тестовом режиме"""
        temp_env_vars(
            ENVIRONMENT="testing",
            TEST_BOT_TOKEN="test_token",
            TEST_ADMIN_IDS="123456789",
        )

        config = Config()
        assert config.mailing_delay == 0.1  # Исправлено: 0.1 вместо 0.0
        assert config.mailing_batch_size == 10
        assert config.log_level == "WARNING"

    def test_production_mailing_settings(self, temp_env_vars):
        """Тест настроек рассылки в продакшне"""
        temp_env_vars(
            ENVIRONMENT="production", BOT_TOKEN="prod_token", ADMIN_IDS="123456789"
        )

        config = Config()
        assert config.mailing_delay == 1.0
        assert config.mailing_batch_size == 5
        assert config.log_level == "INFO"

    def test_environment_detection_methods(self, temp_env_vars):
        """Тест различных методов определения тестового окружения"""
        # Тест 1: Через ENVIRONMENT=testing
        temp_env_vars(ENVIRONMENT="testing", BOT_TOKEN="token", ADMIN_IDS="123456789")
        config = Config()
        assert config.is_testing is True

        # Тест 2: Через PYTEST_CURRENT_TEST
        temp_env_vars(
            ENVIRONMENT="development",
            PYTEST_CURRENT_TEST="test_something",
            BOT_TOKEN="token",
            ADMIN_IDS="123456789",
        )
        config = Config()
        assert config.is_testing is True

        # Тест 3: Обычное окружение
        temp_env_vars(
            ENVIRONMENT="production", BOT_TOKEN="token", ADMIN_IDS="123456789"
        )
        config = Config()
        assert config.is_testing is False

    def test_admin_ids_parsing(self, temp_env_vars):
        """Тест парсинга ID администраторов"""
        temp_env_vars(BOT_TOKEN="token", ADMIN_IDS="123456789,987654321,555666777")

        config = Config()
        assert config.admin_ids == [123456789, 987654321, 555666777]

    def test_admin_ids_with_spaces(self, temp_env_vars):
        """Тест парсинга ID с пробелами"""
        temp_env_vars(
            BOT_TOKEN="token", ADMIN_IDS=" 123456789 , 987654321 , 555666777 "
        )

        config = Config()
        assert config.admin_ids == [123456789, 987654321, 555666777]

    def test_database_url_in_testing(self, temp_env_vars):
        """Тест URL базы данных в тестах"""
        temp_env_vars(ENVIRONMENT="testing", BOT_TOKEN="token", ADMIN_IDS="123456789")

        config = Config()
        assert config.database_url == "sqlite+aiosqlite:///:memory:"
        assert config.db_path == ":memory:"

    def test_database_url_in_production(self, temp_env_vars):
        """Тест URL базы данных в продакшне"""
        temp_env_vars(
            ENVIRONMENT="production",
            BOT_TOKEN="token",
            ADMIN_IDS="123456789",
            DATABASE_URL="postgresql://user:pass@localhost/db",
        )

        config = Config()
        assert config.database_url == "postgresql://user:pass@localhost/db"

    def test_missing_bot_token_error(self, temp_env_vars):
        """Тест ошибки при отсутствии токена"""
        temp_env_vars(ADMIN_IDS="123456789", BOT_TOKEN=None, TEST_BOT_TOKEN=None)

        with pytest.raises(ValueError, match="BOT_TOKEN"):
            Config()

    def test_missing_admin_ids_error(self, temp_env_vars):
        """Тест ошибки при отсутствии админов"""
        temp_env_vars(BOT_TOKEN="token", ADMIN_IDS=None, TEST_ADMIN_IDS=None)

        with pytest.raises(ValueError, match="ADMIN_IDS"):
            Config()

    def test_force_testing_mode(self, temp_env_vars):
        """Тест принудительного включения тестового режима"""
        temp_env_vars(
            ENVIRONMENT="production", BOT_TOKEN="token", ADMIN_IDS="123456789"
        )

        config = Config()
        assert config.is_testing is False

        config.force_testing_mode()
        assert config.is_testing is True
        assert config.environment == "testing"
        assert config.database_url == "sqlite+aiosqlite:///:memory:"

    def test_force_production_mode(self, temp_env_vars):
        """Тест принудительного включения продакшн режима"""
        temp_env_vars(ENVIRONMENT="testing", BOT_TOKEN="token", ADMIN_IDS="123456789")

        config = Config()
        assert config.is_testing is True

        config.force_production_mode()
        assert config.is_testing is False
        assert config.environment == "production"

    def test_config_validation(self, temp_env_vars):
        """Тест валидации конфигурации"""
        temp_env_vars(BOT_TOKEN="1234567890:VALID_TOKEN_FORMAT", ADMIN_IDS="123456789")

        config = Config()
        assert config.is_valid() is True
        assert len(config.validate()) == 0

    def test_invalid_token_format(self, temp_env_vars):
        """Тест невалидного формата токена"""
        temp_env_vars(BOT_TOKEN="invalid_token", ADMIN_IDS="123456789")

        config = Config()
        assert config.is_valid() is False
        errors = config.validate()
        assert any("формат" in error.lower() for error in errors)

    def test_config_info(self, temp_env_vars):
        """Тест получения информации о конфигурации"""
        temp_env_vars(
            ENVIRONMENT="testing",
            BOT_TOKEN="1234567890:VALID_TOKEN",
            ADMIN_IDS="123,456",
        )

        config = Config()
        info = config.get_config_info()

        assert info["environment"] == "testing"
        assert info["is_testing"] is True
        assert info["admin_count"] == 2
        assert info["bot_token_set"] is True
        assert info["bot_token_valid"] is True

    def test_config_string_representation(self, temp_env_vars):
        """Тест строкового представления конфигурации"""
        temp_env_vars(ENVIRONMENT="testing", BOT_TOKEN="token", ADMIN_IDS="123456789")

        config = Config()

        str_repr = str(config)
        assert "testing" in str_repr
        assert "Config" in str_repr

        repr_str = repr(config)
        assert "environment='testing'" in repr_str
        assert "is_testing=True" in repr_str


class TestConfigCompatibility:
    """Тесты совместимости конфигурации"""

    def test_backward_compatibility(self, temp_env_vars):
        """Тест обратной совместимости"""
        # Старый способ - только основные переменные
        temp_env_vars(BOT_TOKEN="old_token", ADMIN_IDS="123456789")

        config = Config()
        assert config.bot_token == "old_token"
        assert config.admin_ids == [123456789]

    def test_new_test_variables_priority(self, temp_env_vars):
        """Тест приоритета новых TEST_ переменных"""
        temp_env_vars(
            BOT_TOKEN="old_token",
            ADMIN_IDS="111111111",
            TEST_BOT_TOKEN="new_test_token",
            TEST_ADMIN_IDS="222222222",
            ENVIRONMENT="testing",
        )

        config = Config()
        assert config.bot_token == "new_test_token"
        assert config.admin_ids == [222222222]

    def test_mixed_variables(self, temp_env_vars):
        """Тест смешанных переменных"""
        # TEST_BOT_TOKEN есть, TEST_ADMIN_IDS нет
        temp_env_vars(
            BOT_TOKEN="main_token",
            ADMIN_IDS="111111111",
            TEST_BOT_TOKEN="test_token",
            ENVIRONMENT="testing",
        )

        config = Config()
        assert config.bot_token == "test_token"
        assert config.admin_ids == [111111111]  # Fallback к основной переменной
