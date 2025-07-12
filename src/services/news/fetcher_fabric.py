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
            backoff_factor: Коэффициент backoff (опционально, по умолчанию 2.0)
            
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
            backoff_factor = backoff_factor or 2.0
            
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
    def create_fetcher_from_config(cls, provider: str) -> BaseFetcher:
        """
        Создает fetcher с настройками из конфига для конкретного провайдера
        
        Args:
            provider: Название провайдера
            
        Returns:
            Экземпляр fetcher'а
            
        Raises:
            ValueError: Если провайдер не поддерживается или не настроен
        """
        from src.config import get_news_providers_settings
        
        providers_settings = get_news_providers_settings()
        provider_settings = providers_settings.get_provider_settings(provider)
        
        if provider_settings is None:
            raise ValueError(f"Provider '{provider}' not found in configuration")
        
        if not provider_settings.enabled:
            raise ValueError(f"Provider '{provider}' is disabled in configuration")
        
        # Создаем fetcher с настройками из конфига
        if provider == "thenewsapi":
            from src.config import TheNewsAPISettings
            if isinstance(provider_settings, TheNewsAPISettings):
                return cls.create_fetcher(
                    provider=provider,
                    api_token=provider_settings.api_token,
                    max_retries=provider_settings.max_retries,
                    backoff_factor=provider_settings.backoff_factor
                )
            else:
                raise ValueError(f"Invalid settings type for provider '{provider}'")
        
        elif provider == "newsapi":
            from src.config import NewsAPISettings
            if isinstance(provider_settings, NewsAPISettings):
                # NewsAPI fetcher пока не требует параметров
                return cls.create_fetcher(provider=provider)
            else:
                raise ValueError(f"Invalid settings type for provider '{provider}'")
        
        else:
            return cls.create_fetcher(provider=provider)
    
    @classmethod
    def create_default_fetcher(cls) -> BaseFetcher:
        """
        Создает fetcher с дефолтными настройками из конфига
        
        Returns:
            Экземпляр fetcher'а
        """
        from src.config import get_news_providers_settings
        
        providers_settings = get_news_providers_settings()
        default_provider = providers_settings.default_provider
        
        return cls.create_fetcher_from_config(default_provider)
    
    @classmethod
    def create_fetcher_with_fallback(cls, preferred_provider: Optional[str] = None) -> BaseFetcher:
        """
        Создает fetcher с поддержкой fallback провайдеров
        
        Args:
            preferred_provider: Предпочтительный провайдер (опционально)
            
        Returns:
            Экземпляр fetcher'а
        """
        from src.config import get_news_providers_settings
        
        providers_settings = get_news_providers_settings()
        
        # Список провайдеров для попытки создания
        providers_to_try = []
        
        if preferred_provider:
            providers_to_try.append(preferred_provider)
        
        # Добавляем дефолтный провайдер
        if providers_settings.default_provider not in providers_to_try:
            providers_to_try.append(providers_settings.default_provider)
        
        # Добавляем fallback провайдеры
        for fallback_provider in providers_settings.fallback_providers:
            if fallback_provider not in providers_to_try:
                providers_to_try.append(fallback_provider)
        
        # Пытаемся создать fetcher для каждого провайдера
        last_error = None
        for provider in providers_to_try:
            try:
                return cls.create_fetcher_from_config(provider)
            except Exception as e:
                last_error = e
                continue
        
        # Если не удалось создать ни одного fetcher'а
        raise ValueError(f"Failed to create any fetcher. Last error: {last_error}")
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Возвращает список доступных провайдеров"""
        return list(cls._fetchers.keys())
    
    @classmethod
    def get_enabled_providers(cls) -> list[str]:
        """Возвращает список включенных провайдеров из конфига"""
        from src.config import get_news_providers_settings
        
        providers_settings = get_news_providers_settings()
        return list(providers_settings.get_enabled_providers().keys())
    
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


def create_news_fetcher_from_config(provider: str) -> BaseFetcher:
    """
    Удобная функция для создания fetcher'а с настройками из конфига
    
    Args:
        provider: Название провайдера
        
    Returns:
        Экземпляр fetcher'а
    """
    return FetcherFactory.create_fetcher_from_config(provider)


def create_default_news_fetcher() -> BaseFetcher:
    """
    Удобная функция для создания дефолтного fetcher'а
    
    Returns:
        Экземпляр fetcher'а
    """
    return FetcherFactory.create_default_fetcher()


def create_news_fetcher_with_fallback(preferred_provider: Optional[str] = None) -> BaseFetcher:
    """
    Удобная функция для создания fetcher'а с поддержкой fallback
    
    Args:
        preferred_provider: Предпочтительный провайдер (опционально)
        
    Returns:
        Экземпляр fetcher'а
    """
    return FetcherFactory.create_fetcher_with_fallback(preferred_provider) 