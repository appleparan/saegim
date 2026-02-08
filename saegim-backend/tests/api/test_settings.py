"""Tests for API settings configuration."""

import os
from pathlib import Path

from saegim.api.settings import Settings, get_settings


class TestSettings:
    """Test cases for API settings."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()

        assert settings.api_host == '0.0.0.0'  # noqa: S104
        assert settings.api_port == 5000
        assert settings.debug is False
        assert settings.log_level == 'INFO'
        assert settings.max_workers == 1
        assert settings.database_url == 'postgresql://labeling:labeling@localhost:5432/labeling'
        assert settings.storage_path == './storage'
        assert 'http://localhost:3000' in settings.cors_origins

    def test_settings_from_env_vars(self, monkeypatch):
        """Test settings loaded from environment variables.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
        """
        monkeypatch.setenv('API_HOST', '127.0.0.1')
        monkeypatch.setenv('API_PORT', '8080')
        monkeypatch.setenv('DEBUG', 'true')
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('MAX_WORKERS', '4')
        monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@db:5432/mydb')
        monkeypatch.setenv('STORAGE_PATH', '/data/storage')

        settings = Settings()

        assert settings.api_host == '127.0.0.1'
        assert settings.api_port == 8080
        assert settings.debug is True
        assert settings.log_level == 'DEBUG'
        assert settings.max_workers == 4
        assert settings.database_url == 'postgresql://user:pass@db:5432/mydb'
        assert settings.storage_path == '/data/storage'

    def test_settings_from_env_file(self, tmp_path):
        """Test settings loaded from .env file.

        Args:
            tmp_path: Pytest temporary directory fixture.
        """
        env_file = tmp_path / '.env'
        env_content = """
API_HOST=192.168.1.100
API_PORT=9000
DEBUG=true
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://test:test@localhost:5432/test
"""
        env_file.write_text(env_content)

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            settings = Settings()

            assert settings.api_host == '192.168.1.100'
            assert settings.api_port == 9000
            assert settings.debug is True
            assert settings.log_level == 'WARNING'
            assert settings.database_url == 'postgresql://test:test@localhost:5432/test'
        finally:
            os.chdir(original_cwd)

    def test_cors_origins_list_parsing(self, monkeypatch):
        """Test CORS origins list parsing from environment.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
        """
        monkeypatch.setenv('CORS_ORIGINS', '["http://example.com"]')
        settings = Settings()
        assert settings.cors_origins == ['http://example.com']

        monkeypatch.setenv('CORS_ORIGINS', '["http://example.com", "https://app.example.com"]')
        settings = Settings()
        assert 'http://example.com' in settings.cors_origins
        assert 'https://app.example.com' in settings.cors_origins

    def test_get_settings_caching(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_validation(self):
        """Test settings field validation."""
        settings = Settings(api_port=8080, max_workers=2, db_pool_min_size=5, db_pool_max_size=20)

        assert settings.api_port == 8080
        assert settings.max_workers == 2
        assert settings.db_pool_min_size == 5
        assert settings.db_pool_max_size == 20

    def test_settings_field_descriptions(self):
        """Test that all fields have proper descriptions."""
        settings = Settings()

        for field_info in settings.model_fields.values():
            assert field_info.description is not None
            assert len(field_info.description) > 0
