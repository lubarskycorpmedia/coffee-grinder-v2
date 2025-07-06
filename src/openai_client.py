# src/openai_client.py

import time
import random
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai.types import CreateEmbeddingResponse
import openai

from src.config import get_ai_settings
from src.logger import setup_logger


class OpenAIClientError(Exception):
    """Базовое исключение для ошибок OpenAI клиента"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, attempt: int = 1):
        self.message = message
        self.status_code = status_code
        self.attempt = attempt
        super().__init__(self.message)


class OpenAIClient:
    """Типизированная обёртка для OpenAI SDK с retry логикой"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 max_retries: int = 3,
                 backoff_factor: float = 2.0,
                 timeout: int = 60):
        """
        Инициализация OpenAI клиента
        
        Args:
            api_key: API ключ OpenAI (если None, берется из настроек)
            max_retries: Максимальное количество попыток при ошибках
            backoff_factor: Коэффициент для экспоненциального backoff
            timeout: Таймаут запросов в секундах
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self._logger = None
        
        # Получаем API ключ
        if api_key is None:
            settings = get_ai_settings()
            api_key = settings.OPENAI_API_KEY
        
        # Инициализируем клиент
        self.client = OpenAI(
            api_key=api_key,
            timeout=timeout
        )
    
    @property
    def logger(self):
        """Ленивое создание логгера"""
        if self._logger is None:
            self._logger = setup_logger(__name__)
        return self._logger
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Вычисляет время задержки для экспоненциального backoff"""
        base_delay = 1.0  # Базовая задержка в секундах
        max_delay = 60.0  # Максимальная задержка
        
        delay = base_delay * (self.backoff_factor ** attempt) + random.uniform(0, 1)
        return min(delay, max_delay)
    
    def _handle_openai_error(self, error: Exception, attempt: int) -> OpenAIClientError:
        """Обрабатывает ошибки OpenAI и возвращает унифицированное исключение"""
        if isinstance(error, openai.RateLimitError):
            return OpenAIClientError(
                f"Rate limit exceeded: {str(error)}", 
                status_code=429, 
                attempt=attempt
            )
        elif isinstance(error, openai.APITimeoutError):
            return OpenAIClientError(
                f"Request timeout: {str(error)}", 
                status_code=408, 
                attempt=attempt
            )
        elif isinstance(error, openai.APIConnectionError):
            return OpenAIClientError(
                f"Connection error: {str(error)}", 
                status_code=None, 
                attempt=attempt
            )
        elif isinstance(error, openai.AuthenticationError):
            return OpenAIClientError(
                f"Authentication error: {str(error)}", 
                status_code=401, 
                attempt=attempt
            )
        elif isinstance(error, openai.BadRequestError):
            return OpenAIClientError(
                f"Bad request: {str(error)}", 
                status_code=400, 
                attempt=attempt
            )
        else:
            return OpenAIClientError(
                f"OpenAI API error: {str(error)}", 
                status_code=getattr(error, 'status_code', None), 
                attempt=attempt
            )
    
    def create_chat_completion(self, 
                             messages: List[Dict[str, str]], 
                             model: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: Optional[int] = None) -> ChatCompletion:
        """
        Создает chat completion с retry логикой
        
        Args:
            messages: Список сообщений для чата
            model: Модель для использования (если None, берется из настроек)
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            
        Returns:
            ChatCompletion ответ
            
        Raises:
            OpenAIClientError: При ошибках API после всех попыток
        """
        if model is None:
            try:
                settings = get_ai_settings()
                model = settings.OPENAI_MODEL
            except Exception:
                model = "gpt-4o-mini"  # Fallback модель
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Creating chat completion, attempt {attempt + 1}/{self.max_retries}")
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                self.logger.info(f"Successfully created chat completion with {len(messages)} messages")
                return response
                
            except Exception as e:
                error = self._handle_openai_error(e, attempt + 1)
                last_error = error
                
                self.logger.warning(f"Chat completion failed: {error.message}")
                
                # Для rate limit и connection errors пытаемся повторить
                if (error.status_code in [429, 408] or error.status_code is None) and attempt < self.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    self.logger.info(f"Waiting {delay:.2f} seconds before retry...")
                    time.sleep(delay)
                    continue
                else:
                    # Для других ошибок или исчерпанных попыток - прерываем
                    break
        
        # Если дошли сюда, значит все попытки исчерпаны
        self.logger.error(f"Chat completion failed after {self.max_retries} attempts: {last_error.message}")
        raise last_error
    
    def create_embeddings(self, 
                         texts: Union[str, List[str]], 
                         model: Optional[str] = None) -> CreateEmbeddingResponse:
        """
        Создает embeddings с retry логикой
        
        Args:
            texts: Текст или список текстов для создания embeddings
            model: Модель для использования (если None, берется из настроек)
            
        Returns:
            CreateEmbeddingResponse ответ
            
        Raises:
            OpenAIClientError: При ошибках API после всех попыток
        """
        if model is None:
            try:
                settings = get_ai_settings()
                model = settings.OPENAI_EMBEDDING_MODEL
            except Exception:
                model = "text-embedding-3-small"  # Fallback модель
        
        # Приводим к списку для унификации
        if isinstance(texts, str):
            texts = [texts]
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Creating embeddings for {len(texts)} texts, attempt {attempt + 1}/{self.max_retries}")
                
                response = self.client.embeddings.create(
                    model=model,
                    input=texts
                )
                
                self.logger.info(f"Successfully created embeddings for {len(texts)} texts")
                return response
                
            except Exception as e:
                error = self._handle_openai_error(e, attempt + 1)
                last_error = error
                
                self.logger.warning(f"Embeddings creation failed: {error.message}")
                
                # Для rate limit и connection errors пытаемся повторить
                if (error.status_code in [429, 408] or error.status_code is None) and attempt < self.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    self.logger.info(f"Waiting {delay:.2f} seconds before retry...")
                    time.sleep(delay)
                    continue
                else:
                    # Для других ошибок или исчерпанных попыток - прерываем
                    break
        
        # Если дошли сюда, значит все попытки исчерпаны
        self.logger.error(f"Embeddings creation failed after {self.max_retries} attempts: {last_error.message}")
        raise last_error


def create_openai_client(api_key: Optional[str] = None,
                        max_retries: int = 3,
                        backoff_factor: float = 2.0,
                        timeout: int = 60) -> OpenAIClient:
    """
    Удобная функция для создания OpenAI клиента
    
    Args:
        api_key: API ключ OpenAI (если None, берется из настроек)
        max_retries: Максимальное количество попыток при ошибках
        backoff_factor: Коэффициент для экспоненциального backoff
        timeout: Таймаут запросов в секундах
        
    Returns:
        Экземпляр OpenAIClient
    """
    return OpenAIClient(
        api_key=api_key,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        timeout=timeout
    ) 