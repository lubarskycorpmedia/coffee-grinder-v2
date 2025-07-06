# src/services/news/fetcher_fabric.py

from typing import Dict, Type, Optional
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
    def create_fetcher(cls, 
                      provider: Optional[str] = None,
                      api_token: Optional[str] = None,
                      max_retries: Optional[int] = None,
                      backoff_factor: Optional[float] = None) -> BaseFetcher:
        """
        Создает fetcher на основе настройки NEWS_API_PROVIDER
        
        Args:
            provider: Название провайдера (опционально, берется из конфига)
            api_token: API токен (опционально, берется из конфига)
            max_retries: Максимальное количество попыток (опционально, берется из конфига)
            backoff_factor: Коэффициент backoff (опционально, берется из конфига)
            
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
        
        # Создаем fetcher с нужными параметрами
        if provider == "thenewsapi":
            # Получаем настройки если не переданы
            if api_token is None or max_retries is None or backoff_factor is None:
                try:
                    settings = get_settings()
                    api_token = api_token or settings.THENEWSAPI_API_TOKEN
                    max_retries = max_retries or settings.MAX_RETRIES
                    backoff_factor = backoff_factor or settings.BACKOFF_FACTOR
                except Exception as e:
                    raise ValueError(f"Cannot get settings for {provider}: {e}")
            
            return fetcher_class(
                api_token=api_token,
                max_retries=max_retries,
                backoff_factor=backoff_factor
            )
        
        elif provider == "newsapi":
            # NewsAPI fetcher пока не требует параметров
            return fetcher_class()
        
        else:
            # Для других fetcher'ов пока используем базовый конструктор
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


def create_news_fetcher(provider: Optional[str] = None,
                       api_token: Optional[str] = None,
                       max_retries: Optional[int] = None,
                       backoff_factor: Optional[float] = None) -> BaseFetcher:
    """
    Удобная функция для создания fetcher'а
    
    Args:
        provider: Название провайдера (опционально)
        api_token: API токен (опционально)
        max_retries: Максимальное количество попыток (опционально)
        backoff_factor: Коэффициент backoff (опционально)
        
    Returns:
        Экземпляр fetcher'а
    """
    return FetcherFactory.create_fetcher(
        provider=provider,
        api_token=api_token,
        max_retries=max_retries,
        backoff_factor=backoff_factor
    ) 