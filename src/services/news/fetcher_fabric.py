# src/services/news/fetcher_fabric.py

from typing import Dict, Type
from .fetchers.base import BaseFetcher
from .fetchers.thenewsapi_com import TheNewsAPIFetcher
from .fetchers.newsapi_org import NewsAPIFetcher
from ...config import get_settings
from ...logger import setup_logger


class FetcherFactory:
    """Фабрика для создания fetcher'ов новостей"""
    
    # Регистр доступных fetcher'ов
    _fetchers: Dict[str, Type[BaseFetcher]] = {
        "thenewsapi": TheNewsAPIFetcher,
        "newsapi": NewsAPIFetcher,
    }
    
    @classmethod
    def create_fetcher(cls, provider: str = None) -> BaseFetcher:
        """
        Создает fetcher на основе настройки NEWS_API_PROVIDER
        
        Args:
            provider: Название провайдера (опционально, берется из конфига)
            
        Returns:
            Экземпляр fetcher'а
            
        Raises:
            ValueError: Если провайдер не поддерживается
        """
        # Используем переданный провайдер или дефолтный
        if provider is None:
            try:
                settings = get_settings()
                provider = settings.NEWS_API_PROVIDER
            except Exception:
                # Если не можем получить настройки, используем дефолтный
                provider = "thenewsapi"
        
        if provider not in cls._fetchers:
            available_providers = ", ".join(cls._fetchers.keys())
            raise ValueError(
                f"Unsupported news provider: {provider}. "
                f"Available providers: {available_providers}"
            )
        
        fetcher_class = cls._fetchers[provider]
        return fetcher_class()
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Возвращает список доступных провайдеров"""
        return list(cls._fetchers.keys())
    
    @classmethod
    def register_fetcher(cls, name: str, fetcher_class: Type[BaseFetcher]) -> None:
        """
        Регистрирует новый fetcher
        
        Args:
            name: Название провайдера
            fetcher_class: Класс fetcher'а
        """
        cls._fetchers[name] = fetcher_class


def create_news_fetcher(provider: str = None) -> BaseFetcher:
    """
    Удобная функция для создания fetcher'а
    
    Args:
        provider: Название провайдера (опционально)
        
    Returns:
        Экземпляр fetcher'а
    """
    return FetcherFactory.create_fetcher(provider) 