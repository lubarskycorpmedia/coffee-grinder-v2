from abc import ABC, ABCMeta, abstractmethod
from typing import Dict, Any, Optional, Type, ClassVar
from datetime import datetime


class NewsAPIError(Exception):
    """Исключение для ошибок API новостей"""
    def __init__(self, message: str, status_code: Optional[int] = None, retry_count: int = 0):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.retry_count = retry_count
        self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        return f"NewsAPIError: {self.message} (status: {self.status_code}, retries: {self.retry_count})"


class FetcherRegistry:
    """Реестр для автоматической регистрации fetcher'ов"""
    _fetchers: Dict[str, Type['BaseFetcher']] = {}
    
    @classmethod
    def register(cls, provider_name: str, fetcher_class: Type['BaseFetcher']):
        """Регистрирует fetcher для провайдера"""
        cls._fetchers[provider_name] = fetcher_class
    
    @classmethod
    def get_fetcher_class(cls, provider_name: str) -> Optional[Type['BaseFetcher']]:
        """Получает класс fetcher'а по имени провайдера"""
        return cls._fetchers.get(provider_name)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Возвращает список доступных провайдеров"""
        return list(cls._fetchers.keys())


class FetcherMeta(ABCMeta):
    """Метакласс для автоматической регистрации fetcher'ов, наследующий от ABCMeta"""
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)
        
        # Регистрируем только конкретные fetcher'ы (не базовый класс)
        if bases and hasattr(cls, 'PROVIDER_NAME') and cls.PROVIDER_NAME:
            provider_name = cls.PROVIDER_NAME
            FetcherRegistry.register(provider_name, cls)
        
        return cls


class BaseFetcher(ABC, metaclass=FetcherMeta):
    """Базовый абстрактный класс для всех fetchers новостей"""
    
    # Каждый fetcher должен определить имя провайдера
    PROVIDER_NAME: ClassVar[str] = ""
    
    def __init__(self, provider_settings: 'BaseProviderSettings'):
        """
        Стандартный конструктор для всех fetcher'ов
        
        Args:
            provider_settings: Настройки провайдера из конфига
        """
        self.provider_settings = provider_settings
        self.max_retries = provider_settings.max_retries
        self.backoff_factor = provider_settings.backoff_factor
        self.timeout = provider_settings.timeout
        self.enabled = provider_settings.enabled
    
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
    
    @abstractmethod
    def fetch_news(self, 
                   query: Optional[str] = None,
                   category: Optional[str] = None,
                   language: Optional[str] = None,
                   limit: int = 50,
                   **kwargs) -> Dict[str, Any]:
        """
        Универсальный метод для получения новостей
        
        Args:
            query: Поисковый запрос
            category: Категория новостей  
            language: Язык новостей (опционально)
            limit: Максимальное количество новостей
            **kwargs: Дополнительные параметры специфичные для провайдера
            
        Returns:
            Dict с результатами в стандартном формате:
            {
                "articles": [
                    {
                        "title": "...",
                        "description": "...",
                        "url": "...",
                        "published_at": "...",
                        "source": "...",
                        "category": "...",
                        "language": "..."
                    }
                ]
            }
            или {"error": NewsAPIError} в случае ошибки
        """
        pass
    
    @classmethod
    def create_from_config(cls, provider_settings: 'BaseProviderSettings') -> 'BaseFetcher':
        """
        Создает экземпляр fetcher'а из настроек
        Может быть переопределен в дочерних классах для специфической логики
        
        Args:
            provider_settings: Настройки провайдера
            
        Returns:
            Экземпляр fetcher'а
        """
        return cls(provider_settings) 