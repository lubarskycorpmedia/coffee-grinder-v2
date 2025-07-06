# tests/services/news/fetchers/test_thenewsapi_com.py

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timedelta

from src.services.news.fetchers.thenewsapi_com import TheNewsAPIFetcher
from src.services.news.fetchers.base import NewsAPIError


class TestTheNewsAPIFetcher:
    """Тесты для TheNewsAPIFetcher"""
    
    @pytest.fixture
    def fetcher(self):
        """Создает экземпляр fetcher'а для тестов"""
        # Теперь можем создать fetcher без моков при импорте
        fetcher = TheNewsAPIFetcher()
        # Мокаем логгер чтобы избежать проблем с настройками
        fetcher._logger = Mock()
        return fetcher
    
    @pytest.fixture
    def mock_settings(self):
        """Мокает settings для тестов"""
        mock_settings = MagicMock()
        mock_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_settings.MAX_RETRIES = 3
        mock_settings.BACKOFF_FACTOR = 2.0
        return mock_settings
    
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
                "code": "invalid_api_token",
                "message": "The provided API token is invalid"
            }
        }
    
    def test_successful_fetch_headlines(self, fetcher, mock_successful_response, mock_settings):
        """Тест успешного получения заголовков"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
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
            
            # Проверяем что API токен добавлен в параметры
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[1]["params"]["api_token"] == "test_token"
    
    def test_successful_fetch_all_news(self, fetcher, mock_settings):
        """Тест успешного поиска всех новостей"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
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
    
    def test_successful_fetch_top_stories(self, fetcher, mock_settings):
        """Тест успешного получения топ новостей"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
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
    
    def test_successful_get_sources(self, fetcher, mock_settings):
        """Тест успешного получения источников"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
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
    
    def test_api_error_response(self, fetcher, mock_error_response, mock_settings):
        """Тест обработки ошибки API в ответе"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
        with patch.object(fetcher.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_error_response
            mock_get.return_value = mock_response
            
            result = fetcher.fetch_headlines()
            
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert "invalid" in result["error"].message.lower()
    
    def test_rate_limit_429_with_retries(self, fetcher, mock_settings):
        """Тест обработки 429 ошибки с ретраями"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
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
            
            # Проверяем успешный результат
            assert "error" not in result
            assert "data" in result
    
    def test_rate_limit_429_max_retries_exceeded(self, fetcher, mock_settings):
        """Тест обработки 429 когда исчерпаны все попытки"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
        with patch.object(fetcher.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # Все попытки возвращают 429
            mock_response = Mock()
            mock_response.status_code = 429
            mock_get.return_value = mock_response
            
            result = fetcher.fetch_headlines()
            
            # Проверяем что сделано MAX_RETRIES попыток
            assert mock_get.call_count == 3
            
            # Проверяем что были задержки (на 1 меньше чем попыток)
            assert mock_sleep.call_count == 2
            
            # Проверяем что возвращена ошибка
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert result["error"].status_code == 429
            assert "rate limit" in result["error"].message.lower()
    
    def test_http_error_handling(self, fetcher, mock_settings):
        """Тест обработки HTTP ошибок"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
        with patch.object(fetcher.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_response.json.side_effect = ValueError("No JSON")
            mock_get.return_value = mock_response
            
            result = fetcher.fetch_headlines()
            
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert result["error"].status_code == 404
    
    def test_server_error_with_retry(self, fetcher, mock_settings):
        """Тест обработки серверной ошибки 5xx с ретраем"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
        with patch.object(fetcher.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # Первая попытка - 500, вторая - успех
            responses = []
            
            mock_500 = Mock()
            mock_500.status_code = 500
            mock_500.text = "Internal Server Error"
            mock_500.json.side_effect = ValueError("No JSON")
            responses.append(mock_500)
            
            mock_success = Mock()
            mock_success.status_code = 200
            mock_success.json.return_value = {"data": []}
            responses.append(mock_success)
            
            mock_get.side_effect = responses
            
            result = fetcher.fetch_headlines()
            
            # Проверяем что сделано 2 попытки
            assert mock_get.call_count == 2
            
            # Проверяем что была задержка
            assert mock_sleep.call_count == 1
            
            # Проверяем успешный результат
            assert "error" not in result
    
    def test_network_error_handling(self, fetcher, mock_settings):
        """Тест обработки сетевых ошибок"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
        with patch.object(fetcher.session, 'get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # Все попытки - сетевая ошибка
            mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
            
            result = fetcher.fetch_headlines()
            
            # Проверяем что сделано MAX_RETRIES попыток
            assert mock_get.call_count == 3
            
            # Проверяем что были задержки
            assert mock_sleep.call_count == 2
            
            # Проверяем что возвращена ошибка
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert "network error" in result["error"].message.lower()
    
    def test_exponential_backoff_calculation(self, fetcher, mock_settings):
        """Тест расчета экспоненциального backoff"""
        # Мокаем _settings напрямую
        fetcher._settings = mock_settings
        
        # Проверяем что задержка увеличивается экспоненциально
        delay_0 = fetcher._exponential_backoff(0)
        delay_1 = fetcher._exponential_backoff(1)
        delay_2 = fetcher._exponential_backoff(2)
        
        # Базовая проверка что задержки увеличиваются
        assert delay_0 < delay_1 < delay_2
        
        # Проверяем что не превышает максимум
        delay_large = fetcher._exponential_backoff(10)
        assert delay_large <= 60.0
    
    def test_fetch_recent_tech_news(self, fetcher, mock_settings):
        """Тест получения последних технологических новостей"""
        # Мокаем settings
        fetcher._settings = mock_settings
        
        mock_response_data = {
            "data": [
                {
                    "uuid": "tech-news-1",
                    "title": "AI Breakthrough",
                    "categories": ["tech"]
                }
            ]
        }
        
        with patch.object(fetcher.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            result = fetcher.fetch_recent_tech_news(days_back=2)
            
            assert "error" not in result
            assert "data" in result
            
            # Проверяем что в запросе есть правильные параметры
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            assert "technology" in params["search"]
            assert params["categories"] == "tech,business"
            assert params["sort"] == "relevance_score"
            
            # Проверяем дату
            expected_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
            assert params["published_after"] == expected_date 