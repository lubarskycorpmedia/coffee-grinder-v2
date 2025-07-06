# tests/services/news/fetchers/test_newsapi_org.py

import pytest

from src.services.news.fetchers.newsapi_org import NewsAPIFetcher
from src.services.news.fetchers.base import NewsAPIError


class TestNewsAPIFetcher:
    """Тесты для NewsAPIFetcher (заглушка)"""
    
    @pytest.fixture
    def fetcher(self):
        """Создает экземпляр NewsAPIFetcher"""
        return NewsAPIFetcher()
    
    def test_fetch_headlines_not_implemented(self, fetcher):
        """Тест что fetch_headlines не реализован"""
        result = fetcher.fetch_headlines()
        
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "not implemented" in result["error"].message.lower()
    
    def test_fetch_all_news_not_implemented(self, fetcher):
        """Тест что fetch_all_news не реализован"""
        result = fetcher.fetch_all_news()
        
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "not implemented" in result["error"].message.lower()
    
    def test_fetch_top_stories_not_implemented(self, fetcher):
        """Тест что fetch_top_stories не реализован"""
        result = fetcher.fetch_top_stories()
        
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "not implemented" in result["error"].message.lower()
    
    def test_get_sources_not_implemented(self, fetcher):
        """Тест что get_sources не реализован"""
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
            fetcher.get_sources
        ]
        
        for method in methods:
            result = method()
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert "newsapi.org" in result["error"].message.lower() 