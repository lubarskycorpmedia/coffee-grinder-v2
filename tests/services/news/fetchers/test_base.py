# tests/services/news/fetchers/test_base.py

import pytest
from datetime import datetime

from src.services.news.fetchers.base import NewsAPIError, BaseFetcher


class TestNewsAPIError:
    """Тесты для NewsAPIError"""
    
    def test_create_error_with_message_only(self):
        """Тест создания ошибки только с сообщением"""
        error = NewsAPIError("Test error message")
        
        assert error.message == "Test error message"
        assert error.status_code is None
        assert error.retry_count == 0
        assert isinstance(error.timestamp, datetime)
    
    def test_create_error_with_all_params(self):
        """Тест создания ошибки со всеми параметрами"""
        error = NewsAPIError("API error", status_code=429, retry_count=3)
        
        assert error.message == "API error"
        assert error.status_code == 429
        assert error.retry_count == 3
        assert isinstance(error.timestamp, datetime)
    
    def test_error_string_representation(self):
        """Тест строкового представления ошибки"""
        error = NewsAPIError("Rate limit exceeded", status_code=429, retry_count=2)
        
        error_str = str(error)
        
        assert "NewsAPIError" in error_str
        assert "Rate limit exceeded" in error_str
        assert "429" in error_str
        assert "2" in error_str
    
    def test_error_string_representation_no_status(self):
        """Тест строкового представления ошибки без статус кода"""
        error = NewsAPIError("Network error", retry_count=1)
        
        error_str = str(error)
        
        assert "NewsAPIError" in error_str
        assert "Network error" in error_str
        assert "None" in error_str
        assert "1" in error_str


class TestBaseFetcher:
    """Тесты для BaseFetcher"""
    
    def test_base_fetcher_is_abstract(self):
        """Тест что BaseFetcher является абстрактным классом"""
        with pytest.raises(TypeError):
            BaseFetcher()
    
    def test_base_fetcher_methods_are_abstract(self):
        """Тест что методы BaseFetcher являются абстрактными"""
        class IncompleteFetcher(BaseFetcher):
            pass
        
        with pytest.raises(TypeError):
            IncompleteFetcher()
    
    def test_complete_fetcher_implementation(self):
        """Тест полной реализации BaseFetcher"""
        class CompleteFetcher(BaseFetcher):
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
        
        # Не должно вызвать исключение
        fetcher = CompleteFetcher()
        
        # Проверяем что методы работают
        assert fetcher.fetch_headlines() == {"data": []}
        assert fetcher.fetch_all_news() == {"data": []}
        assert fetcher.fetch_top_stories() == {"data": []}
        assert fetcher.get_sources() == {"data": []} 