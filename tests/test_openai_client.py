# tests/test_openai_client.py

import pytest
from unittest.mock import Mock, patch, MagicMock
import openai

from src.openai_client import OpenAIClient, OpenAIClientError, create_openai_client


class TestOpenAIClient:
    """Тесты для OpenAIClient"""
    
    @pytest.fixture
    def mock_settings(self):
        """Мокает settings для тестов"""
        mock_settings = MagicMock()
        mock_settings.OPENAI_API_KEY = "test_api_key"
        mock_settings.LLM_MODEL = "gpt-4o-mini"
        mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"
        return mock_settings
    
    @pytest.fixture
    def client(self, mock_settings):
        """Создает экземпляр клиента для тестов"""
        with patch('src.openai_client.get_settings', return_value=mock_settings):
            client = OpenAIClient(max_retries=3, backoff_factor=2.0)
            client._logger = Mock()  # Мокаем логгер
            return client
    
    def test_client_initialization_with_api_key(self):
        """Тест инициализации клиента с явным API ключом"""
        client = OpenAIClient(api_key="explicit_key", max_retries=5, backoff_factor=1.5)
        
        assert client.max_retries == 5
        assert client.backoff_factor == 1.5
        assert client.timeout == 60  # дефолтный
        assert client.client.api_key == "explicit_key"
    
    def test_client_initialization_with_settings(self, mock_settings):
        """Тест инициализации клиента с настройками из config"""
        with patch('src.openai_client.get_settings', return_value=mock_settings):
            client = OpenAIClient()
            
            assert client.max_retries == 3  # дефолтный
            assert client.backoff_factor == 2.0  # дефолтный
            assert client.client.api_key == "test_api_key"
    
    def test_exponential_backoff_calculation(self, client):
        """Тест расчета экспоненциального backoff"""
        delay_0 = client._exponential_backoff(0)
        delay_1 = client._exponential_backoff(1)
        delay_2 = client._exponential_backoff(2)
        
        # Базовая проверка что задержки увеличиваются
        assert delay_0 < delay_1 < delay_2
        
        # Проверяем что не превышает максимум
        delay_large = client._exponential_backoff(10)
        assert delay_large <= 60.0
    
    def test_handle_openai_error_rate_limit(self, client):
        """Тест обработки ошибки rate limit"""
        rate_limit_error = openai.RateLimitError("Rate limit exceeded", response=Mock(), body=None)
        
        handled_error = client._handle_openai_error(rate_limit_error, 1)
        
        assert isinstance(handled_error, OpenAIClientError)
        assert handled_error.status_code == 429
        assert "rate limit" in handled_error.message.lower()
        assert handled_error.attempt == 1
    
    def test_handle_openai_error_timeout(self, client):
        """Тест обработки ошибки timeout"""
        timeout_error = openai.APITimeoutError("Request timeout")
        
        handled_error = client._handle_openai_error(timeout_error, 2)
        
        assert isinstance(handled_error, OpenAIClientError)
        assert handled_error.status_code == 408
        assert "timeout" in handled_error.message.lower()
        assert handled_error.attempt == 2
    
    def test_handle_openai_error_authentication(self, client):
        """Тест обработки ошибки аутентификации"""
        auth_error = openai.AuthenticationError("Invalid API key", response=Mock(), body=None)
        
        handled_error = client._handle_openai_error(auth_error, 1)
        
        assert isinstance(handled_error, OpenAIClientError)
        assert handled_error.status_code == 401
        assert "authentication" in handled_error.message.lower()
    
    def test_successful_chat_completion(self, client, mock_settings):
        """Тест успешного создания chat completion"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        with patch.object(client.client.chat.completions, 'create', return_value=mock_response), \
             patch('src.openai_client.get_settings', return_value=mock_settings):
            messages = [{"role": "user", "content": "Test message"}]
            
            result = client.create_chat_completion(messages, temperature=0.5)
            
            assert result == mock_response
            client.client.chat.completions.create.assert_called_once_with(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.5,
                max_tokens=None
            )
    
    def test_chat_completion_with_custom_model(self, client):
        """Тест chat completion с кастомной моделью"""
        mock_response = Mock()
        
        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            messages = [{"role": "user", "content": "Test"}]
            
            result = client.create_chat_completion(messages, model="gpt-4")
            
            assert result == mock_response
            client.client.chat.completions.create.assert_called_once_with(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=None
            )
    
    def test_chat_completion_rate_limit_with_retry(self, client):
        """Тест chat completion с rate limit и успешным retry"""
        mock_response = Mock()
        
        with patch.object(client.client.chat.completions, 'create') as mock_create, \
             patch('time.sleep') as mock_sleep:
            
            # Первая попытка - rate limit, вторая - успех
            mock_create.side_effect = [
                openai.RateLimitError("Rate limit", response=Mock(), body=None),
                mock_response
            ]
            
            messages = [{"role": "user", "content": "Test"}]
            result = client.create_chat_completion(messages, model="gpt-4o-mini")  # Явно указываем модель
            
            assert result == mock_response
            assert mock_create.call_count == 2
            assert mock_sleep.call_count == 1
    
    def test_chat_completion_max_retries_exceeded(self, client):
        """Тест chat completion когда исчерпаны все попытки"""
        with patch.object(client.client.chat.completions, 'create') as mock_create, \
             patch('time.sleep') as mock_sleep:
            
            # Все попытки - rate limit
            mock_create.side_effect = openai.RateLimitError("Rate limit", response=Mock(), body=None)
            
            messages = [{"role": "user", "content": "Test"}]
            
            with pytest.raises(OpenAIClientError) as exc_info:
                client.create_chat_completion(messages, model="gpt-4o-mini")  # Явно указываем модель
            
            assert exc_info.value.status_code == 429
            assert mock_create.call_count == 3
            assert mock_sleep.call_count == 2
    
    def test_chat_completion_authentication_error_no_retry(self, client):
        """Тест что authentication error не ретраится"""
        with patch.object(client.client.chat.completions, 'create') as mock_create, \
             patch('time.sleep') as mock_sleep:
            
            mock_create.side_effect = openai.AuthenticationError("Invalid key", response=Mock(), body=None)
            
            messages = [{"role": "user", "content": "Test"}]
            
            with pytest.raises(OpenAIClientError) as exc_info:
                client.create_chat_completion(messages, model="gpt-4o-mini")  # Явно указываем модель
            
            assert exc_info.value.status_code == 401
            assert mock_create.call_count == 1  # Только одна попытка
            assert mock_sleep.call_count == 0  # Без задержек
    
    def test_successful_embeddings_creation(self, client, mock_settings):
        """Тест успешного создания embeddings"""
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        
        with patch.object(client.client.embeddings, 'create', return_value=mock_response), \
             patch('src.openai_client.get_settings', return_value=mock_settings):
            texts = ["Test text 1", "Test text 2"]
            
            result = client.create_embeddings(texts)
            
            assert result == mock_response
            client.client.embeddings.create.assert_called_once_with(
                model="text-embedding-3-small",
                input=texts
            )
    
    def test_embeddings_creation_single_text(self, client, mock_settings):
        """Тест создания embeddings для одного текста"""
        mock_response = Mock()
        
        with patch.object(client.client.embeddings, 'create', return_value=mock_response), \
             patch('src.openai_client.get_settings', return_value=mock_settings):
            text = "Single test text"
            
            result = client.create_embeddings(text)
            
            assert result == mock_response
            client.client.embeddings.create.assert_called_once_with(
                model="text-embedding-3-small",
                input=[text]  # Должен быть преобразован в список
            )
    
    def test_embeddings_creation_with_custom_model(self, client):
        """Тест создания embeddings с кастомной моделью"""
        mock_response = Mock()
        
        with patch.object(client.client.embeddings, 'create', return_value=mock_response):
            texts = ["Test text"]
            
            result = client.create_embeddings(texts, model="text-embedding-ada-002")
            
            assert result == mock_response
            client.client.embeddings.create.assert_called_once_with(
                model="text-embedding-ada-002",
                input=texts
            )
    
    def test_embeddings_rate_limit_with_retry(self, client):
        """Тест embeddings с rate limit и успешным retry"""
        mock_response = Mock()
        
        with patch.object(client.client.embeddings, 'create') as mock_create, \
             patch('time.sleep') as mock_sleep:
            
            # Первая попытка - rate limit, вторая - успех
            mock_create.side_effect = [
                openai.RateLimitError("Rate limit", response=Mock(), body=None),
                mock_response
            ]
            
            texts = ["Test text"]
            result = client.create_embeddings(texts, model="text-embedding-3-small")  # Явно указываем модель
            
            assert result == mock_response
            assert mock_create.call_count == 2
            assert mock_sleep.call_count == 1
    
    def test_embeddings_max_retries_exceeded(self, client):
        """Тест embeddings когда исчерпаны все попытки"""
        with patch.object(client.client.embeddings, 'create') as mock_create, \
             patch('time.sleep') as mock_sleep:
            
            # Все попытки - connection error
            mock_create.side_effect = openai.APIConnectionError(request=Mock())
            
            texts = ["Test text"]
            
            with pytest.raises(OpenAIClientError) as exc_info:
                client.create_embeddings(texts, model="text-embedding-3-small")  # Явно указываем модель
            
            assert "connection" in exc_info.value.message.lower()
            assert mock_create.call_count == 3
            assert mock_sleep.call_count == 2
    
    def test_create_openai_client_convenience_function(self):
        """Тест удобной функции create_openai_client"""
        client = create_openai_client(
            api_key="test_key",
            max_retries=5,
            backoff_factor=1.5,
            timeout=30
        )
        
        assert isinstance(client, OpenAIClient)
        assert client.max_retries == 5
        assert client.backoff_factor == 1.5
        assert client.timeout == 30
        assert client.client.api_key == "test_key" 