# tests/test_config.py

import pytest
import os
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from src.config import (
    get_settings, get_news_settings, get_ai_settings, get_google_settings,
    get_log_level, is_debug_mode,
    Settings, NewsSettings, AISettings, GoogleSettings
)


class TestSettings:
    """Тесты для основного класса настроек"""
    
    def test_settings_creation_with_required_fields(self):
        """Тест создания настроек с обязательными полями"""
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'test_news_token',
            'OPENAI_API_KEY': 'test_openai_key',
            'GOOGLE_GSHEET_ID': 'test_sheet_id',
            'GOOGLE_ACCOUNT_EMAIL': 'test@example.com',
            'GOOGLE_ACCOUNT_KEY': 'test_google_key'
        }):
            settings = Settings()
            
            assert settings.THENEWSAPI_API_TOKEN == 'test_news_token'
            assert settings.OPENAI_API_KEY == 'test_openai_key'
            assert settings.GOOGLE_GSHEET_ID == 'test_sheet_id'
            assert settings.GOOGLE_ACCOUNT_EMAIL == 'test@example.com'
            assert settings.GOOGLE_ACCOUNT_KEY == 'test_google_key'
    
    def test_settings_defaults(self):
        """Тест дефолтных значений"""
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'test_token',
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_GSHEET_ID': 'test_id',
            'GOOGLE_ACCOUNT_EMAIL': 'test@example.com',
            'GOOGLE_ACCOUNT_KEY': 'test_key'
        }):
            settings = Settings()
            
            assert settings.NEWS_API_PROVIDER == "thenewsapi"
            assert settings.MAX_RETRIES == 3
            assert settings.BACKOFF_FACTOR == 0.5
            assert settings.OPENAI_MODEL == "gpt-4o-mini"
            assert settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-small"
            assert settings.MAX_TOKENS == 1000
            assert settings.TEMPERATURE == 0.7
            assert settings.LOG_LEVEL == "INFO"
            assert settings.DEBUG == False


class TestNewsSettings:
    """Тесты для настроек новостей"""
    
    def test_news_settings_creation(self):
        """Тест создания настроек новостей"""
        news_settings = NewsSettings(
            NEWS_API_PROVIDER="thenewsapi",
            THENEWSAPI_API_TOKEN="test_token",
            MAX_RETRIES=5,
            BACKOFF_FACTOR=1.0
        )
        
        assert news_settings.NEWS_API_PROVIDER == "thenewsapi"
        assert news_settings.THENEWSAPI_API_TOKEN == "test_token"
        assert news_settings.MAX_RETRIES == 5
        assert news_settings.BACKOFF_FACTOR == 1.0
    
    def test_news_settings_defaults(self):
        """Тест дефолтных значений для настроек новостей"""
        news_settings = NewsSettings(THENEWSAPI_API_TOKEN="test_token")
        
        assert news_settings.NEWS_API_PROVIDER == "thenewsapi"
        assert news_settings.MAX_RETRIES == 3
        assert news_settings.BACKOFF_FACTOR == 0.5
    
    def test_news_settings_validation_error(self):
        """Тест ошибки валидации при отсутствии обязательных полей"""
        with pytest.raises(ValidationError):
            NewsSettings()  # Отсутствует THENEWSAPI_API_TOKEN


class TestAISettings:
    """Тесты для настроек AI"""
    
    def test_ai_settings_creation(self):
        """Тест создания настроек AI"""
        ai_settings = AISettings(
            OPENAI_API_KEY="test_key",
            OPENAI_MODEL="gpt-4",
            OPENAI_EMBEDDING_MODEL="text-embedding-ada-002",
            MAX_TOKENS=2000,
            TEMPERATURE=0.5
        )
        
        assert ai_settings.OPENAI_API_KEY == "test_key"
        assert ai_settings.OPENAI_MODEL == "gpt-4"
        assert ai_settings.OPENAI_EMBEDDING_MODEL == "text-embedding-ada-002"
        assert ai_settings.MAX_TOKENS == 2000
        assert ai_settings.TEMPERATURE == 0.5
    
    def test_ai_settings_defaults(self):
        """Тест дефолтных значений для настроек AI"""
        ai_settings = AISettings(OPENAI_API_KEY="test_key")
        
        assert ai_settings.OPENAI_MODEL == "gpt-4o-mini"
        assert ai_settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-small"
        assert ai_settings.MAX_TOKENS == 1000
        assert ai_settings.TEMPERATURE == 0.7
    
    def test_ai_settings_validation_error(self):
        """Тест ошибки валидации при отсутствии обязательных полей"""
        with pytest.raises(ValidationError):
            AISettings()  # Отсутствует OPENAI_API_KEY


