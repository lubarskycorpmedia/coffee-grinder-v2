# tests/services/news/fetchers/test_newsapi_org.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.news.fetchers.newsapi_org import NewsAPIFetcher
from src.config import NewsAPISettings
from newsapi.newsapi_exception import NewsAPIException


class TestNewsAPIFetcher:
    """Тесты для NewsAPIFetcher"""
    
    @pytest.fixture
    def provider_settings(self):
        """Создает настройки провайдера для тестов"""
        return NewsAPISettings(
            api_key="test_key",
            max_retries=3,
            backoff_factor=2.0,
            default_country="us",
            page_size=100,
            supported_languages=["en", "ru", "fr"],
            supported_categories=["business", "entertainment", "general", "health", "science", "sports", "technology"]
        )
    
    @pytest.fixture
    def mock_client(self):
        """Создает мок клиента NewsAPI"""
        with patch('src.services.news.fetchers.newsapi_org.NewsApiClient') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def fetcher(self, provider_settings, mock_client):
        """Создает экземпляр NewsAPIFetcher с мок клиентом"""
        return NewsAPIFetcher(provider_settings)
    
    def test_init(self, provider_settings, mock_client):
        """Тест инициализации fetcher'а"""
        fetcher = NewsAPIFetcher(provider_settings)
        
        assert fetcher.PROVIDER_NAME == "newsapi"
        assert fetcher.settings == provider_settings
        assert fetcher.client == mock_client
    
    def test_fetch_news_success(self, fetcher, mock_client):
        """Тест успешного получения новостей"""
        # Подготавливаем мок ответ
        mock_response = {
            'status': 'ok',
            'articles': [
                {
                    'title': 'Test Article',
                    'description': 'Test Description',
                    'content': 'Test Content',
                    'url': 'https://example.com/article',
                    'urlToImage': 'https://example.com/image.jpg',
                    'publishedAt': '2023-12-01T10:00:00Z',
                    'source': {'name': 'Test Source', 'id': 'test-source'},
                    'author': 'Test Author'
                }
            ]
        }
        mock_client.get_top_headlines.return_value = mock_response
        
        # Вызываем метод
        result = fetcher.fetch_news(category="business", language="en", limit=50)
        
        # Проверяем результат в новом формате
        assert "articles" in result
        assert len(result["articles"]) == 1
        article = result["articles"][0]
        assert article['title'] == 'Test Article'
        assert article['provider'] == 'newsapi'
        assert article['source']['name'] == 'Test Source'
        
        # Проверяем вызов API
        mock_client.get_top_headlines.assert_called_once_with(
            category='business',
            language='en',
            country='us',
            page_size=50
        )
    
    def test_fetch_news_api_error(self, fetcher, mock_client):
        """Тест обработки ошибки API"""
        mock_client.get_top_headlines.return_value = {
            'status': 'error',
            'message': 'API Error'
        }
        
        result = fetcher.fetch_news()
        
        assert "error" in result
        assert result["error"].message == "NewsAPI error: API Error"
    
    def test_fetch_news_exception(self, fetcher, mock_client):
        """Тест обработки исключения NewsAPI"""
        mock_client.get_top_headlines.side_effect = NewsAPIException("API Exception")
        
        result = fetcher.fetch_news()
        
        assert "error" in result
        assert result["error"].message == "NewsAPI exception: API Exception"
    
    def test_search_news_success(self, fetcher, mock_client):
        """Тест успешного поиска новостей"""
        mock_response = {
            'status': 'ok',
            'articles': [
                {
                    'title': 'Search Result',
                    'description': 'Search Description',
                    'content': 'Search Content',
                    'url': 'https://example.com/search',
                    'urlToImage': None,
                    'publishedAt': '2023-12-01T12:00:00Z',
                    'source': {'name': 'Search Source', 'id': 'search-source'},
                    'author': 'Search Author'
                }
            ]
        }
        mock_client.get_everything.return_value = mock_response
        
        from_date = datetime(2023, 12, 1)
        to_date = datetime(2023, 12, 2)
        
        result = fetcher.search_news(
            query="test query",
            language="en",
            limit=25,
            from_date=from_date,
            to_date=to_date,
            sources="test-source"
        )
        
        assert len(result) == 1
        article = result[0]
        assert article['title'] == 'Search Result'
        assert article['provider'] == 'newsapi'
        
        # Проверяем параметры вызова
        mock_client.get_everything.assert_called_once_with(
            q="test query",
            language="en",
            page_size=25,
            sort_by="publishedAt",
            from_param="2023-12-01",
            to="2023-12-02",
            sources="test-source"
        )
    
    def test_search_news_api_error(self, fetcher, mock_client):
        """Тест обработки ошибки при поиске"""
        mock_client.get_everything.return_value = {
            'status': 'error',
            'message': 'Search Error'
        }
        
        result = fetcher.search_news("test query")
        
        assert result == []
    
    def test_get_sources_success(self, fetcher, mock_client):
        """Тест успешного получения источников"""
        mock_response = {
            'status': 'ok',
            'sources': [
                {
                    'id': 'test-source',
                    'name': 'Test Source',
                    'description': 'Test Description',
                    'url': 'https://example.com',
                    'category': 'business',
                    'language': 'en',
                    'country': 'us'
                }
            ]
        }
        mock_client.get_sources.return_value = mock_response
        
        result = fetcher.get_sources(language="en", category="business", country="us")
        
        assert "sources" in result
        assert len(result["sources"]) == 1
        source = result["sources"][0]
        assert source['id'] == 'test-source'
        assert source['name'] == 'Test Source'
        assert source['provider'] == 'newsapi'
        
        mock_client.get_sources.assert_called_once_with(
            language="en",
            category="business",
            country="us"
        )
    
    def test_get_sources_api_error(self, fetcher, mock_client):
        """Тест обработки ошибки при получении источников"""
        mock_client.get_sources.return_value = {
            'status': 'error',
            'message': 'Sources Error'
        }
        
        result = fetcher.get_sources()
        
        assert "sources" in result
        assert result["sources"] == []
    
    def test_get_categories(self, fetcher):
        """Тест получения списка категорий"""
        categories = fetcher.get_categories()
        
        expected_categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
        assert categories == expected_categories
    
    def test_get_languages(self, fetcher):
        """Тест получения списка языков"""
        languages = fetcher.get_languages()
        
        expected_languages = ["en", "ru", "fr"]
        assert languages == expected_languages
    
    def test_check_health_success(self, fetcher, mock_client):
        """Тест успешной проверки состояния"""
        mock_client.get_sources.return_value = {'status': 'ok'}
        
        result = fetcher.check_health()
        
        assert result['status'] == 'healthy'
        assert result['provider'] == 'newsapi'
        assert 'accessible' in result['message']
    
    def test_check_health_api_error(self, fetcher, mock_client):
        """Тест проверки состояния при ошибке API"""
        mock_client.get_sources.return_value = {
            'status': 'error',
            'message': 'Health Check Error'
        }
        
        result = fetcher.check_health()
        
        assert result['status'] == 'unhealthy'
        assert result['provider'] == 'newsapi'
        assert 'Health Check Error' in result['message']
    
    def test_check_health_exception(self, fetcher, mock_client):
        """Тест проверки состояния при исключении"""
        mock_client.get_sources.side_effect = NewsAPIException("Connection Error")
        
        result = fetcher.check_health()
        
        assert result['status'] == 'unhealthy'
        assert result['provider'] == 'newsapi'
        assert 'Connection Error' in result['message']
    
    def test_map_rubric_to_category(self, fetcher):
        """Тест маппинга рубрик в категории"""
        # Прямое соответствие
        assert fetcher._map_rubric_to_category("business") == "business"
        assert fetcher._map_rubric_to_category("TECHNOLOGY") == "technology"
        
        # Неизвестная рубрика
        assert fetcher._map_rubric_to_category("unknown") == "general"
        
        # None
        assert fetcher._map_rubric_to_category(None) is None
    
    def test_standardize_article(self, fetcher):
        """Тест стандартизации статьи"""
        article_data = {
            'title': 'Test Title',
            'description': 'Test Description',
            'content': 'Test Content',
            'url': 'https://example.com',
            'urlToImage': 'https://example.com/image.jpg',
            'publishedAt': '2023-12-01T10:00:00Z',
            'source': {'name': 'Test Source', 'id': 'test-source'},
            'author': 'Test Author'
        }
        
        result = fetcher._standardize_article(article_data)
        
        assert result['title'] == 'Test Title'
        assert result['provider'] == 'newsapi'
        assert result['source']['name'] == 'Test Source'
        assert result['published_at'] is not None
        assert result['raw_data'] == article_data
    
    def test_standardize_article_invalid_date(self, fetcher):
        """Тест стандартизации статьи с неверной датой"""
        article_data = {
            'title': 'Test Title',
            'publishedAt': 'invalid-date',
            'source': {'name': 'Test Source'}
        }
        
        result = fetcher._standardize_article(article_data)
        
        assert result['title'] == 'Test Title'
        assert result['published_at'] is None
    
    def test_standardize_source(self, fetcher):
        """Тест стандартизации источника"""
        source_data = {
            'id': 'test-source',
            'name': 'Test Source',
            'description': 'Test Description',
            'url': 'https://example.com',
            'category': 'business',
            'language': 'en',
            'country': 'us'
        }
        
        result = fetcher._standardize_source(source_data)
        
        assert result['id'] == 'test-source'
        assert result['name'] == 'Test Source'
        assert result['provider'] == 'newsapi'
        assert result['category'] == 'business'
    
    def test_language_fallback(self, fetcher, mock_client):
        """Тест fallback на английский для неподдерживаемого языка"""
        mock_client.get_top_headlines.return_value = {'status': 'ok', 'articles': []}
        
        fetcher.fetch_news(language="unsupported")
        
        # Проверяем что использовался английский
        mock_client.get_top_headlines.assert_called_once()
        call_args = mock_client.get_top_headlines.call_args[1]
        assert call_args['language'] == 'en'
    
    def test_limit_enforcement(self, fetcher, mock_client):
        """Тест ограничения лимита по page_size"""
        mock_client.get_top_headlines.return_value = {'status': 'ok', 'articles': []}
        
        fetcher.fetch_news(limit=200)  # Больше чем page_size=100
        
        # Проверяем что использовался максимальный page_size
        mock_client.get_top_headlines.assert_called_once()
        call_args = mock_client.get_top_headlines.call_args[1]
        assert call_args['page_size'] == 100 