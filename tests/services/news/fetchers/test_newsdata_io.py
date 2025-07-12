# tests/services/news/fetchers/test_newsdata_io.py

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from src.services.news.fetchers.newsdata_io import NewsDataIOFetcher
from src.services.news.fetchers.base import NewsAPIError


class MockNewsDataIOSettings:
    """Mock для настроек NewsData.io"""
    def __init__(self):
        self.api_key = "test_api_key"
        self.base_url = "https://newsdata.io/api/1"
        self.page_size = 10
        self.enabled = True
        self.priority = 3
        self.max_retries = 3
        self.backoff_factor = 2.0
        self.timeout = 30


@pytest.fixture
def mock_settings():
    """Фикстура для настроек провайдера"""
    return MockNewsDataIOSettings()


@pytest.fixture
def mock_client():
    """Фикстура для мока клиента NewsData.io"""
    with patch('src.services.news.fetchers.newsdata_io.NewsDataApiClient') as mock:
        yield mock


@pytest.fixture
def fetcher(mock_settings, mock_client):
    """Фикстура для создания экземпляра fetcher'а"""
    return NewsDataIOFetcher(mock_settings)


class TestNewsDataIOFetcher:
    """Тесты для NewsDataIOFetcher"""
    
    def test_init(self, mock_settings, mock_client):
        """Тест инициализации fetcher'а"""
        fetcher = NewsDataIOFetcher(mock_settings)
        
        assert fetcher.PROVIDER_NAME == "newsdata"
        assert fetcher.api_key == "test_api_key"
        assert fetcher.base_url == "https://newsdata.io/api/1"
        assert fetcher.page_size == 10
        
        # Проверяем что клиент был создан с правильным API ключом
        mock_client.assert_called_once_with(apikey="test_api_key")
    
    def test_fetch_news_success(self, fetcher):
        """Тест успешного получения новостей"""
        # Мокаем ответ API
        mock_response = {
            'status': 'success',
            'results': [
                {
                    'title': 'Test Article',
                    'description': 'Test Description',
                    'link': 'https://example.com/article',
                    'pubDate': '2025-01-14T10:00:00Z',
                    'source_id': 'test_source',
                    'language': 'en',
                    'category': ['business'],
                    'country': ['us'],
                    'creator': ['Test Author'],
                    'image_url': 'https://example.com/image.jpg',
                    'content': 'Test content',
                    'sentiment': 'neutral',
                    'duplicate': False
                }
            ]
        }
        
        fetcher.client.news_api.return_value = mock_response
        
        result = fetcher.fetch_news(
            query="test",
            category="business",
            language="en",
            limit=10
        )
        
        # Проверяем результат
        assert "articles" in result
        assert len(result["articles"]) == 1
        
        article = result["articles"][0]
        assert article["title"] == "Test Article"
        assert article["description"] == "Test Description"
        assert article["url"] == "https://example.com/article"
        assert article["provider"] == "newsdata"
        assert article["language"] == "en"
        assert article["category"] == "business"
        assert article["country"] == "us"
        assert article["author"] == "Test Author"
        assert article["image_url"] == "https://example.com/image.jpg"
        assert article["sentiment"] == "neutral"
        assert article["duplicate"] is False
        
        # Проверяем что API был вызван с правильными параметрами
        fetcher.client.news_api.assert_called_once_with(
            size=10,
            q="test",
            category="business",
            language="en"
        )
    
    def test_fetch_news_api_error(self, fetcher):
        """Тест обработки ошибки API"""
        # Мокаем ошибочный ответ API
        mock_response = {
            'status': 'error',
            'message': 'API key is invalid'
        }
        
        fetcher.client.news_api.return_value = mock_response
        
        result = fetcher.fetch_news(query="test")
        
        # Проверяем что возвращается ошибка
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "API key is invalid" in str(result["error"])
    
    def test_fetch_news_exception(self, fetcher):
        """Тест обработки исключения при запросе"""
        # Мокаем исключение
        fetcher.client.news_api.side_effect = Exception("Connection error")
        
        result = fetcher.fetch_news(query="test")
        
        # Проверяем что возвращается ошибка
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "Connection error" in str(result["error"])
    
    def test_search_news_success(self, fetcher):
        """Тест успешного поиска новостей"""
        # Мокаем ответ API
        mock_response = {
            'status': 'success',
            'results': [
                {
                    'title': 'Search Result',
                    'description': 'Search Description',
                    'link': 'https://example.com/search',
                    'pubDate': '2025-01-14T10:00:00Z',
                    'source_id': 'search_source',
                    'language': 'en'
                }
            ]
        }
        
        fetcher.client.news_api.return_value = mock_response
        
        result = fetcher.search_news(
            query="search term",
            language="en",
            limit=5
        )
        
        # Проверяем результат
        assert len(result) == 1
        assert result[0]["title"] == "Search Result"
        assert result[0]["provider"] == "newsdata"
        
        # Проверяем что API был вызван с правильными параметрами
        fetcher.client.news_api.assert_called_once_with(
            q="search term",
            size=5,
            language="en"
        )
    
    def test_search_news_with_dates(self, fetcher):
        """Тест поиска новостей с датами"""
        # Мокаем ответ API
        mock_response = {
            'status': 'success',
            'results': []
        }
        
        fetcher.client.news_api.return_value = mock_response
        
        from_date = datetime(2025, 1, 1)
        to_date = datetime(2025, 1, 14)
        
        result = fetcher.search_news(
            query="test",
            from_date=from_date,
            to_date=to_date,
            country="us",
            category="business"
        )
        
        # Проверяем что API был вызван с правильными параметрами
        fetcher.client.news_api.assert_called_once_with(
            q="test",
            size=10,
            from_date="2025-01-01",
            to_date="2025-01-14",
            country="us",
            category="business"
        )
    
    def test_get_sources_success(self, fetcher):
        """Тест успешного получения источников"""
        # Мокаем ответ API
        mock_response = {
            'status': 'success',
            'results': [
                {
                    'id': 'source1',
                    'name': 'Test Source',
                    'description': 'Test source description',
                    'url': 'https://testsource.com',
                    'category': ['business'],
                    'language': ['en'],
                    'country': ['us']
                }
            ]
        }
        
        fetcher.client.sources_api.return_value = mock_response
        
        result = fetcher.get_sources(
            language="en",
            category="business",
            country="us"
        )
        
        # Проверяем результат
        assert "sources" in result
        assert len(result["sources"]) == 1
        
        source = result["sources"][0]
        assert source["id"] == "source1"
        assert source["name"] == "Test Source"
        assert source["provider"] == "newsdata"
        assert source["category"] == "business"
        assert source["language"] == "en"
        assert source["country"] == "us"
        
        # Проверяем что API был вызван с правильными параметрами
        fetcher.client.sources_api.assert_called_once_with(
            language="en",
            category="business",
            country="us"
        )
    
    def test_check_health_success(self, fetcher):
        """Тест успешной проверки здоровья"""
        # Мокаем успешный ответ API
        mock_response = {'status': 'success'}
        fetcher.client.sources_api.return_value = mock_response
        
        result = fetcher.check_health()
        
        assert result["status"] == "healthy"
        assert result["provider"] == "newsdata"
        assert "NewsData.io is accessible" in result["message"]
    
    def test_check_health_failure(self, fetcher):
        """Тест неуспешной проверки здоровья"""
        # Мокаем ошибочный ответ API
        mock_response = {
            'status': 'error',
            'message': 'Service unavailable'
        }
        fetcher.client.sources_api.return_value = mock_response
        
        result = fetcher.check_health()
        
        assert result["status"] == "unhealthy"
        assert result["provider"] == "newsdata"
        assert "Service unavailable" in result["message"]
    
    def test_check_health_exception(self, fetcher):
        """Тест проверки здоровья при исключении"""
        # Мокаем исключение
        fetcher.client.sources_api.side_effect = Exception("Network error")
        
        result = fetcher.check_health()
        
        assert result["status"] == "unhealthy"
        assert result["provider"] == "newsdata"
        assert "Network error" in result["message"]
    
    def test_get_categories(self, fetcher):
        """Тест получения поддерживаемых категорий"""
        categories = fetcher.get_categories()
        
        expected_categories = [
            "business", "entertainment", "environment", "food", "health", 
            "politics", "science", "sports", "technology", "top", 
            "tourism", "world"
        ]
        
        assert categories == expected_categories
    
    def test_get_languages(self, fetcher):
        """Тест получения поддерживаемых языков"""
        languages = fetcher.get_languages()
        
        # Проверяем что есть основные языки
        assert "en" in languages
        assert "ru" in languages
        assert "es" in languages
        assert "fr" in languages
        assert "de" in languages
        assert len(languages) > 30  # NewsData.io поддерживает много языков
    
    def test_fetch_headlines_wrapper(self, fetcher):
        """Тест обертки fetch_headlines"""
        # Мокаем fetch_news
        with patch.object(fetcher, 'fetch_news') as mock_fetch:
            mock_fetch.return_value = {"articles": [{"title": "test"}]}
            
            result = fetcher.fetch_headlines(category="business")
            
            assert "articles" in result
            mock_fetch.assert_called_once_with(category="business")
    
    def test_fetch_all_news_wrapper(self, fetcher):
        """Тест обертки fetch_all_news"""
        # Мокаем search_news
        with patch.object(fetcher, 'search_news') as mock_search:
            mock_search.return_value = [{"title": "test"}]
            
            result = fetcher.fetch_all_news(query="test")
            
            assert "articles" in result
            mock_search.assert_called_once_with(query="test")
    
    def test_fetch_top_stories_wrapper(self, fetcher):
        """Тест обертки fetch_top_stories"""
        # Мокаем fetch_news
        with patch.object(fetcher, 'fetch_news') as mock_fetch:
            mock_fetch.return_value = {"articles": [{"title": "test"}]}
            
            result = fetcher.fetch_top_stories(limit=5)
            
            assert "articles" in result
            mock_fetch.assert_called_once_with(limit=5)
    
    def test_standardize_article_minimal_data(self, fetcher):
        """Тест стандартизации статьи с минимальными данными"""
        article = {
            'title': 'Minimal Article',
            'link': 'https://example.com'
        }
        
        result = fetcher._standardize_article(article)
        
        assert result['title'] == 'Minimal Article'
        assert result['url'] == 'https://example.com'
        assert result['provider'] == 'newsdata'
        assert result['description'] == ''
        assert result['published_at'] is None
        assert result['author'] is None
        assert result['category'] is None
    
    def test_standardize_article_invalid_date(self, fetcher):
        """Тест стандартизации статьи с некорректной датой"""
        article = {
            'title': 'Test Article',
            'link': 'https://example.com',
            'pubDate': 'invalid-date'
        }
        
        with patch('src.services.news.fetchers.newsdata_io.logger') as mock_logger:
            result = fetcher._standardize_article(article)
            
            assert result['published_at'] is None
            mock_logger.warning.assert_called_once()
    
    def test_standardize_source_minimal_data(self, fetcher):
        """Тест стандартизации источника с минимальными данными"""
        source = {
            'id': 'test_source',
            'name': 'Test Source'
        }
        
        result = fetcher._standardize_source(source)
        
        assert result['id'] == 'test_source'
        assert result['name'] == 'Test Source'
        assert result['provider'] == 'newsdata'
        assert result['description'] == ''
        assert result['category'] is None
        assert result['language'] is None
        assert result['country'] is None 