# tests/services/news/fetchers/test_gnews_io.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from requests import Response

from src.services.news.fetchers.gnews_io import GNewsIOFetcher
from src.services.news.fetchers.base import NewsAPIError
from src.config import GNewsIOSettings


class TestGNewsIOFetcher:
    """Тесты для GNewsIOFetcher"""
    
    @pytest.fixture
    def mock_settings(self):
        """Фикстура с настройками для тестов"""
        return GNewsIOSettings(
            api_key="test_api_key",
            base_url="https://gnews.io/api/v4",
            page_size=100,
            enabled=True,
            priority=1,
            max_retries=3,
            backoff_factor=2.0,
            timeout=30
        )
    
    @pytest.fixture
    def fetcher(self, mock_settings):
        """Фикстура с экземпляром fetcher'а"""
        return GNewsIOFetcher(mock_settings)
    
    @pytest.fixture
    def mock_response_data(self):
        """Фикстура с примером ответа от GNews API"""
        return {
            "totalArticles": 2,
            "articles": [
                {
                    "title": "Test Article 1",
                    "description": "Test description 1",
                    "content": "Test content 1",
                    "url": "https://example.com/article1",
                    "image": "https://example.com/image1.jpg",
                    "publishedAt": "2023-12-01T10:00:00Z",
                    "source": {
                        "name": "Test Source 1",
                        "url": "https://example.com"
                    }
                },
                {
                    "title": "Test Article 2", 
                    "description": "Test description 2",
                    "content": "Test content 2",
                    "url": "https://example.com/article2",
                    "image": "https://example.com/image2.jpg",
                    "publishedAt": "2023-12-01T11:00:00Z",
                    "source": {
                        "name": "Test Source 2",
                        "url": "https://example2.com"
                    }
                }
            ]
        }
    
    def test_provider_name(self, fetcher):
        """Тест правильности имени провайдера"""
        assert fetcher.PROVIDER_NAME == "gnews"
    
    def test_init(self, mock_settings):
        """Тест инициализации fetcher'а"""
        fetcher = GNewsIOFetcher(mock_settings)
        
        assert fetcher.api_key == "test_api_key"
        assert fetcher.base_url == "https://gnews.io/api/v4"
        assert fetcher.page_size == 100
        assert fetcher.enabled is True
        assert fetcher.max_retries == 3
        assert fetcher.timeout == 30
    
    def test_get_categories(self, fetcher):
        """Тест получения поддерживаемых категорий"""
        categories = fetcher.get_categories()
        
        expected_categories = [
            "general", "world", "nation", "business", "technology",
            "entertainment", "sports", "science", "health"
        ]
        
        assert categories == expected_categories
        assert len(categories) == 9
    
    def test_get_languages(self, fetcher):
        """Тест получения поддерживаемых языков"""
        languages = fetcher.get_languages()
        
        # Проверяем что есть основные языки
        assert "en" in languages
        assert "ru" in languages
        assert "de" in languages
        assert "fr" in languages
        assert "es" in languages
        assert len(languages) > 10
    
    def test_get_countries(self, fetcher):
        """Тест получения поддерживаемых стран"""
        countries = fetcher.get_countries()
        
        # Проверяем что есть основные страны
        assert "us" in countries
        assert "gb" in countries
        assert "ru" in countries
        assert "de" in countries
        assert "fr" in countries
        assert len(countries) > 20
    
    def test_map_category_to_gnews(self, fetcher):
        """Тест маппинга категорий"""
        # Прямое соответствие
        assert fetcher._map_category_to_gnews("business") == "business"
        assert fetcher._map_category_to_gnews("technology") == "technology"
        assert fetcher._map_category_to_gnews("health") == "health"
        
        # Маппинг синонимов
        assert fetcher._map_category_to_gnews("tech") == "technology"
        assert fetcher._map_category_to_gnews("sport") == "sports"
        assert fetcher._map_category_to_gnews("finance") == "business"
        assert fetcher._map_category_to_gnews("politics") == "nation"
        
        # Несуществующая категория
        assert fetcher._map_category_to_gnews("unknown") is None
        
        # None
        assert fetcher._map_category_to_gnews(None) is None
    
    @patch('src.services.news.fetchers.gnews_io.requests.Session')
    def test_make_request_success(self, mock_session_class, fetcher, mock_response_data):
        """Тест успешного HTTP запроса"""
        # Настройка мока
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        # Мокаем метод базового класса
        with patch.object(fetcher, '_make_request_with_retries') as mock_base_request:
            mock_base_request.return_value = {"response": mock_response, "success": True}
            
            result = fetcher._make_request("search", {"q": "test"})
            
            # Проверяем результат
            assert result == mock_response_data
            assert "error" not in result
            
            # Проверяем что был вызван базовый метод
            mock_base_request.assert_called_once()
            call_args = mock_base_request.call_args
            assert call_args[1]["url"] == "https://gnews.io/api/v4/search"
            assert call_args[1]["params"]["apikey"] == "test_api_key"
            assert call_args[1]["params"]["q"] == "test"
    
    @patch('src.services.news.fetchers.gnews_io.requests.Session')
    def test_make_request_api_error(self, mock_session_class, fetcher):
        """Тест обработки ошибки API"""
        # Настройка мока для ошибки API
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Invalid API key"}
        
        with patch.object(fetcher, '_make_request_with_retries') as mock_base_request:
            mock_base_request.return_value = {"response": mock_response, "success": True}
            
            result = fetcher._make_request("search", {"q": "test"})
            
            # Проверяем что вернулась ошибка
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert "Invalid API key" in str(result["error"])
    
    @patch('src.services.news.fetchers.gnews_io.requests.Session')
    def test_make_request_network_error(self, mock_session_class, fetcher):
        """Тест обработки сетевой ошибки"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Мокаем сетевую ошибку из базового класса
        with patch.object(fetcher, '_make_request_with_retries') as mock_base_request:
            mock_base_request.return_value = {"error": NewsAPIError("Network error", None, 1)}
            
            result = fetcher._make_request("search", {"q": "test"})
            
            # Проверяем что ошибка прошла через
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
    
    def test_fetch_headlines_success(self, fetcher, mock_response_data):
        """Тест успешного получения заголовков"""
        with patch.object(fetcher, '_make_request') as mock_request:
            mock_request.return_value = mock_response_data
            
            result = fetcher.fetch_headlines(
                category="business",
                language="en",
                country="us",
                limit=10
            )
            
            # Проверяем вызов API
            mock_request.assert_called_once_with("top-headlines", {
                "max": 10,
                "category": "business",
                "lang": "en",
                "country": "us"
            })
            
            # Проверяем результат
            assert result == mock_response_data
    
    def test_fetch_headlines_with_category_mapping(self, fetcher, mock_response_data):
        """Тест получения заголовков с маппингом категории"""
        with patch.object(fetcher, '_make_request') as mock_request:
            mock_request.return_value = mock_response_data
            
            result = fetcher.fetch_headlines(category="tech", limit=5)
            
            # Проверяем что категория была замаплена
            mock_request.assert_called_once_with("top-headlines", {
                "max": 5,
                "category": "technology"
            })
    
    def test_fetch_all_news_success(self, fetcher, mock_response_data):
        """Тест успешного поиска новостей"""
        with patch.object(fetcher, '_make_request') as mock_request:
            mock_request.return_value = mock_response_data
            
            result = fetcher.fetch_all_news(
                query="test query",
                language="en",
                country="us",
                limit=20
            )
            
            # Проверяем вызов API
            mock_request.assert_called_once_with("search", {
                "q": "test query",
                "max": 20,
                "lang": "en",
                "country": "us"
            })
            
            # Проверяем результат
            assert result == mock_response_data
    
    def test_fetch_news_with_query(self, fetcher, mock_response_data):
        """Тест универсального метода fetch_news с запросом"""
        with patch.object(fetcher, 'fetch_all_news') as mock_fetch_all:
            mock_fetch_all.return_value = mock_response_data
            
            result = fetcher.fetch_news(
                query="test query",
                category="business",
                language="en",
                limit=10
            )
            
            # Проверяем что был вызван fetch_all_news
            mock_fetch_all.assert_called_once_with(
                query="test query",
                language="en",
                limit=10
            )
            
            # Проверяем стандартизацию результата
            assert "articles" in result
            assert len(result["articles"]) == 2
    
    def test_fetch_news_without_query(self, fetcher, mock_response_data):
        """Тест универсального метода fetch_news без запроса"""
        with patch.object(fetcher, 'fetch_headlines') as mock_fetch_headlines:
            mock_fetch_headlines.return_value = mock_response_data
            
            result = fetcher.fetch_news(
                category="business",
                language="en",
                limit=10
            )
            
            # Проверяем что был вызван fetch_headlines
            mock_fetch_headlines.assert_called_once_with(
                category="business",
                language="en",
                limit=10
            )
            
            # Проверяем стандартизацию результата
            assert "articles" in result
            assert len(result["articles"]) == 2
    
    def test_search_news_success(self, fetcher, mock_response_data):
        """Тест поиска новостей"""
        with patch.object(fetcher, 'fetch_all_news') as mock_fetch_all:
            mock_fetch_all.return_value = mock_response_data
            
            result = fetcher.search_news(
                query="test query",
                language="en",
                limit=15
            )
            
            # Проверяем что был вызван fetch_all_news
            mock_fetch_all.assert_called_once_with(
                query="test query",
                language="en",
                limit=15
            )
            
            # Проверяем что результат - список стандартизированных статей
            assert isinstance(result, list)
            assert len(result) == 2
            
            # Проверяем стандартизацию первой статьи
            article = result[0]
            assert article["title"] == "Test Article 1"
            assert article["provider"] == "gnews"
            assert "raw_data" in article
    
    def test_search_news_error(self, fetcher):
        """Тест поиска новостей с ошибкой"""
        with patch.object(fetcher, 'fetch_all_news') as mock_fetch_all:
            mock_fetch_all.return_value = {"error": NewsAPIError("API error")}
            
            result = fetcher.search_news(query="test", limit=10)
            
            # При ошибке должен вернуться пустой список
            assert result == []
    
    def test_standardize_article(self, fetcher):
        """Тест стандартизации статьи"""
        article_data = {
            "title": "Test Article",
            "description": "Test description",
            "content": "Test content",
            "url": "https://example.com/article",
            "image": "https://example.com/image.jpg",
            "publishedAt": "2023-12-01T10:00:00Z",
            "source": {
                "name": "Test Source",
                "url": "https://example.com"
            }
        }
        
        result = fetcher._standardize_article(
            article_data, 
            language="en", 
            category="business"
        )
        
        # Проверяем стандартизированные поля
        assert result["title"] == "Test Article"
        assert result["description"] == "Test description"
        assert result["content"] == "Test content"
        assert result["url"] == "https://example.com/article"
        assert result["image_url"] == "https://example.com/image.jpg"
        assert result["provider"] == "gnews"
        assert result["language"] == "en"
        assert result["category"] == "business"
        assert result["raw_data"] == article_data
        
        # Проверяем парсинг даты
        assert isinstance(result["published_at"], datetime)
        assert result["published_at"].year == 2023
        assert result["published_at"].month == 12
        assert result["published_at"].day == 1
        
        # Проверяем источник
        assert result["source"]["name"] == "Test Source"
        assert result["source"]["url"] == "https://example.com"
    
    def test_standardize_article_with_invalid_date(self, fetcher):
        """Тест стандартизации статьи с некорректной датой"""
        article_data = {
            "title": "Test Article",
            "publishedAt": "invalid-date",
            "source": {"name": "Test Source"}
        }
        
        result = fetcher._standardize_article(article_data)
        
        # При некорректной дате published_at должен быть None
        assert result["published_at"] is None
    
    def test_check_health_success(self, fetcher):
        """Тест успешной проверки здоровья"""
        mock_response = {"totalArticles": 1, "articles": []}
        
        with patch.object(fetcher, '_make_request') as mock_request:
            mock_request.return_value = mock_response
            
            result = fetcher.check_health()
            
            assert result["status"] == "healthy"
            assert result["provider"] == "gnews"
            assert "GNews API is accessible" in result["message"]
    
    def test_check_health_failure(self, fetcher):
        """Тест неуспешной проверки здоровья"""
        with patch.object(fetcher, '_make_request') as mock_request:
            mock_request.return_value = {"error": NewsAPIError("API error")}
            
            result = fetcher.check_health()
            
            assert result["status"] == "unhealthy"
            assert result["provider"] == "gnews"
            assert "API error" in result["message"]
    
    def test_get_sources(self, fetcher):
        """Тест получения источников (GNews не поддерживает)"""
        result = fetcher.get_sources()
        
        # GNews не предоставляет эндпоинт для источников
        assert result == {"sources": []}
    
    def test_fetch_top_stories(self, fetcher, mock_response_data):
        """Тест получения топ новостей"""
        with patch.object(fetcher, 'fetch_headlines') as mock_fetch_headlines:
            mock_fetch_headlines.return_value = mock_response_data
            
            result = fetcher.fetch_top_stories(category="business")
            
            mock_fetch_headlines.assert_called_once_with(category="business")
            assert result == mock_response_data
    
    def test_session_property_lazy_initialization(self, fetcher):
        """Тест ленивой инициализации сессии"""
        # При первом обращении создается сессия
        session1 = fetcher.session
        assert session1 is not None
        
        # При повторном обращении возвращается та же сессия
        session2 = fetcher.session
        assert session1 is session2
    
    def test_logger_property_lazy_initialization(self, fetcher):
        """Тест ленивой инициализации логгера"""
        # При первом обращении создается логгер
        logger1 = fetcher.logger
        assert logger1 is not None
        
        # При повторном обращении возвращается тот же логгер
        logger2 = fetcher.logger
        assert logger1 is logger2 