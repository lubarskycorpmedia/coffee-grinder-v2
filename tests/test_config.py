# tests/test_config.py

import pytest
import os
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from src.config import (
    get_settings, get_news_providers_settings, get_ai_settings, get_google_settings,
    get_log_level, is_debug_mode,
    Settings, BaseProviderSettings, TheNewsAPISettings, NewsAPISettings, 
    NewsProvidersSettings, AISettings, GoogleSettings
)


class TestSettings:
    """Тесты для основного класса настроек"""
    
    def test_settings_creation_with_required_fields(self):
        """Тест создания настроек с обязательными полями"""
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'test_news_token',
            'NEWSAPI_API_KEY': 'test_newsapi_key',
            'OPENAI_API_KEY': 'test_openai_key',
            'GOOGLE_SHEET_ID': 'test_sheet_id',
            'GOOGLE_SERVICE_ACCOUNT_PATH': '/test/path',
            'GOOGLE_ACCOUNT_EMAIL': 'test@example.com',
            'GOOGLE_ACCOUNT_KEY': 'test_google_key'
        }):
            settings = Settings()

            assert settings.THENEWSAPI_API_TOKEN == 'test_news_token'
            assert settings.NEWSAPI_API_KEY == 'test_newsapi_key'
            assert settings.OPENAI_API_KEY == 'test_openai_key'
            assert settings.GOOGLE_SHEET_ID == 'test_sheet_id'
            assert settings.GOOGLE_SERVICE_ACCOUNT_PATH == '/test/path'
            assert settings.GOOGLE_ACCOUNT_EMAIL == 'test@example.com'
            assert settings.GOOGLE_ACCOUNT_KEY == 'test_google_key'
    
    def test_settings_defaults(self):
        """Тест дефолтных значений"""
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'test_token',
            'NEWSAPI_API_KEY': 'test_newsapi_key',
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_SHEET_ID': 'test_id',
            'GOOGLE_SERVICE_ACCOUNT_PATH': '/test/path',
            'GOOGLE_ACCOUNT_EMAIL': 'test@example.com',
            'GOOGLE_ACCOUNT_KEY': 'test_key'
        }):
            settings = Settings()
            
            # Settings класс содержит только секретные поля
            assert settings.THENEWSAPI_API_TOKEN == "test_token"
            assert settings.NEWSAPI_API_KEY == "test_newsapi_key"
            assert settings.OPENAI_API_KEY == "test_key"
            assert settings.GOOGLE_SHEET_ID == "test_id"
            assert settings.GOOGLE_SERVICE_ACCOUNT_PATH == "/test/path"
            assert settings.GOOGLE_ACCOUNT_EMAIL == "test@example.com"
            assert settings.GOOGLE_ACCOUNT_KEY == "test_key"


class TestBaseProviderSettings:
    """Тесты для базовых настроек провайдеров"""
    
    def test_base_provider_settings_creation(self):
        """Тест создания базовых настроек провайдера"""
        settings = BaseProviderSettings(
            enabled=True,
            priority=1,
            max_retries=5,
            backoff_factor=1.5,
            timeout=45
        )
        
        assert settings.enabled == True
        assert settings.priority == 1
        assert settings.max_retries == 5
        assert settings.backoff_factor == 1.5
        assert settings.timeout == 45
    
    def test_base_provider_settings_defaults(self):
        """Тест дефолтных значений для базовых настроек провайдера"""
        settings = BaseProviderSettings()
        
        assert settings.enabled == True
        assert settings.priority == 1
        assert settings.max_retries == 3
        assert settings.backoff_factor == 2.0
        assert settings.timeout == 30


