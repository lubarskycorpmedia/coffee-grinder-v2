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
    def get_available_providers(cls) -> list[str]:
        """Возвращает список доступных провайдеров"""
        return FetcherRegistry.get_available_providers()
    
    @classmethod
    def get_enabled_providers(cls) -> list[str]:
        """Возвращает список включенных провайдеров из конфига"""
        from src.config import get_news_providers_settings
        
        providers_settings = get_news_providers_settings()
        return list(providers_settings.get_enabled_providers().keys())


# Удобная функция для создания fetcher'а
def create_news_fetcher_from_config(provider: str) -> BaseFetcher:
    """
    Удобная функция для создания fetcher'а с настройками из конфига
    
    Args:
        provider: Название провайдера
        
    Returns:
        Экземпляр fetcher'а
    """
    return FetcherFactory.create_fetcher_from_config(provider) 