# tests/services/news/test_fetcher_fabric.py

import pytest
from unittest.mock import patch, MagicMock

from src.services.news.fetcher_fabric import FetcherFactory, create_news_fetcher, create_news_fetcher_with_config
from src.services.news.fetchers.base import BaseFetcher
from src.services.news.fetchers.thenewsapi_com import TheNewsAPIFetcher
from src.services.news.fetchers.newsapi_org import NewsAPIFetcher


class TestFetcherFactory:
    """Тесты для FetcherFactory"""
    

    
    def test_create_thenewsapi_fetcher_with_explicit_params(self):
        """Тест создания TheNewsAPI fetcher с явными параметрами"""
        fetcher = FetcherFactory.create_fetcher(
            provider="thenewsapi",
            api_token="explicit_token",
            max_retries=5,
            backoff_factor=1.5
        )
        
        assert isinstance(fetcher, TheNewsAPIFetcher)
        assert fetcher.api_token == "explicit_token"
        assert fetcher.max_retries == 5
        assert fetcher.backoff_factor == 1.5
    
    def test_create_thenewsapi_fetcher_with_defaults(self):
        """Тест создания TheNewsAPI fetcher с дефолтными параметрами"""
        fetcher = FetcherFactory.create_fetcher(
            provider="thenewsapi",
            api_token="test_token"
        )
        
        assert isinstance(fetcher, TheNewsAPIFetcher)
        assert fetcher.api_token == "test_token"
        assert fetcher.max_retries == 3  # дефолт
        assert fetcher.backoff_factor == 0.5  # дефолт
    
    def test_create_thenewsapi_fetcher_missing_token(self):
        """Тест создания TheNewsAPI fetcher без токена"""
        with pytest.raises(ValueError) as exc_info:
            FetcherFactory.create_fetcher(provider="thenewsapi")
        
        assert "api_token is required for thenewsapi provider" in str(exc_info.value)
    
    def test_create_newsapi_fetcher(self):
        """Тест создания NewsAPI fetcher"""
        fetcher = FetcherFactory.create_fetcher(provider="newsapi")
        
        assert isinstance(fetcher, NewsAPIFetcher)
        assert isinstance(fetcher, BaseFetcher)
    

    
    def test_create_fetcher_unsupported_provider(self):
        """Тест создания fetcher с неподдерживаемым провайдером"""
        with pytest.raises(ValueError) as exc_info:
            FetcherFactory.create_fetcher("unsupported_provider")
        
        assert "Unsupported news provider" in str(exc_info.value)
        assert "unsupported_provider" in str(exc_info.value)
        assert "thenewsapi" in str(exc_info.value)
        assert "newsapi" in str(exc_info.value)
    

    

    
    def test_get_available_providers(self):
        """Тест получения списка доступных провайдеров"""
        providers = FetcherFactory.get_available_providers()
        
        assert isinstance(providers, list)
        assert "thenewsapi" in providers
        assert "newsapi" in providers
        assert len(providers) == 2
    
    def test_register_fetcher(self):
        """Тест регистрации нового fetcher"""
        class CustomFetcher(BaseFetcher):
            def __init__(self):
                pass

            def fetch_headlines(self, **kwargs):
                return {"data": []}

            def fetch_all_news(self, **kwargs):
                return {"data": []}

            def fetch_top_stories(self, **kwargs):
                return {"data": []}

            def get_sources(self, **kwargs):
                return {"data": []}

            def fetch_news(self, **kwargs):
                return {"data": []}
        
        # Регистрируем новый fetcher
        FetcherFactory.register_fetcher("custom", CustomFetcher)
        
        # Проверяем что он доступен
        providers = FetcherFactory.get_available_providers()
        assert "custom" in providers
        
        # Проверяем что можем создать его экземпляр
        fetcher = FetcherFactory.create_fetcher("custom")
        assert isinstance(fetcher, CustomFetcher)
        
        # Очищаем после теста
        del FetcherFactory._fetchers["custom"]
    
    def test_create_news_fetcher_convenience_function(self):
        """Тест удобной функции create_news_fetcher"""
        fetcher = create_news_fetcher(
            provider="thenewsapi",
            api_token="test_token",
            max_retries=3,
            backoff_factor=2.0
        )
        
        assert isinstance(fetcher, TheNewsAPIFetcher)
        assert fetcher.api_token == "test_token"
    
    def test_create_news_fetcher_with_config(self):
        """Тест create_news_fetcher_with_config с настройками из config"""
        with patch('src.config.get_news_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.NEWS_API_PROVIDER = "thenewsapi"
            mock_settings.THENEWSAPI_API_TOKEN = "config_token"
            mock_settings.MAX_RETRIES = 4
            mock_settings.BACKOFF_FACTOR = 3.0
            mock_get_settings.return_value = mock_settings
            
            fetcher = create_news_fetcher_with_config()
            
            assert isinstance(fetcher, TheNewsAPIFetcher)
            assert fetcher.api_token == "config_token"
            assert fetcher.max_retries == 4
            assert fetcher.backoff_factor == 3.0
    
    def test_create_fetcher_with_config_settings(self):
        """Тест создания fetcher с настройками из config"""
        with patch('src.config.get_news_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.NEWS_API_PROVIDER = "thenewsapi"
            mock_settings.THENEWSAPI_API_TOKEN = "config_token"
            mock_settings.MAX_RETRIES = 4
            mock_settings.BACKOFF_FACTOR = 3.0
            mock_get_settings.return_value = mock_settings
            
            fetcher = FetcherFactory.create_fetcher_with_config()
            
            assert isinstance(fetcher, TheNewsAPIFetcher)
            assert fetcher.api_token == "config_token"
            assert fetcher.max_retries == 4
            assert fetcher.backoff_factor == 3.0
    
    def test_create_fetcher_with_config_settings_error(self):
        """Тест обработки ошибки при получении настроек"""
        with patch('src.config.get_news_settings') as mock_get_settings:
            mock_get_settings.side_effect = Exception("Settings error")
            
            with pytest.raises(ValueError) as exc_info:
                FetcherFactory.create_fetcher_with_config(provider="thenewsapi")
            
            assert "Cannot get news settings for thenewsapi" in str(exc_info.value)
    
    def test_create_fetcher_with_config_fallback_provider(self):
        """Тест использования fallback провайдера при ошибке настроек"""
        with patch('src.config.get_news_settings') as mock_get_settings:
            # При получении провайдера - ошибка, используется fallback
            mock_get_settings.side_effect = [
                Exception("Settings error"),  # Первый вызов для провайдера
                Exception("Settings error"),  # Второй вызов для токена
            ]
            
            # Должен использовать fallback "thenewsapi" но без настроек вызовет ошибку
            with pytest.raises(ValueError):
                FetcherFactory.create_fetcher_with_config() 