class TestTheNewsAPISettings:
    """Тесты для настроек TheNewsAPI"""
    
    def test_thenewsapi_settings_creation(self):
        """Тест создания настроек TheNewsAPI"""
        settings = TheNewsAPISettings(
            api_token="test_token",
            enabled=True,
            priority=1,
            max_retries=5,
            backoff_factor=1.5,
            base_url="https://api.test.com/v1",
            supported_languages=["en", "ru"],
            supported_categories=["tech", "sports"],
            default_locale="ru",
            headlines_per_category=10
        )
        
        assert settings.api_token == "test_token"
        assert settings.enabled == True
        assert settings.priority == 1
        assert settings.max_retries == 5
        assert settings.backoff_factor == 1.5
        assert settings.base_url == "https://api.test.com/v1"
        assert settings.supported_languages == ["en", "ru"]
        assert settings.supported_categories == ["tech", "sports"]
        assert settings.default_locale == "ru"
        assert settings.headlines_per_category == 10
    
    def test_thenewsapi_settings_defaults(self):
        """Тест дефолтных значений для настроек TheNewsAPI"""
        settings = TheNewsAPISettings(api_token="test_token")
        
        assert settings.api_token == "test_token"
        assert settings.enabled == True  # наследуется от базового
        assert settings.priority == 1  # наследуется от базового
        assert settings.max_retries == 3  # наследуется от базового
        assert settings.backoff_factor == 2.0  # наследуется от базового
        assert settings.base_url == "https://api.thenewsapi.com/v1"
        assert "en" in settings.supported_languages
        assert "general" in settings.supported_categories
        assert settings.default_locale == "us"
        assert settings.headlines_per_category == 6
    
    def test_thenewsapi_settings_validation_error(self):
        """Тест ошибки валидации при отсутствии обязательных полей"""
        with pytest.raises(ValidationError):
            TheNewsAPISettings()  # Отсутствует api_token


class TestNewsAPISettings:
    """Тесты для настроек NewsAPI"""
    
    def test_newsapi_settings_creation(self):
        """Тест создания настроек NewsAPI"""
        settings = NewsAPISettings(
            api_key="test_key",
            enabled=True,
            priority=2,
            base_url="https://newsapi.test.com/v2",
            supported_languages=["en", "fr"],
            supported_categories=["business", "health"],
            default_country="fr",
            page_size=50
        )
        
        assert settings.api_key == "test_key"
        assert settings.enabled == True
        assert settings.priority == 2
        assert settings.base_url == "https://newsapi.test.com/v2"
        assert settings.supported_languages == ["en", "fr"]
        assert settings.supported_categories == ["business", "health"]
        assert settings.default_country == "fr"
        assert settings.page_size == 50
    
    def test_newsapi_settings_defaults(self):
        """Тест дефолтных значений для настроек NewsAPI"""
        settings = NewsAPISettings(api_key="test_key")
        
        assert settings.api_key == "test_key"
        assert settings.enabled == True  # наследуется от базового
        assert settings.priority == 1  # наследуется от базового
        assert settings.base_url == "https://newsapi.org/v2"
        assert "en" in settings.supported_languages
        assert "business" in settings.supported_categories
        assert settings.default_country == "us"
        assert settings.page_size == 100
    
    def test_newsapi_settings_validation_error(self):
        """Тест ошибки валидации при отсутствии обязательных полей"""
        with pytest.raises(ValidationError):
            NewsAPISettings()  # Отсутствует api_key


