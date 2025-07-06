# tests/services/news/test_fetcher_fabric.py

import pytest
from unittest.mock import patch

from src.services.news.fetcher_fabric import FetcherFactory, create_news_fetcher
from src.services.news.fetchers.base import BaseFetcher
from src.services.news.fetchers.thenewsapi_com import TheNewsAPIFetcher
from src.services.news.fetchers.newsapi_org import NewsAPIFetcher


class TestFetcherFactory:
    """Тесты для FetcherFactory"""
    
    def test_create_thenewsapi_fetcher(self):
        """Тест создания TheNewsAPI fetcher"""
        with patch('src.services.news.fetcher_fabric.get_settings') as mock_settings:
            mock_settings.return_value.NEWS_API_PROVIDER = "thenewsapi"
            mock_settings.return_value.THENEWSAPI_API_TOKEN = "test_token"
            mock_settings.return_value.MAX_RETRIES = 3
            mock_settings.return_value.BACKOFF_FACTOR = 2.0
            
            fetcher = FetcherFactory.create_fetcher()
            
            assert isinstance(fetcher, TheNewsAPIFetcher)
            assert isinstance(fetcher, BaseFetcher)
    
    def test_create_newsapi_fetcher(self):
        """Тест создания NewsAPI fetcher"""
        with patch('src.services.news.fetcher_fabric.get_settings') as mock_settings:
            mock_settings.return_value.NEWS_API_PROVIDER = "newsapi"
            
            fetcher = FetcherFactory.create_fetcher()
            
            assert isinstance(fetcher, NewsAPIFetcher)
            assert isinstance(fetcher, BaseFetcher)
    
    def test_create_fetcher_with_explicit_provider(self):
        """Тест создания fetcher с явно указанным провайдером"""
        with patch('src.services.news.fetcher_fabric.get_settings') as mock_settings:
            mock_settings.return_value.NEWS_API_PROVIDER = "thenewsapi"  # Конфиг говорит одно
            mock_settings.return_value.THENEWSAPI_API_TOKEN = "test_token"
            mock_settings.return_value.MAX_RETRIES = 3
            mock_settings.return_value.BACKOFF_FACTOR = 2.0
            
            # Но мы явно просим другое
            fetcher = FetcherFactory.create_fetcher("newsapi")
            
            assert isinstance(fetcher, NewsAPIFetcher)
    
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
            def fetch_headlines(self, **kwargs):
                return {"data": []}
            
            def fetch_all_news(self, **kwargs):
                return {"data": []}
            
            def fetch_top_stories(self, **kwargs):
                return {"data": []}
            
            def get_sources(self, **kwargs):
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
        with patch('src.services.news.fetcher_fabric.get_settings') as mock_settings:
            mock_settings.return_value.NEWS_API_PROVIDER = "thenewsapi"
            mock_settings.return_value.THENEWSAPI_API_TOKEN = "test_token"
            mock_settings.return_value.MAX_RETRIES = 3
            mock_settings.return_value.BACKOFF_FACTOR = 2.0
            
            fetcher = create_news_fetcher()
            
            assert isinstance(fetcher, TheNewsAPIFetcher)
    
    def test_create_news_fetcher_with_provider(self):
        """Тест удобной функции create_news_fetcher с провайдером"""
        fetcher = create_news_fetcher("newsapi")
        
        assert isinstance(fetcher, NewsAPIFetcher) 