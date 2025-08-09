"""
Тесты для модуля config.py
"""

import pytest
import os
from unittest.mock import patch

from config import Config


class TestConfig:
    """Тесты конфигурации"""

    def test_config_loading(self):
        """Тест загрузки конфигурации"""
        config = Config()
        assert config.bot_token == "test:token:for:testing"
        assert 123456789 in config.admin_ids
        assert 987654321 in config.admin_ids
        assert "sqlite" in config.database_url

    def test_config_validation_missing_token(self):
        """Тест валидации при отсутствии токена"""
        with patch.dict(os.environ, {"BOT_TOKEN": ""}):
            with pytest.raises(ValueError, match="BOT_TOKEN"):
                Config()

    def test_config_validation_missing_admins(self):
        """Тест валидации при отсутствии админов"""
        with patch.dict(os.environ, {"ADMIN_IDS": ""}):
            with pytest.raises(ValueError, match="ADMIN_IDS"):
                Config()

    def test_config_validation_invalid_admin_ids(self):
        """Тест валидации неверного формата admin_ids"""
        with patch.dict(os.environ, {"ADMIN_IDS": "not_a_number,123"}):
            with pytest.raises(ValueError):
                Config()

    def test_config_database_url_custom_path(self):
        """Тест кастомного пути к БД"""
        with patch.dict(os.environ, {"DB_PATH": "custom_database.db"}):
            config = Config()
            assert "custom_database.db" in config.database_url

    def test_config_string_representation(self):
        """Тест строкового представления конфигурации"""
        config = Config()
        config_str = str(config)

        # Токен должен быть замаскирован
        assert "testing" in config_str
        assert config.bot_token not in config_str

        # Админы должны быть видны
        assert "123456789" in config_str
        assert "987654321" in config_str

        # БД должна быть указана
        assert "SQLite" in config_str

    def test_config_mailing_settings(self):
        """Тест настроек рассылки"""
        config = Config()

        assert config.mailing_delay == 0.1
        assert config.batch_size == 30

        # Тестируем кастомные значения
        with patch.dict(os.environ, {"MAILING_DELAY": "0.5", "BATCH_SIZE": "50"}):
            custom_config = Config()
            assert custom_config.mailing_delay == 0.5
            assert custom_config.batch_size == 50

    def test_config_log_level(self):
        """Тест настройки уровня логирования"""
        config = Config()
        assert config.log_level == "DEBUG"  # Из conftest.py

        with patch.dict(os.environ, {"LOG_LEVEL": "INFO"}):
            custom_config = Config()
            assert custom_config.log_level == "INFO"