class TestGoogleSettings:
    """Тесты для настроек Google"""
    
    def test_google_settings_creation(self):
        """Тест создания настроек Google"""
        google_settings = GoogleSettings(
            GOOGLE_GSHEET_ID="test_sheet_id",
            GOOGLE_ACCOUNT_EMAIL="test@example.com",
            GOOGLE_ACCOUNT_KEY="test_key"
        )
        
        assert google_settings.GOOGLE_GSHEET_ID == "test_sheet_id"
        assert google_settings.GOOGLE_ACCOUNT_EMAIL == "test@example.com"
        assert google_settings.GOOGLE_ACCOUNT_KEY == "test_key"
    
    def test_google_settings_validation_error(self):
        """Тест ошибки валидации при отсутствии обязательных полей"""
        with pytest.raises(ValidationError):
            GoogleSettings()  # Отсутствуют все обязательные поля


class TestSettingsGetters:
    """Тесты для функций получения настроек"""
    
    @patch('src.config.get_settings')
    def test_get_news_settings_from_main_settings(self, mock_get_settings):
        """Тест получения настроек новостей из основных настроек"""
        mock_settings = MagicMock()
        mock_settings.NEWS_API_PROVIDER = "thenewsapi"
        mock_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_settings.MAX_RETRIES = 5
        mock_settings.BACKOFF_FACTOR = 1.0
        mock_get_settings.return_value = mock_settings
        
        news_settings = get_news_settings()
        
        assert news_settings.NEWS_API_PROVIDER == "thenewsapi"
        assert news_settings.THENEWSAPI_API_TOKEN == "test_token"
        assert news_settings.MAX_RETRIES == 5
        assert news_settings.BACKOFF_FACTOR == 1.0
    
    @patch('src.config.get_settings')
    def test_get_news_settings_fallback_to_env(self, mock_get_settings):
        """Тест fallback к переменным окружения при ошибке основных настроек"""
        mock_get_settings.side_effect = Exception("Settings error")
        
        # Очищаем кэш перед тестом
        get_news_settings.cache_clear()
        
        with patch.dict(os.environ, {
            'NEWS_API_PROVIDER': 'newsapi',
            'THENEWSAPI_API_TOKEN': 'env_token',
            'MAX_RETRIES': '7',
            'BACKOFF_FACTOR': '2.5'
        }, clear=True):
            news_settings = get_news_settings()
            
            assert news_settings.NEWS_API_PROVIDER == "newsapi"
            assert news_settings.THENEWSAPI_API_TOKEN == "env_token"
            assert news_settings.MAX_RETRIES == 7
            assert news_settings.BACKOFF_FACTOR == 2.5
    
    @patch('src.config.get_settings')
    def test_get_ai_settings_from_main_settings(self, mock_get_settings):
        """Тест получения настроек AI из основных настроек"""
        mock_settings = MagicMock()
        mock_settings.OPENAI_API_KEY = "test_key"
        mock_settings.OPENAI_MODEL = "gpt-4"
        mock_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
        mock_settings.MAX_TOKENS = 2000
        mock_settings.TEMPERATURE = 0.5
        mock_get_settings.return_value = mock_settings
        
        ai_settings = get_ai_settings()
        
        assert ai_settings.OPENAI_API_KEY == "test_key"
        assert ai_settings.OPENAI_MODEL == "gpt-4"
        assert ai_settings.OPENAI_EMBEDDING_MODEL == "text-embedding-ada-002"
        assert ai_settings.MAX_TOKENS == 2000
        assert ai_settings.TEMPERATURE == 0.5
    
    @patch('src.config.get_settings')
    def test_get_ai_settings_fallback_to_env(self, mock_get_settings):
        """Тест fallback к переменным окружения при ошибке основных настроек"""
        mock_get_settings.side_effect = Exception("Settings error")
        
        # Очищаем кэш перед тестом
        get_ai_settings.cache_clear()
        
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'env_key',
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'OPENAI_EMBEDDING_MODEL': 'text-embedding-ada-002',
            'MAX_TOKENS': '1500',
            'TEMPERATURE': '0.8'
        }, clear=True):
            ai_settings = get_ai_settings()
            
            assert ai_settings.OPENAI_API_KEY == "env_key"
            assert ai_settings.OPENAI_MODEL == "gpt-3.5-turbo"
            assert ai_settings.OPENAI_EMBEDDING_MODEL == "text-embedding-ada-002"
            assert ai_settings.MAX_TOKENS == 1500
            assert ai_settings.TEMPERATURE == 0.8
    
    @patch('src.config.get_settings')
    def test_get_google_settings_from_main_settings(self, mock_get_settings):
        """Тест получения настроек Google из основных настроек"""
        mock_settings = MagicMock()
        mock_settings.GOOGLE_GSHEET_ID = "test_sheet_id"
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        mock_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_get_settings.return_value = mock_settings
        
        google_settings = get_google_settings()
        
        assert google_settings.GOOGLE_GSHEET_ID == "test_sheet_id"
        assert google_settings.GOOGLE_ACCOUNT_EMAIL == "test@example.com"
        assert google_settings.GOOGLE_ACCOUNT_KEY == "test_key"
    
    @patch('src.config.get_settings')
    def test_get_google_settings_fallback_to_env(self, mock_get_settings):
        """Тест fallback к переменным окружения при ошибке основных настроек"""
        mock_get_settings.side_effect = Exception("Settings error")
        
        # Очищаем кэш перед тестом
        get_google_settings.cache_clear()
        
        with patch.dict(os.environ, {
            'GOOGLE_GSHEET_ID': 'env_sheet_id',
            'GOOGLE_ACCOUNT_EMAIL': 'env@example.com',
            'GOOGLE_ACCOUNT_KEY': 'env_key'
        }, clear=True):
            google_settings = get_google_settings()
            
            assert google_settings.GOOGLE_GSHEET_ID == "env_sheet_id"
            assert google_settings.GOOGLE_ACCOUNT_EMAIL == "env@example.com"
            assert google_settings.GOOGLE_ACCOUNT_KEY == "env_key"
    
    def test_get_log_level(self):
        """Тест получения уровня логирования"""
        with patch.dict(os.environ, {'LOG_LEVEL': 'DEBUG'}):
            assert get_log_level() == "DEBUG"
        
        with patch.dict(os.environ, {}, clear=True):
            assert get_log_level() == "INFO"  # дефолт
    
    def test_is_debug_mode(self):
        """Тест проверки режима отладки"""
        with patch.dict(os.environ, {'DEBUG': 'true'}):
            assert is_debug_mode() == True
        
        with patch.dict(os.environ, {'DEBUG': '1'}):
            assert is_debug_mode() == True
        
        with patch.dict(os.environ, {'DEBUG': 'yes'}):
            assert is_debug_mode() == True
        
        with patch.dict(os.environ, {'DEBUG': 'false'}):
            assert is_debug_mode() == False
        
        with patch.dict(os.environ, {}, clear=True):
            assert is_debug_mode() == False  # дефолт


class TestGetSettings:
    """Тесты для функции get_settings."""
    
    def test_get_settings_caching(self):
        """Тест кэширования настроек."""
        # Очищаем кэш для чистого теста
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'test_token',
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_GSHEET_ID': 'test_id',
            'GOOGLE_ACCOUNT_EMAIL': 'test@email.com',
            'GOOGLE_ACCOUNT_KEY': 'test_key'
        }):
            # Первый вызов
            result1 = get_settings()
            # Второй вызов
            result2 = get_settings()
            
            # Должны вернуться одинаковые объекты из-за кэширования
            assert result1 is result2 