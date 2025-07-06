# src/services/news/fetcher_fabric.py

from typing import Dict, Type, Optional
from .fetchers.base import BaseFetcher
from .fetchers.thenewsapi_com import TheNewsAPIFetcher
from .fetchers.newsapi_org import NewsAPIFetcher
from src.logger import setup_logger


class FetcherFactory:
    """Фабрика для создания fetcher'ов новостей"""
    
    # Регистр доступных fetcher'ов
    _fetchers: Dict[str, Type[BaseFetcher]] = {
        "thenewsapi": TheNewsAPIFetcher,
        "newsapi": NewsAPIFetcher,
    }
    
    @classmethod
    def create_fetcher(cls, 
                      provider: str,
                      api_token: Optional[str] = None,
                      max_retries: Optional[int] = None,
                      backoff_factor: Optional[float] = None) -> BaseFetcher:
        """
        Создает fetcher на основе переданных параметров
        
        Args:
            provider: Название провайдера (обязательно)
            api_token: API токен (обязательно для thenewsapi)
            max_retries: Максимальное количество попыток (опционально, по умолчанию 3)
            backoff_factor: Коэффициент backoff (опционально, по умолчанию 0.5)
            
        Returns:
            Экземпляр fetcher'а
            
        Raises:
            ValueError: Если провайдер не поддерживается или отсутствуют обязательные параметры
        """
        if provider not in cls._fetchers:
            available_providers = ", ".join(cls._fetchers.keys())
            raise ValueError(
                f"Unsupported news provider: {provider}. "
                f"Available providers: {available_providers}"
            )
        
        fetcher_class = cls._fetchers[provider]
        
        # Создаем fetcher с нужными параметрами
        if provider == "thenewsapi":
            if api_token is None:
                raise ValueError("api_token is required for thenewsapi provider")
            
            # Используем дефолтные значения если не переданы
            max_retries = max_retries or 3
            backoff_factor = backoff_factor or 0.5
            
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
    def create_fetcher_with_config(cls, 
                                  provider: Optional[str] = None,
                                  api_token: Optional[str] = None,
                                  max_retries: Optional[int] = None,
                                  backoff_factor: Optional[float] = None) -> BaseFetcher:
        """
        Создает fetcher с получением настроек из конфига (для обратной совместимости)
        
        Args:
            provider: Название провайдера (опционально, берется из конфига)
            api_token: API токен (опционально, берется из конфига)
            max_retries: Максимальное количество попыток (опционально, берется из конфига)
            backoff_factor: Коэффициент backoff (опционально, берется из конфига)
            
        Returns:
            Экземпляр fetcher'а
            
        Raises:
            ValueError: Если провайдер не поддерживается или не удается получить настройки
        """
        from src.config import get_news_settings
        
        # Используем переданный провайдер или дефолтный
        if provider is None:
            try:
                settings = get_news_settings()
                provider = settings.NEWS_API_PROVIDER
            except Exception:
                # Если не можем получить настройки, используем дефолтный
                provider = "thenewsapi"
        
        # Создаем fetcher с нужными параметрами
        if provider == "thenewsapi":
            # Проверяем что API токен обязательно есть
            if api_token is None:
                try:
                    settings = get_news_settings()
                    api_token = settings.THENEWSAPI_API_TOKEN
                except Exception as e:
                    raise ValueError(f"Cannot get news settings for {provider}: {e}")
            
            # Получаем остальные настройки если не переданы
            if max_retries is None or backoff_factor is None:
                try:
                    settings = get_news_settings()
                    if max_retries is None:
                        max_retries = settings.MAX_RETRIES
                    if backoff_factor is None:
                        backoff_factor = settings.BACKOFF_FACTOR
                except Exception:
                    # Если не можем получить настройки, используем дефолтные
                    max_retries = max_retries or 3
                    backoff_factor = backoff_factor or 0.5
            
            return cls.create_fetcher(
                provider=provider,
                api_token=api_token,
                max_retries=max_retries,
                backoff_factor=backoff_factor
            )
        
        else:
            return cls.create_fetcher(provider=provider)
    
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


def create_news_fetcher(provider: str,
                       api_token: Optional[str] = None,
                       max_retries: Optional[int] = None,
                       backoff_factor: Optional[float] = None) -> BaseFetcher:
    """
    Удобная функция для создания fetcher'а без зависимости от настроек
    
    Args:
        provider: Название провайдера (обязательно)
        api_token: API токен (обязательно для thenewsapi)
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


def create_news_fetcher_with_config(provider: Optional[str] = None,
                                   api_token: Optional[str] = None,
                                   max_retries: Optional[int] = None,
                                   backoff_factor: Optional[float] = None) -> BaseFetcher:
    """
    Удобная функция для создания fetcher'а с получением настроек из конфига
    
    Args:
        provider: Название провайдера (опционально)
        api_token: API токен (опционально)
        max_retries: Максимальное количество попыток (опционально)
        backoff_factor: Коэффициент backoff (опционально)
        
    Returns:
        Экземпляр fetcher'а
    """
    return FetcherFactory.create_fetcher_with_config(
        provider=provider,
        api_token=api_token,
        max_retries=max_retries,
        backoff_factor=backoff_factor
    ) 