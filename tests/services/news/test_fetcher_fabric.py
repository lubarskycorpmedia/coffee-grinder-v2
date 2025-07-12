# tests/services/news/test_fetcher_fabric.py

import pytest
from unittest.mock import patch, MagicMock

from src.services.news.fetcher_fabric import FetcherFactory, create_news_fetcher_from_config, create_default_news_fetcher, create_news_fetcher_with_fallback
from src.services.news.fetchers.base import BaseFetcher, FetcherRegistry
from src.services.news.fetchers.thenewsapi_com import TheNewsAPIFetcher
from src.services.news.fetchers.newsapi_org import NewsAPIFetcher


class TestFetcherFactory:
    """Тесты для FetcherFactory"""
    
    def test_get_available_providers(self):
        """Тест получения списка доступных провайдеров"""
        providers = FetcherFactory.get_available_providers()
        
        assert isinstance(providers, list)
        assert "thenewsapi" in providers
        assert "newsapi" in providers
        assert len(providers) >= 2
    
    def test_create_fetcher_from_config_settings(self):
        """Тест создания fetcher с настройками из config"""
        with patch('src.config.get_news_providers_settings') as mock_get_providers_settings:
            from src.config import TheNewsAPISettings
            
            mock_thenewsapi_settings = TheNewsAPISettings(
                api_token="config_token",
                max_retries=4,
                backoff_factor=3.0
            )
            
            mock_providers_settings = MagicMock()
            mock_providers_settings.get_provider_settings.return_value = mock_thenewsapi_settings
            mock_get_providers_settings.return_value = mock_providers_settings
            
            fetcher = FetcherFactory.create_fetcher_from_config("thenewsapi")
            
            assert isinstance(fetcher, TheNewsAPIFetcher)
            assert fetcher.api_token == "config_token"
            assert fetcher.max_retries == 4
            assert fetcher.backoff_factor == 3.0
    
    def test_create_fetcher_from_config_provider_not_found(self):
        """Тест обработки ошибки при отсутствии провайдера в настройках"""
        with patch('src.config.get_news_providers_settings') as mock_get_providers_settings:
            mock_providers_settings = MagicMock()
            mock_providers_settings.get_provider_settings.return_value = None
            mock_get_providers_settings.return_value = mock_providers_settings
            
            with pytest.raises(ValueError) as exc_info:
                FetcherFactory.create_fetcher_from_config("thenewsapi")
            
            assert "Provider 'thenewsapi' not found in configuration" in str(exc_info.value)
    
    def test_create_fetcher_from_config_provider_disabled(self):
        """Тест обработки ошибки при отключенном провайдере"""
        with patch('src.config.get_news_providers_settings') as mock_get_providers_settings:
            from src.config import TheNewsAPISettings
            
            mock_thenewsapi_settings = TheNewsAPISettings(
                api_token="config_token",
                enabled=False
            )
            
            mock_providers_settings = MagicMock()
            mock_providers_settings.get_provider_settings.return_value = mock_thenewsapi_settings
            mock_get_providers_settings.return_value = mock_providers_settings
            
            with pytest.raises(ValueError) as exc_info:
                FetcherFactory.create_fetcher_from_config("thenewsapi")
            
            assert "Provider 'thenewsapi' is disabled in configuration" in str(exc_info.value)
    
    def test_create_fetcher_from_config_unsupported_provider(self):
        """Тест создания fetcher с неподдерживаемым провайдером"""
        with pytest.raises(ValueError) as exc_info:
            FetcherFactory.create_fetcher_from_config("unsupported_provider")
        
        assert "Unsupported news provider" in str(exc_info.value)
        assert "unsupported_provider" in str(exc_info.value)
    
    def test_create_default_fetcher(self):
        """Тест создания дефолтного fetcher"""
        with patch('src.config.get_news_providers_settings') as mock_get_providers_settings:
            from src.config import TheNewsAPISettings
            
            mock_thenewsapi_settings = TheNewsAPISettings(api_token="default_token")
            
            mock_providers_settings = MagicMock()
            mock_providers_settings.default_provider = "thenewsapi"
            mock_providers_settings.get_provider_settings.return_value = mock_thenewsapi_settings
            mock_get_providers_settings.return_value = mock_providers_settings
            
            fetcher = FetcherFactory.create_default_fetcher()
            
            assert isinstance(fetcher, TheNewsAPIFetcher)
            assert fetcher.api_token == "default_token"
    
    def test_create_fetcher_with_fallback(self):
        """Тест создания fetcher с fallback"""
        with patch('src.config.get_news_providers_settings') as mock_get_providers_settings:
            from src.config import TheNewsAPISettings
            
            mock_thenewsapi_settings = TheNewsAPISettings(api_token="fallback_token")
            
            mock_providers_settings = MagicMock()
            mock_providers_settings.default_provider = "thenewsapi"
            mock_providers_settings.fallback_providers = ["newsapi"]
            mock_providers_settings.get_provider_settings.return_value = mock_thenewsapi_settings
            mock_get_providers_settings.return_value = mock_providers_settings
            
            fetcher = FetcherFactory.create_fetcher_with_fallback("thenewsapi")
            
            assert isinstance(fetcher, TheNewsAPIFetcher)
            assert fetcher.api_token == "fallback_token"
    
    def test_create_news_fetcher_from_config(self):
        """Тест create_news_fetcher_from_config с настройками из config"""
        with patch('src.config.get_news_providers_settings') as mock_get_providers_settings:
            from src.config import TheNewsAPISettings
            
            mock_thenewsapi_settings = TheNewsAPISettings(
                api_token="config_token",
                max_retries=4,
                backoff_factor=3.0
            )
            
            mock_providers_settings = MagicMock()
            mock_providers_settings.get_provider_settings.return_value = mock_thenewsapi_settings
            mock_get_providers_settings.return_value = mock_providers_settings
            
            fetcher = create_news_fetcher_from_config("thenewsapi")
            
            assert isinstance(fetcher, TheNewsAPIFetcher)
            assert fetcher.api_token == "config_token"
            assert fetcher.max_retries == 4
            assert fetcher.backoff_factor == 3.0


class TestFetcherRegistry:
    """Тесты для FetcherRegistry"""
    
    def test_get_available_providers(self):
        """Тест получения списка доступных провайдеров"""
        providers = FetcherRegistry.get_available_providers()
        
        assert isinstance(providers, list)
        assert "thenewsapi" in providers
        assert "newsapi" in providers
    
    def test_get_fetcher_class(self):
        """Тест получения класса fetcher'а"""
        fetcher_class = FetcherRegistry.get_fetcher_class("thenewsapi")
        assert fetcher_class == TheNewsAPIFetcher
        
        fetcher_class = FetcherRegistry.get_fetcher_class("newsapi")
        assert fetcher_class == NewsAPIFetcher
        
        fetcher_class = FetcherRegistry.get_fetcher_class("nonexistent")
        assert fetcher_class is None 