class TestNewsProvidersSettings:
    """Тесты для настроек всех провайдеров новостей"""
    
    def test_news_providers_settings_creation(self):
        """Тест создания настроек провайдеров"""
        thenewsapi_settings = TheNewsAPISettings(api_token="test_token")
        newsapi_settings = NewsAPISettings(api_key="test_key")
        
        providers = {
            "thenewsapi": thenewsapi_settings,
            "newsapi": newsapi_settings
        }
        
        settings = NewsProvidersSettings(
            providers=providers,
            default_provider="thenewsapi",
            fallback_providers=["newsapi"]
        )
        
        assert len(settings.providers) == 2
        assert "thenewsapi" in settings.providers
        assert "newsapi" in settings.providers
        assert settings.default_provider == "thenewsapi"
        assert settings.fallback_providers == ["newsapi"]
    
    def test_news_providers_settings_defaults(self):
        """Тест дефолтных значений для настроек провайдеров"""
        settings = NewsProvidersSettings()
        
        assert settings.providers == {}
        assert settings.default_provider == "thenewsapi"
        assert settings.fallback_providers == []
    
    def test_get_provider_settings(self):
        """Тест получения настроек конкретного провайдера"""
        thenewsapi_settings = TheNewsAPISettings(api_token="test_token")
        providers = {"thenewsapi": thenewsapi_settings}
        settings = NewsProvidersSettings(providers=providers)
        
        provider_settings = settings.get_provider_settings("thenewsapi")
        assert provider_settings == thenewsapi_settings
        
        missing_provider = settings.get_provider_settings("missing")
        assert missing_provider is None
    
    def test_get_enabled_providers(self):
        """Тест получения только включенных провайдеров"""
        thenewsapi_settings = TheNewsAPISettings(api_token="test_token", enabled=True)
        newsapi_settings = NewsAPISettings(api_key="test_key", enabled=False)
        
        providers = {
            "thenewsapi": thenewsapi_settings,
            "newsapi": newsapi_settings
        }
        settings = NewsProvidersSettings(providers=providers)
        
        enabled = settings.get_enabled_providers()
        assert len(enabled) == 1
        assert "thenewsapi" in enabled
        assert "newsapi" not in enabled
    
    def test_get_providers_by_priority(self):
        """Тест получения провайдеров отсортированных по приоритету"""
        thenewsapi_settings = TheNewsAPISettings(api_token="test_token", priority=2)
        newsapi_settings = NewsAPISettings(api_key="test_key", priority=1)
        
        providers = {
            "thenewsapi": thenewsapi_settings,
            "newsapi": newsapi_settings
        }
        settings = NewsProvidersSettings(providers=providers)
        
        sorted_providers = settings.get_providers_by_priority()
        assert len(sorted_providers) == 2
        assert sorted_providers[0][0] == "newsapi"  # priority 1
        assert sorted_providers[1][0] == "thenewsapi"  # priority 2


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
            GOOGLE_SHEET_ID="test_sheet_id",
            GOOGLE_SERVICE_ACCOUNT_PATH="/test/path",
            GOOGLE_ACCOUNT_EMAIL="test@example.com",
            GOOGLE_ACCOUNT_KEY="test_key"
        )
        
        assert google_settings.GOOGLE_SHEET_ID == "test_sheet_id"
        assert google_settings.GOOGLE_SERVICE_ACCOUNT_PATH == "/test/path"
        assert google_settings.GOOGLE_ACCOUNT_EMAIL == "test@example.com"
        assert google_settings.GOOGLE_ACCOUNT_KEY == "test_key"
    
    def test_google_settings_validation_error(self):
        """Тест ошибки валидации при отсутствии обязательных полей"""
        with pytest.raises(ValidationError):
            GoogleSettings()  # Отсутствуют все обязательные поля


