# tests/services/news/fetchers/test_mediastack_com.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import requests

from src.services.news.fetchers.mediastack_com import MediaStackFetcher
from src.services.news.fetchers.base import NewsAPIError
from src.config import MediaStackSettings


@pytest.fixture
def mock_settings():
    """Создает mock настройки для MediaStack"""
    settings = Mock(spec=MediaStackSettings)
    settings.access_key = "test_access_key"
    settings.base_url = "https://api.mediastack.com/v1"
    settings.page_size = 25
    settings.enabled = True
    settings.priority = 4
    settings.max_retries = 3
    settings.backoff_factor = 2.0
    settings.timeout = 30
    return settings


@pytest.fixture
def fetcher(mock_settings):
    """Создает экземпляр MediaStackFetcher с mock настройками"""
    return MediaStackFetcher(mock_settings)


class TestMediaStackFetcher:
    """Тесты для MediaStackFetcher"""
    
    def test_init(self, mock_settings):
        """Тест инициализации fetcher'а"""
        fetcher = MediaStackFetcher(mock_settings)
        
        assert fetcher.PROVIDER_NAME == "mediastack"
        assert fetcher.access_key == "test_access_key"
        assert fetcher.base_url == "https://api.mediastack.com/v1"
        assert fetcher.page_size == 25
        assert fetcher.enabled == True
        assert fetcher.max_retries == 3
        assert fetcher.timeout == 30
    
    def test_session_lazy_initialization(self, fetcher):
        """Тест ленивой инициализации сессии"""
        # Сессия не должна быть создана до первого обращения
        assert fetcher._session is None
        
        # После первого обращения сессия должна быть создана
        session = fetcher.session
        assert session is not None
        assert isinstance(session, requests.Session)
        
        # Повторное обращение должно возвращать ту же сессию
        assert fetcher.session is session
    
    def test_logger_lazy_initialization(self, fetcher):
        """Тест ленивой инициализации логгера"""
        # Логгер не должен быть создан до первого обращения
        assert fetcher._logger is None
        
        # После первого обращения логгер должен быть создан
        logger = fetcher.logger
        assert logger is not None
        
        # Повторное обращение должно возвращать тот же логгер
        assert fetcher.logger is logger
    
    def test_get_categories(self, fetcher):
        """Тест получения поддерживаемых категорий"""
        categories = fetcher.get_categories()
        
        expected_categories = [
            "general", "business", "entertainment", "health", 
            "science", "sports", "technology"
        ]
        
        assert categories == expected_categories
        assert len(categories) == 7
        assert "general" in categories
        assert "business" in categories
        assert "technology" in categories
    
    def test_get_languages(self, fetcher):
        """Тест получения поддерживаемых языков"""
        languages = fetcher.get_languages()
        
        expected_languages = [
            "ar", "de", "en", "es", "fr", "he", "it", 
            "nl", "no", "pt", "ru", "se", "zh"
        ]
        
        assert languages == expected_languages
        assert len(languages) == 13
        assert "en" in languages
        assert "ru" in languages
        assert "zh" in languages
    
    def test_get_supported_countries(self, fetcher):
        """Тест получения поддерживаемых стран"""
        countries = fetcher.get_supported_countries()
        
        assert isinstance(countries, list)
        assert len(countries) > 0
        assert "us" in countries
        assert "gb" in countries
        assert "ru" in countries
        assert "cn" in countries
    
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get, fetcher):
        """Тест успешного выполнения запроса"""
        # Настраиваем mock ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pagination": {"limit": 25, "offset": 0, "count": 10, "total": 100},
            "data": [
                {
                    "title": "Test News",
                    "description": "Test description",
                    "url": "https://example.com/news",
                    "author": "Test Author",
                    "source": "Test Source",
                    "category": "general",
                    "language": "en",
                    "country": "us",
                    "published_at": "2023-01-01T12:00:00Z",
                    "image": "https://example.com/image.jpg"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Выполняем запрос
        result = fetcher._make_request("news", {"limit": 10})
        
        # Проверяем результат
        assert "error" not in result
        assert "data" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["title"] == "Test News"
        
        # Проверяем, что запрос был выполнен с правильными параметрами
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["params"]["access_key"] == "test_access_key"
        assert kwargs["params"]["limit"] == 10
    
    @patch('src.services.news.fetchers.mediastack_com.MediaStackFetcher._make_request_with_retries')
    def test_make_request_api_error(self, mock_make_request_with_retries, fetcher):
        """Тест обработки ошибки API"""
        # Настраиваем mock ответ с ошибкой
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "code": "invalid_access_key",
                "message": "Invalid access key provided"
            }
        }
        
        # Настраиваем mock для _make_request_with_retries
        mock_make_request_with_retries.return_value = {"response": mock_response}
        
        # Выполняем запрос
        result = fetcher._make_request("news", {"limit": 10})
        
        # Проверяем результат
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "invalid_access_key" in str(result["error"])
        assert "Invalid access key provided" in str(result["error"])
    
    @patch('requests.Session.get')
    def test_make_request_network_error(self, mock_get, fetcher):
        """Тест обработки сетевой ошибки"""
        # Настраиваем mock для генерации исключения
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        # Выполняем запрос
        result = fetcher._make_request("news", {"limit": 10})
        
        # Проверяем результат
        assert "error" in result
        assert isinstance(result["error"], NewsAPIError)
        assert "Network error" in str(result["error"])
    
    @patch('requests.Session.get')
    def test_fetch_news_success(self, mock_get, fetcher):
        """Тест успешного получения новостей"""
        # Настраиваем mock ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pagination": {"limit": 25, "offset": 0, "count": 2, "total": 100},
            "data": [
                {
                    "title": "Test News 1",
                    "description": "Test description 1",
                    "url": "https://example.com/news1",
                    "author": "Author 1",
                    "source": "Source 1",
                    "category": "business",
                    "language": "en",
                    "country": "us",
                    "published_at": "2023-01-01T12:00:00Z",
                    "image": "https://example.com/image1.jpg"
                },
                {
                    "title": "Test News 2",
                    "description": "Test description 2",
                    "url": "https://example.com/news2",
                    "author": "Author 2",
                    "source": "Source 2",
                    "category": "technology",
                    "language": "en",
                    "country": "us",
                    "published_at": "2023-01-01T13:00:00Z",
                    "image": "https://example.com/image2.jpg"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Выполняем запрос
        result = fetcher.fetch_news(
            query="test",
            category="business",
            language="en",
            limit=10
        )
        
        # Проверяем результат
        assert "error" not in result
        assert "articles" in result
        assert len(result["articles"]) == 2
        
        # Проверяем первую статью
        article1 = result["articles"][0]
        assert article1["title"] == "Test News 1"
        assert article1["description"] == "Test description 1"
        assert article1["url"] == "https://example.com/news1"
        assert article1["author"] == "Author 1"
        assert article1["source"] == "Source 1"
        assert article1["category"] == "business"
        assert article1["language"] == "en"
        assert article1["image_url"] == "https://example.com/image1.jpg"
        assert article1["country"] == "us"
        assert "raw_data" in article1
        
        # Проверяем meta информацию
        assert "meta" in result
        assert result["meta"]["total"] == 100
        assert result["meta"]["limit"] == 10
        assert result["meta"]["count"] == 2
        
        # Проверяем pagination
        assert "pagination" in result
        assert result["pagination"]["total"] == 100
    
    @patch('requests.Session.get')
    def test_fetch_news_with_kwargs(self, mock_get, fetcher):
        """Тест получения новостей с дополнительными параметрами"""
        # Настраиваем mock ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pagination": {"limit": 25, "offset": 0, "count": 1, "total": 10},
            "data": [
                {
                    "title": "Test News",
                    "description": "Test description",
                    "url": "https://example.com/news",
                    "author": "Test Author",
                    "source": "Test Source",
                    "category": "general",
                    "language": "en",
                    "country": "us",
                    "published_at": "2023-01-01T12:00:00Z",
                    "image": "https://example.com/image.jpg"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Выполняем запрос с дополнительными параметрами
        result = fetcher.fetch_news(
            query="bitcoin",
            category="business",
            language="en",
            limit=5,
            sources="cnn,bbc",
            countries="us,gb",
            date="2023-01-01",
            offset=10
        )
        
        # Проверяем результат
        assert "error" not in result
        assert "articles" in result
        
        # Проверяем, что запрос был выполнен с правильными параметрами
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        params = kwargs["params"]
        
        assert params["access_key"] == "test_access_key"
        assert params["keywords"] == "bitcoin"
        assert params["categories"] == "business"
        assert params["languages"] == "en"
        assert params["limit"] == 5
        assert params["sources"] == "cnn,bbc"
        assert params["countries"] == "us,gb"
        assert params["date"] == "2023-01-01"
        assert params["offset"] == 10
    
    @patch('requests.Session.get')
    def test_fetch_headlines(self, mock_get, fetcher):
        """Тест получения заголовков (алиас для fetch_news)"""
        # Настраиваем mock ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pagination": {"limit": 25, "offset": 0, "count": 1, "total": 10},
            "data": [
                {
                    "title": "Headline News",
                    "description": "Headline description",
                    "url": "https://example.com/headline",
                    "author": "Author",
                    "source": "Source",
                    "category": "general",
                    "language": "en",
                    "country": "us",
                    "published_at": "2023-01-01T12:00:00Z",
                    "image": "https://example.com/image.jpg"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Выполняем запрос
        result = fetcher.fetch_headlines(limit=10)
        
        # Проверяем результат
        assert "error" not in result
        assert "articles" in result
        assert len(result["articles"]) == 1
        assert result["articles"][0]["title"] == "Headline News"
    
    @patch('requests.Session.get')
    def test_fetch_historical_news(self, mock_get, fetcher):
        """Тест получения исторических новостей"""
        # Настраиваем mock ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pagination": {"limit": 25, "offset": 0, "count": 1, "total": 10},
            "data": [
                {
                    "title": "Historical News",
                    "description": "Historical description",
                    "url": "https://example.com/historical",
                    "author": "Author",
                    "source": "Source",
                    "category": "general",
                    "language": "en",
                    "country": "us",
                    "published_at": "2023-01-01T12:00:00Z",
                    "image": "https://example.com/image.jpg"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Выполняем запрос
        result = fetcher.fetch_historical_news(
            date="2023-01-01",
            categories="business",
            languages="en",
            limit=10
        )
        
        # Проверяем результат
        assert "error" not in result
        assert "data" in result
        assert len(result["data"]) == 1
        
        # Проверяем, что запрос был выполнен с правильными параметрами
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        params = kwargs["params"]
        
        assert params["access_key"] == "test_access_key"
        assert params["date"] == "2023-01-01"
        assert params["categories"] == "business"
        assert params["languages"] == "en"
        assert params["limit"] == 10
    
    @patch('requests.Session.get')
    def test_get_sources(self, mock_get, fetcher):
        """Тест получения источников новостей"""
        # Настраиваем mock ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pagination": {"limit": 25, "offset": 0, "count": 2, "total": 100},
            "data": [
                {
                    "id": "cnn",
                    "name": "CNN",
                    "category": "general",
                    "country": "us",
                    "language": "en",
                    "url": "https://cnn.com"
                },
                {
                    "id": "bbc",
                    "name": "BBC",
                    "category": "general",
                    "country": "gb",
                    "language": "en",
                    "url": "https://bbc.com"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Выполняем запрос
        result = fetcher.get_sources(
            search="cnn",
            countries="us,gb",
            languages="en",
            limit=10
        )
        
        # Проверяем результат
        assert "error" not in result
        assert "sources" in result
        assert len(result["sources"]) == 2
        
        # Проверяем первый источник
        source1 = result["sources"][0]
        assert source1["id"] == "cnn"
        assert source1["name"] == "CNN"
        assert source1["category"] == "general"
        assert source1["country"] == "us"
        assert source1["language"] == "en"
        assert source1["url"] == "https://cnn.com"
        assert source1["provider"] == "mediastack"
        assert "raw_data" in source1
        
        # Проверяем pagination
        assert "pagination" in result
        assert result["pagination"]["total"] == 100
    
    @patch('requests.Session.get')
    def test_search_news(self, mock_get, fetcher):
        """Тест поиска новостей"""
        # Настраиваем mock ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pagination": {"limit": 25, "offset": 0, "count": 1, "total": 10},
            "data": [
                {
                    "title": "Search Result",
                    "description": "Search description",
                    "url": "https://example.com/search",
                    "author": "Author",
                    "source": "Source",
                    "category": "general",
                    "language": "en",
                    "country": "us",
                    "published_at": "2023-01-01T12:00:00Z",
                    "image": "https://example.com/image.jpg"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Выполняем поиск
        result = fetcher.search_news(
            query="bitcoin",
            language="en",
            limit=10
        )
        
        # Проверяем результат
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Search Result"
        assert result[0]["description"] == "Search description"
    
    @patch('requests.Session.get')
    def test_search_news_error(self, mock_get, fetcher):
        """Тест обработки ошибки при поиске новостей"""
        # Настраиваем mock для генерации ошибки
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        # Выполняем поиск
        result = fetcher.search_news(query="test", limit=10)
        
        # Проверяем результат
        assert isinstance(result, list)
        assert len(result) == 0
    
    @patch('requests.Session.get')
    def test_check_health_success(self, mock_get, fetcher):
        """Тест успешной проверки здоровья API"""
        # Настраиваем mock ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pagination": {"limit": 1, "offset": 0, "count": 1, "total": 100},
            "data": [{"id": "test", "name": "Test Source"}]
        }
        mock_get.return_value = mock_response
        
        # Выполняем проверку
        result = fetcher.check_health()
        
        # Проверяем результат
        assert result["status"] == "healthy"
        assert result["provider"] == "mediastack"
        assert "MediaStack API is accessible" in result["message"]
    
    @patch('src.services.news.fetchers.mediastack_com.MediaStackFetcher._make_request')
    def test_check_health_failure(self, mock_make_request, fetcher):
        """Тест неуспешной проверки здоровья API"""
        # Настраиваем mock для генерации ошибки
        mock_make_request.side_effect = Exception("Network error")
        
        # Выполняем проверку
        result = fetcher.check_health()
        
        # Проверяем результат
        assert result["status"] == "unhealthy"
        assert result["provider"] == "mediastack"
        assert "Health check failed" in result["message"]
    
    def test_extract_category(self, fetcher):
        """Тест извлечения категории из статьи"""
        # Тест с категорией в статье
        article_with_category = {"category": "business", "title": "Test"}
        result = fetcher._extract_category(article_with_category, "general")
        assert result == "business"
        
        # Тест без категории в статье
        article_without_category = {"title": "Test"}
        result = fetcher._extract_category(article_without_category, "general")
        assert result == "general"
        
        # Тест без категории в статье и без запрошенной категории
        result = fetcher._extract_category(article_without_category, None)
        assert result is None
    
    def test_add_random_delay(self, fetcher):
        """Тест добавления случайной задержки"""
        import time
        
        start_time = time.time()
        fetcher._add_random_delay()
        end_time = time.time()
        
        # Проверяем, что задержка была в пределах ожидаемого диапазона (0.1-0.5 секунд)
        delay = end_time - start_time
        assert 0.1 <= delay <= 0.6  # Небольшой запас для учета времени выполнения кода

    def test_extract_domain_from_url(self, fetcher):
        """Тест извлечения домена из URL"""
        test_cases = [
            ("https://www.cnn.com/path", "cnn.com"),
            ("http://sub.domain.com/path?param=value", "sub.domain.com"),
            ("https://example.org:8080/test", "example.org"),
            ("ftp://files.company.co.uk/downloads", "files.company.co.uk"),
            ("domain.com", "domain.com"),
            ("sub.example.net", "sub.example.net"),
            ("", None),
            ("invalid", "invalid"),
            ("https://", None),
        ]
        
        for url, expected in test_cases:
            result = fetcher._extract_domain_from_url(url)
            assert result == expected, f"Failed for URL: {url}, expected: {expected}, got: {result}"

    def test_extract_root_domain(self, fetcher):
        """Тест извлечения корневого домена"""
        # Тестируем различные входные данные
        assert fetcher._extract_root_domain("news.example.com") == "example"
        assert fetcher._extract_root_domain("sub.news.example.com") == "sub,example"
        assert fetcher._extract_root_domain("example.com") == "example"
        assert fetcher._extract_root_domain("news.com") == "news"  # news как единственная часть остается
        assert fetcher._extract_root_domain("") is None
        assert fetcher._extract_root_domain("single") == "single"
    
    @patch('src.services.news.fetchers.mediastack_com.MediaStackFetcher._search_source_by_domain')
    def test_check_source_by_domain_success(self, mock_search_source, fetcher):
        """Тест успешной проверки источника по домену"""
        # Настраиваем mock для возврата найденного источника
        mock_search_source.return_value = "cnn"
        
        result = fetcher.check_source_by_domain("cnn.com")
        
        assert result == "да"
        mock_search_source.assert_called_once_with("cnn.com")
    
    @patch('src.services.news.fetchers.mediastack_com.MediaStackFetcher._search_source_by_domain')
    def test_check_source_by_domain_not_found(self, mock_search_source, fetcher):
        """Тест проверки несуществующего источника"""
        # Настраиваем mock для возврата unavailable
        mock_search_source.return_value = "unavailable"
        
        result = fetcher.check_source_by_domain("nonexistent.com")
        
        assert result == "нет"
        mock_search_source.assert_called_once_with("nonexistent.com")
    
    @patch('src.services.news.fetchers.mediastack_com.MediaStackFetcher._extract_domain_from_url')
    @patch('src.services.news.fetchers.mediastack_com.MediaStackFetcher._search_source_by_domain')
    def test_check_source_by_domain_invalid_domain(self, mock_search_source, mock_extract_domain, fetcher):
        """Тест проверки с невалидным доменом"""
        # Настраиваем mock для возврата None (невалидный домен)
        mock_extract_domain.return_value = None
        
        result = fetcher.check_source_by_domain("invalid-domain")
        
        assert result == "нет"
        mock_extract_domain.assert_called_once_with("invalid-domain")
        mock_search_source.assert_not_called()
    
    @patch('src.services.news.fetchers.mediastack_com.MediaStackFetcher._search_source_by_domain')
    def test_check_source_by_domain_exception(self, mock_search_source, fetcher):
        """Тест обработки исключения при проверке источника"""
        # Настраиваем mock для выброса исключения
        mock_search_source.side_effect = Exception("API error")
        
        result = fetcher.check_source_by_domain("test.com")
        
        assert result.startswith("error: ")
        assert "API error" in result
    
    @patch('src.services.news.fetchers.mediastack_com.MediaStackFetcher._search_source_by_domain')
    def test_check_source_by_domain_with_url(self, mock_search_source, fetcher):
        """Тест проверки источника с полным URL"""
        mock_search_source.return_value = "bbc"
        
        result = fetcher.check_source_by_domain("https://www.bbc.com/news")
        
        assert result == "да"
        # Проверяем, что домен был нормализован
        mock_search_source.assert_called_once_with("bbc.com") 