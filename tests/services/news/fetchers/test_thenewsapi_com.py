# tests/services/news/fetchers/test_thenewsapi_com.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.news.fetchers.thenewsapi_com import TheNewsAPIFetcher
from src.services.news.fetchers.base import NewsAPIError
from src.config import TheNewsAPISettings


class TestTheNewsAPIFetcher:
    """Тесты для TheNewsAPIFetcher"""
    
    @pytest.fixture
    def provider_settings(self):
        """Создает настройки провайдера для тестов"""
        return TheNewsAPISettings(
            api_token="test_token",
            max_retries=3,
            backoff_factor=2.0
        )
    
    @pytest.fixture
    def fetcher(self, provider_settings):
        """Создает экземпляр fetcher'а для тестов"""
        fetcher = TheNewsAPIFetcher(provider_settings)
        # Мокаем логгер чтобы избежать проблем с настройками
        fetcher._logger = Mock()
        return fetcher
    
    @pytest.fixture
    def mock_successful_response(self):
        """Мок успешного ответа API"""
        return {
            "data": {
                "general": [
                    {
                        "uuid": "test-uuid",
                        "title": "Test News Title",
                        "description": "Test news description",
                        "url": "https://example.com/news",
                        "image_url": "https://example.com/image.jpg",
                        "language": "en",
                        "published_at": "2025-01-07T12:00:00Z",
                        "source": "example.com",
                        "categories": ["general"],
                        "locale": "us"
                    }
                ]
            }
        }
    
    @pytest.fixture
    def mock_error_response(self):
        """Мок ответа с ошибкой API"""
        return {
            "error": {
                "code": "invalid_token",
                "message": "Invalid API token provided"
            }
        }
    
    def test_fetcher_initialization(self, provider_settings):
        """Тест правильной инициализации fetcher'а"""
        fetcher = TheNewsAPIFetcher(provider_settings)
        
        assert fetcher.api_token == "test_token"
        assert fetcher.max_retries == 3
        assert fetcher.backoff_factor == 2.0
        assert fetcher.base_url == "https://api.thenewsapi.com/v1"
    
    def test_successful_fetch_headlines(self, fetcher, mock_successful_response):
        """Тест успешного получения заголовков"""
        with patch.object(fetcher.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_successful_response
            mock_get.return_value = mock_response
            
            result = fetcher.fetch_headlines(locale="us", language="en")
            
            assert "error" not in result
            assert "data" in result
            assert "general" in result["data"]
            assert len(result["data"]["general"]) == 1
            assert result["data"]["general"][0]["title"] == "Test News Title"
            
            # Проверяем что API токен был добавлен в параметры
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert params["api_token"] == "test_token"
    
    def test_successful_fetch_all_news(self, fetcher):
        """Тест успешного поиска всех новостей"""
        mock_response_data = {
            "data": [
                {
                    "uuid": "test-uuid-1",
                    "title": "AI News",
                    "description": "Latest AI developments",
                    "url": "https://example.com/ai-news"
                }
            ]
        }
        
        with patch.object(fetcher.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = fetcher.fetch_all_news(
                search="AI + technology",
                language="en",
                published_after="2025-01-01"
            )
            
            assert "error" not in result
            assert "data" in result
            assert len(result["data"]) == 1
            assert result["data"][0]["title"] == "AI News"
    
    def test_successful_fetch_top_stories(self, fetcher):
        """Тест успешного получения топ новостей"""
        mock_response_data = {
            "data": [
                {
                    "uuid": "top-story-1",
                    "title": "Breaking News",
                    "description": "Important breaking news"
                }
            ]
        }
        
        with patch.object(fetcher.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = fetcher.fetch_top_stories(locale="us", categories="general")
            
            assert "error" not in result
            assert "data" in result
            assert result["data"][0]["title"] == "Breaking News"
    
    def test_successful_get_sources(self, fetcher):
        """Тест успешного получения источников"""
        mock_response_data = {
            "data": [
                {
                    "id": "example-com",
                    "name": "Example News",
                    "domain": "example.com",
                    "categories": ["general"]
                }
            ]
        }
        
        with patch.object(fetcher.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = fetcher.get_sources(language="en")
            
            assert "error" not in result
            assert "data" in result
            assert result["data"][0]["name"] == "Example News"
    
    def test_api_error_response(self, fetcher, mock_error_response):
        """Тест обработки ошибки API в ответе"""
        with patch.object(fetcher.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_error_response
            mock_get.return_value = mock_response
            
            result = fetcher.fetch_headlines()
            
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert "invalid" in result["error"].message.lower()
    
    def test_rate_limit_429_with_retries(self, fetcher):
        """Тест обработки 429 ошибки с ретраями"""
        with patch.object(fetcher.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # Первые 2 попытки - 429, третья - успех
            responses = []
            
            # 429 ответы
            for i in range(2):
                mock_429 = Mock()
                mock_429.status_code = 429
                responses.append(mock_429)
            
            # Успешный ответ
            mock_success = Mock()
            mock_success.status_code = 200
            mock_success.json.return_value = {"data": []}
            responses.append(mock_success)
            
            mock_get.side_effect = responses
            
            result = fetcher.fetch_headlines()
            
            # Проверяем что сделано 3 попытки
            assert mock_get.call_count == 3
            
            # Проверяем что были задержки (2 раза sleep)
            assert mock_sleep.call_count == 2
            
            # Проверяем что получили успешный результат
            assert "error" not in result
            assert "data" in result
    
    def test_rate_limit_429_max_retries_exceeded(self, fetcher):
        """Тест превышения максимального количества попыток при 429"""
        with patch.object(fetcher.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # Все попытки возвращают 429
            mock_429 = Mock()
            mock_429.status_code = 429
            mock_get.return_value = mock_429
            
            result = fetcher.fetch_headlines()
            
            # Проверяем что сделано максимальное количество попыток
            assert mock_get.call_count == 3
            
            # Проверяем что получили ошибку
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert result["error"].status_code == 429
    
    def test_server_error_with_retry(self, fetcher):
        """Тест обработки серверной ошибки 500 с ретраем"""
        with patch.object(fetcher.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # Первая попытка - 500, вторая - успех
            mock_500 = Mock()
            mock_500.status_code = 500
            
            mock_success = Mock()
            mock_success.status_code = 200
            mock_success.json.return_value = {"data": []}
            
            mock_get.side_effect = [mock_500, mock_success]
            
            result = fetcher.fetch_headlines()
            
            # Проверяем что сделано 2 попытки
            assert mock_get.call_count == 2
            
            # Проверяем что была задержка
            assert mock_sleep.call_count == 1
            
            # Проверяем что получили успешный результат
            assert "error" not in result
            assert "data" in result
    
    def test_network_error_handling(self, fetcher):
        """Тест обработки сетевой ошибки"""
        with patch.object(fetcher.session, 'get') as mock_get:
            # Имитируем сетевую ошибку
            mock_get.side_effect = Exception("Network error")
            
            result = fetcher.fetch_headlines()
            
            # Проверяем что получили ошибку
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert "network error" in result["error"].message.lower()
    
    def test_exponential_backoff_calculation(self, fetcher):
        """Тест расчета экспоненциального backoff"""
        # Тестируем приватный метод
        delay_0 = fetcher._exponential_backoff(0)
        delay_1 = fetcher._exponential_backoff(1)
        delay_2 = fetcher._exponential_backoff(2)
        
        # Проверяем что задержки увеличиваются
        assert delay_0 < delay_1 < delay_2
        
        # Проверяем что все задержки положительные
        assert delay_0 > 0
        assert delay_1 > 0
        assert delay_2 > 0
    
    def test_fetch_recent_tech_news(self, fetcher):
        """Интеграционный тест получения технологических новостей"""
        mock_response_data = {
            "data": [
                {
                    "uuid": "tech-news-1",
                    "title": "New AI Breakthrough",
                    "description": "Scientists achieve new AI milestone",
                    "url": "https://example.com/ai-news",
                    "published_at": "2025-01-07T10:00:00Z",
                    "source": "TechNews",
                    "categories": ["technology"],
                    "language": "en"
                }
            ]
        }
        
        with patch.object(fetcher.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = fetcher.fetch_news(
                query="AI technology",
                category="technology",
                language="en",
                limit=10
            )
            
            assert "error" not in result
            assert "articles" in result
            assert len(result["articles"]) == 1
            
            article = result["articles"][0]
            assert article["title"] == "New AI Breakthrough"
            assert article["category"] == "technology"
            assert article["language"] == "en" 