class TestSettingsGetters:
    """Тесты для функций получения настроек"""
    
    @patch('src.config.get_settings')
    def test_get_news_providers_settings_from_main_settings(self, mock_get_settings):
        """Тест получения настроек провайдеров из основных настроек"""
        mock_settings = MagicMock()
        mock_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_settings.NEWSAPI_API_KEY = "test_key"
        mock_get_settings.return_value = mock_settings
        
        providers_settings = get_news_providers_settings()
        
        assert providers_settings.default_provider == "thenewsapi"
        assert providers_settings.fallback_providers == ["newsapi"]
        assert len(providers_settings.providers) == 2
        assert "thenewsapi" in providers_settings.providers
        assert "newsapi" in providers_settings.providers
        
        thenewsapi_settings = providers_settings.get_provider_settings("thenewsapi")
        assert isinstance(thenewsapi_settings, TheNewsAPISettings)
        assert thenewsapi_settings.api_token == "test_token"
        
        newsapi_settings = providers_settings.get_provider_settings("newsapi")
        assert isinstance(newsapi_settings, NewsAPISettings)
        assert newsapi_settings.api_key == "test_key"
    
    @patch('src.config.get_settings')
    def test_get_news_providers_settings_fallback_to_env(self, mock_get_settings):
        """Тест fallback к переменным окружения при ошибке основных настроек"""
        mock_get_settings.side_effect = Exception("Settings error")
        
        # Очищаем кэш перед тестом
        get_news_providers_settings.cache_clear()
        
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'env_token',
            'NEWSAPI_API_KEY': 'env_key'
        }, clear=True):
            providers_settings = get_news_providers_settings()
            
            assert len(providers_settings.providers) == 2
            assert "thenewsapi" in providers_settings.providers
            assert "newsapi" in providers_settings.providers
            
            thenewsapi_settings = providers_settings.get_provider_settings("thenewsapi")
            assert thenewsapi_settings.api_token == "env_token"
            
            newsapi_settings = providers_settings.get_provider_settings("newsapi")
            assert newsapi_settings.api_key == "env_key"
    
    @patch('src.config.get_settings')
    def test_get_ai_settings_from_main_settings(self, mock_get_settings):
        """Тест получения настроек AI из основных настроек"""
        mock_settings = MagicMock()
        mock_settings.OPENAI_API_KEY = "test_key"
        mock_get_settings.return_value = mock_settings
        
        ai_settings = get_ai_settings()
        
        assert ai_settings.OPENAI_API_KEY == "test_key"
        assert ai_settings.OPENAI_MODEL == "gpt-4o-mini"  # дефолт
        assert ai_settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-small"  # дефолт
        assert ai_settings.MAX_TOKENS == 1000  # дефолт
        assert ai_settings.TEMPERATURE == 0.7  # дефолт
    
    @patch('src.config.get_settings')
    def test_get_ai_settings_fallback_to_env(self, mock_get_settings):
        """Тест fallback к переменным окружения при ошибке основных настроек"""
        mock_get_settings.side_effect = Exception("Settings error")
        
        # Очищаем кэш перед тестом
        get_ai_settings.cache_clear()
        
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'env_key',
        }, clear=True):
            ai_settings = get_ai_settings()
            
            assert ai_settings.OPENAI_API_KEY == "env_key"
            assert ai_settings.OPENAI_MODEL == "gpt-4o-mini"  # дефолт
            assert ai_settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-small"  # дефолт
            assert ai_settings.MAX_TOKENS == 1000  # дефолт
            assert ai_settings.TEMPERATURE == 0.7  # дефолт
    
    @patch('src.config.get_settings')
    def test_get_google_settings_from_main_settings(self, mock_get_settings):
        """Тест получения настроек Google из основных настроек"""
        mock_settings = MagicMock()
        mock_settings.GOOGLE_SHEET_ID = "test_sheet_id"
        mock_settings.GOOGLE_SERVICE_ACCOUNT_PATH = "/test/path"
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        mock_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_get_settings.return_value = mock_settings
        
        google_settings = get_google_settings()
        
        assert google_settings.GOOGLE_SHEET_ID == "test_sheet_id"
        assert google_settings.GOOGLE_SERVICE_ACCOUNT_PATH == "/test/path"
        assert google_settings.GOOGLE_ACCOUNT_EMAIL == "test@example.com"
        assert google_settings.GOOGLE_ACCOUNT_KEY == "test_key"
    
    @patch('src.config.get_settings')
    def test_get_google_settings_fallback_to_env(self, mock_get_settings):
        """Тест fallback к переменным окружения при ошибке основных настроек"""
        mock_get_settings.side_effect = Exception("Settings error")
        
        # Очищаем кэш перед тестом
        get_google_settings.cache_clear()
        
        with patch.dict(os.environ, {
            'GOOGLE_SHEET_ID': 'env_sheet_id',
            'GOOGLE_SERVICE_ACCOUNT_PATH': '/env/path',
            'GOOGLE_ACCOUNT_EMAIL': 'env@example.com',
            'GOOGLE_ACCOUNT_KEY': 'env_key'
        }, clear=True):
            google_settings = get_google_settings()
            
            assert google_settings.GOOGLE_SHEET_ID == "env_sheet_id"
            assert google_settings.GOOGLE_SERVICE_ACCOUNT_PATH == "/env/path"
            assert google_settings.GOOGLE_ACCOUNT_EMAIL == "env@example.com"
            assert google_settings.GOOGLE_ACCOUNT_KEY == "env_key"


class TestUtilityFunctions:
    """Тесты для вспомогательных функций"""
    
    def test_get_log_level(self):
        """Тест получения уровня логирования"""
        assert get_log_level() == "INFO"
    
    def test_is_debug_mode(self):
        """Тест проверки режима отладки"""
        assert is_debug_mode() == False


class TestGetSettings:
    """Тесты для функции get_settings"""
    
    def test_get_settings_caching(self):
        """Тест кэширования настроек"""
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'test_token',
            'NEWSAPI_API_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_openai_key',
            'GOOGLE_SHEET_ID': 'test_sheet_id',
            'GOOGLE_SERVICE_ACCOUNT_PATH': '/test/path',
            'GOOGLE_ACCOUNT_EMAIL': 'test@example.com',
            'GOOGLE_ACCOUNT_KEY': 'test_google_key'
        }):
            settings1 = get_settings()
            settings2 = get_settings()
            
            # Должны быть одним и тем же объектом благодаря кэшированию
            assert settings1 is settings2 