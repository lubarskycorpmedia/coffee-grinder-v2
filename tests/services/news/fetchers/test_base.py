# tests/services/news/fetchers/test_base.py

import pytest
import requests
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.news.fetchers.base import BaseFetcher, NewsAPIError
from src.config import BaseProviderSettings


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
    
    def test_complete_fetcher_implementation(self):
        """Тест полной реализации BaseFetcher"""
        # Создаем mock настройки
        mock_settings = Mock(spec=BaseProviderSettings)
        mock_settings.max_retries = 3
        mock_settings.backoff_factor = 2.0
        mock_settings.timeout = 30
        mock_settings.enabled = True
        
        class CompleteFetcher(BaseFetcher):
            PROVIDER_NAME = "test"
            
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
        fetcher = CompleteFetcher(mock_settings)
        
        # Проверяем что настройки были установлены
        assert fetcher.max_retries == 3
        assert fetcher.backoff_factor == 2.0
        assert fetcher.timeout == 30
        assert fetcher.enabled is True
    
    def test_abstract_methods_enforcement(self):
        """Тест что абстрактные методы действительно абстрактные"""
        # Создаем mock настройки
        mock_settings = Mock(spec=BaseProviderSettings)
        mock_settings.max_retries = 3
        mock_settings.backoff_factor = 2.0
        mock_settings.timeout = 30
        mock_settings.enabled = True
        
        class IncompleteFetcher(BaseFetcher):
            PROVIDER_NAME = "incomplete"
            # Не реализуем все абстрактные методы
            pass
        
        # Должно вызвать TypeError при попытке создания экземпляра
        with pytest.raises(TypeError):
            IncompleteFetcher(mock_settings)


class TestBaseFetcherRetryLogic:
    """Тесты для логики ретраев в BaseFetcher"""
    
    @pytest.fixture
    def mock_settings(self):
        """Мок настроек провайдера"""
        settings = Mock(spec=BaseProviderSettings)
        settings.max_retries = 3
        settings.backoff_factor = 2.0
        settings.timeout = 30
        settings.enabled = True
        return settings
    
    @pytest.fixture
    def test_fetcher(self, mock_settings):
        """Тестовый fetcher для проверки базовой логики"""
        class TestRetryFetcher(BaseFetcher):
            PROVIDER_NAME = "test_retry"
            
            def fetch_headlines(self, **kwargs):
                return {}
            
            def fetch_all_news(self, **kwargs):
                return {}
            
            def fetch_top_stories(self, **kwargs):
                return {}
            
            def get_sources(self, **kwargs):
                return {}
            
            def fetch_news(self, **kwargs):
                return {}
        
        fetcher = TestRetryFetcher(mock_settings)
        fetcher._logger = Mock()  # Мокируем логгер
        return fetcher
    
    def test_exponential_backoff(self, test_fetcher):
        """Тест расчета экспоненциального backoff"""
        delay_0 = test_fetcher._exponential_backoff(0)
        delay_1 = test_fetcher._exponential_backoff(1)
        delay_2 = test_fetcher._exponential_backoff(2)
        
        # Проверяем что задержки увеличиваются
        assert delay_0 < delay_1 < delay_2
        
        # Проверяем что все задержки положительные
        assert delay_0 > 0
        assert delay_1 > 0
        assert delay_2 > 0
        
        # Проверяем что задержка не превышает максимум
        delay_large = test_fetcher._exponential_backoff(10)
        assert delay_large <= 60.0
    
    def test_should_retry_logic(self, test_fetcher):
        """Тест логики определения необходимости повтора"""
        # Создаем мок ответа
        response_429 = Mock()
        response_429.status_code = 429
        
        response_500 = Mock()
        response_500.status_code = 500
        
        response_404 = Mock()
        response_404.status_code = 404
        
        # Тестируем что повторяем для 429 и 500
        assert test_fetcher._should_retry(response_429, 0) == True
        assert test_fetcher._should_retry(response_500, 1) == True
        
        # Тестируем что не повторяем для 404
        assert test_fetcher._should_retry(response_404, 0) == False
        
        # Тестируем что не повторяем при достижении максимума попыток
        assert test_fetcher._should_retry(response_429, 2) == False  # max_retries = 3
    
    def test_make_request_with_retries_success(self, test_fetcher):
        """Тест успешного запроса без ретраев"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        
        result = test_fetcher._make_request_with_retries(
            session=mock_session,
            url="http://test.com",
            params={"test": "value"}
        )
        
        assert result["success"] == True
        assert result["response"] == mock_response
        assert mock_session.get.call_count == 1
    
    def test_make_request_with_retries_with_retry(self, test_fetcher):
        """Тест запроса с ретраем"""
        with patch('time.sleep') as mock_sleep:
            mock_session = Mock()
            
            # Первый ответ - 429, второй - успех
            mock_429 = Mock()
            mock_429.status_code = 429
            mock_429.text = "Rate limited"
            
            mock_success = Mock()
            mock_success.status_code = 200
            
            mock_session.get.side_effect = [mock_429, mock_success]
            
            result = test_fetcher._make_request_with_retries(
                session=mock_session,
                url="http://test.com"
            )
            
            assert result["success"] == True
            assert result["response"] == mock_success
            assert mock_session.get.call_count == 2
            assert mock_sleep.call_count == 1
    
    def test_make_request_with_retries_max_attempts(self, test_fetcher):
        """Тест исчерпания максимального количества попыток"""
        with patch('time.sleep') as mock_sleep:
            mock_session = Mock()
            
            # Все ответы - 429
            mock_429 = Mock()
            mock_429.status_code = 429
            mock_429.text = "Rate limited"
            mock_session.get.return_value = mock_429
            
            result = test_fetcher._make_request_with_retries(
                session=mock_session,
                url="http://test.com"
            )
            
            assert "error" in result
            assert isinstance(result["error"], NewsAPIError)
            assert result["error"].status_code == 429
            assert mock_session.get.call_count == 3  # max_retries
            assert mock_sleep.call_count == 2  # retries - 1
    
    def test_make_request_with_retries_network_error(self, test_fetcher):
        """Тест обработки сетевых ошибок"""
        with patch('time.sleep') as mock_sleep:
            mock_session = Mock()
            
            # Первый запрос - сетевая ошибка, второй - успех
            mock_session.get.side_effect = [
                requests.exceptions.ConnectionError("Network error"),
                Mock(status_code=200)
            ]
            
            result = test_fetcher._make_request_with_retries(
                session=mock_session,
                url="http://test.com"
            )
            
            assert result["success"] == True
            assert mock_session.get.call_count == 2
            assert mock_sleep.call_count == 1 