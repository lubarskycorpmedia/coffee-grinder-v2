# src/services/news/fetcher_fabric.py

from typing import Dict, Type, Optional
from .fetchers.base import BaseFetcher, FetcherRegistry
from src.logger import setup_logger


class FetcherFactory:
    """Фабрика для создания fetcher'ов новостей с автоматической регистрацией"""
    
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
        
        # Получаем класс fetcher'а из реестра
        fetcher_class = FetcherRegistry.get_fetcher_class(provider)
        if fetcher_class is None:
            available_providers = ", ".join(FetcherRegistry.get_available_providers())
            raise ValueError(
                f"Unsupported news provider: {provider}. "
                f"Available providers: {available_providers}"
            )
        
        # Получаем настройки провайдера
        providers_settings = get_news_providers_settings()
        provider_settings = providers_settings.get_provider_settings(provider)
        
        if provider_settings is None:
            raise ValueError(f"Provider '{provider}' not found in configuration")
        
        if not provider_settings.enabled:
            raise ValueError(f"Provider '{provider}' is disabled in configuration")
        
        # Создаем fetcher используя метод create_from_config
        return fetcher_class.create_from_config(provider_settings)
    
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
        return FetcherRegistry.get_available_providers()
    
    @classmethod
    def get_enabled_providers(cls) -> list[str]:
        """Возвращает список включенных провайдеров из конфига"""
        from src.config import get_news_providers_settings
        
        providers_settings = get_news_providers_settings()
        return list(providers_settings.get_enabled_providers().keys())


# Удобные функции для создания fetcher'ов
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