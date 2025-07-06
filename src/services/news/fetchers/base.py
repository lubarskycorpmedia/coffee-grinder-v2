from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class NewsAPIError:
    """Класс для представления ошибок API новостей"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, retry_count: int = 0):
        self.message = message
        self.status_code = status_code
        self.retry_count = retry_count
        self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        return f"NewsAPIError: {self.message} (status: {self.status_code}, retries: {self.retry_count})"


class BaseFetcher(ABC):
    """Базовый абстрактный класс для всех fetchers новостей"""
    
    @abstractmethod
    def fetch_headlines(self, **kwargs) -> Dict[str, Any]:
        """Получает заголовки новостей"""
        pass
    
    @abstractmethod
    def fetch_all_news(self, **kwargs) -> Dict[str, Any]:
        """Получает все новости по поиску"""
        pass
    
    @abstractmethod
    def fetch_top_stories(self, **kwargs) -> Dict[str, Any]:
        """Получает топ новости"""
        pass
    
    @abstractmethod
    def get_sources(self, **kwargs) -> Dict[str, Any]:
        """Получает список доступных источников"""
        pass 