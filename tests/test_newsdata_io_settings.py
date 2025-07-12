# tests/test_newsdata_io_settings.py

import pytest
from pydantic import ValidationError
from src.config import NewsDataIOSettings


class TestNewsDataIOSettings:
    """Тесты для настроек NewsData.io"""
    
    def test_newsdata_io_settings_creation(self):
        """Тест создания настроек NewsData.io"""
        settings = NewsDataIOSettings(
            api_key="test_key",
            enabled=True,
            priority=3,
            base_url="https://newsdata.test.com/api/1",
            page_size=20
        )
        
        assert settings.api_key == "test_key"
        assert settings.enabled == True
        assert settings.priority == 3
        assert settings.base_url == "https://newsdata.test.com/api/1"
        assert settings.page_size == 20
    
    def test_newsdata_io_settings_defaults(self):
        """Тест дефолтных значений для настроек NewsData.io"""
        settings = NewsDataIOSettings(api_key="test_key")
        
        assert settings.api_key == "test_key"
        assert settings.enabled == True  # наследуется от базового
        assert settings.priority == 1  # наследуется от базового
        assert settings.base_url == "https://newsdata.io/api/1"
        assert settings.page_size == 10
        assert settings.max_retries == 3  # наследуется от базового
        assert settings.backoff_factor == 2.0  # наследуется от базового
        assert settings.timeout == 30  # наследуется от базового
    
    def test_newsdata_io_settings_validation_error(self):
        """Тест ошибки валидации при отсутствии обязательных полей"""
        with pytest.raises(ValidationError):
            NewsDataIOSettings()  # Отсутствует api_key
    
    def test_newsdata_io_settings_inheritance(self):
        """Тест наследования от BaseProviderSettings"""
        settings = NewsDataIOSettings(
            api_key="test_key",
            max_retries=5,
            backoff_factor=1.5,
            timeout=45
        )
        
        # Проверяем что унаследованные поля работают
        assert settings.max_retries == 5
        assert settings.backoff_factor == 1.5
        assert settings.timeout == 45
        
        # Проверяем специфичные для NewsData.io поля
        assert settings.api_key == "test_key"
        assert settings.base_url == "https://newsdata.io/api/1"
        assert settings.page_size == 10 