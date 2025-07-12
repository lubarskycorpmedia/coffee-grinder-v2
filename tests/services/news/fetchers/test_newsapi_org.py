# tests/services/news/fetchers/test_newsapi_org.py

import pytest
from unittest.mock import Mock

from src.services.news.fetchers.newsapi_org import NewsAPIFetcher
from src.services.news.fetchers.base import NewsAPIError
from src.config import NewsAPISettings


class TestNewsAPIFetcher:
    """Тесты для NewsAPIFetcher (заглушка)"""
    
    @pytest.fixture
    def provider_settings(self):
        """Создает настройки провайдера для тестов"""
        return NewsAPISettings(
            api_key="test_key",
            max_retries=3,
            backoff_factor=2.0
        )
    
    @pytest.fixture
    def fetcher(self, provider_settings):
        """Создает экземпляр NewsAPIFetcher"""
        return NewsAPIFetcher(provider_settings)
    
    def test_fetch_headlines_not_implemented(self, fetcher):
        """Тест что fetch_headlines возвращает ошибку 'не реализовано'"""
        result = fetcher.fetch_headlines()
        
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "not implemented" in result["error"].message.lower()
    
    def test_fetch_all_news_not_implemented(self, fetcher):
        """Тест что fetch_all_news возвращает ошибку 'не реализовано'"""
        result = fetcher.fetch_all_news()
        
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "not implemented" in result["error"].message.lower()
    
    def test_fetch_top_stories_not_implemented(self, fetcher):
        """Тест что fetch_top_stories возвращает ошибку 'не реализовано'"""
        result = fetcher.fetch_top_stories()
        
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "not implemented" in result["error"].message.lower()
    
    def test_get_sources_not_implemented(self, fetcher):
        """Тест что get_sources возвращает ошибку 'не реализовано'"""
        result = fetcher.get_sources()
        
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "not implemented" in result["error"].message.lower()
    
    def test_all_methods_return_same_error_type(self, fetcher):
        """Тест что все методы возвращают одинаковый тип ошибки"""
        methods = [
            fetcher.fetch_headlines,
            fetcher.fetch_all_news,
            fetcher.fetch_top_stories,
            fetcher.get_sources,
            fetcher.fetch_news
        ]
        
        for method in methods:
            result = method()
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert "not implemented" in result["error"].message.lower() 