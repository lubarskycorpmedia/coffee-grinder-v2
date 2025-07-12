# tests/test_news_module_isolation.py

import pytest
import os
from unittest.mock import patch, MagicMock

from src.services.news.fetcher_fabric import FetcherFactory, create_news_fetcher_from_config


class TestNewsModuleIsolation:
    """Тесты для проверки изоляции модуля новостей"""
    
    def test_fetcher_factory_available_providers(self):
        """Тест что фабрика возвращает доступные провайдеры"""
        available_providers = FetcherFactory.get_available_providers()
        
        # Проверяем что зарегистрированы оба провайдера
        assert "thenewsapi" in available_providers
        assert "newsapi" in available_providers
        assert len(available_providers) >= 2
    
    @patch('src.config.get_news_providers_settings')
    def test_create_fetcher_from_config_success(self, mock_get_settings):
        """Тест успешного создания fetcher'а из конфига"""
        # Создаем реальные настройки
        from src.config import TheNewsAPISettings
        
        mock_settings = MagicMock()
        mock_provider_settings = TheNewsAPISettings(
            api_token="test_token",
            enabled=True,
            max_retries=3,
            backoff_factor=2.0
        )
        
        mock_settings.get_provider_settings.return_value = mock_provider_settings
        mock_get_settings.return_value = mock_settings
        
        # Создаем fetcher
        fetcher = create_news_fetcher_from_config("thenewsapi")
        
        # Проверяем что fetcher создался
        assert fetcher is not None
        assert fetcher.PROVIDER_NAME == "thenewsapi"
    
    @patch('src.config.get_news_providers_settings')
    def test_create_fetcher_provider_not_found(self, mock_get_settings):
        """Тест обработки случая когда провайдер не найден в конфиге"""
        mock_settings = MagicMock()
        mock_settings.get_provider_settings.return_value = None
        mock_get_settings.return_value = mock_settings
        
        with pytest.raises(ValueError) as exc_info:
            create_news_fetcher_from_config("thenewsapi")
        
        assert "Provider 'thenewsapi' not found in configuration" in str(exc_info.value)
    
    @patch('src.config.get_news_providers_settings')
    def test_create_fetcher_provider_disabled(self, mock_get_settings):
        """Тест обработки случая когда провайдер отключен"""
        mock_settings = MagicMock()
        mock_provider_settings = MagicMock()
        mock_provider_settings.enabled = False
        
        mock_settings.get_provider_settings.return_value = mock_provider_settings
        mock_get_settings.return_value = mock_settings
        
        with pytest.raises(ValueError) as exc_info:
            create_news_fetcher_from_config("thenewsapi")
        
        assert "Provider 'thenewsapi' is disabled in configuration" in str(exc_info.value)
    
    def test_create_fetcher_unsupported_provider(self):
        """Тест обработки неподдерживаемого провайдера"""
        with pytest.raises(ValueError) as exc_info:
            create_news_fetcher_from_config("unsupported_provider")
        
        assert "Unsupported news provider: unsupported_provider" in str(exc_info.value)
        assert "Available providers:" in str(exc_info.value)
    
    @patch('src.config.get_news_providers_settings')
    def test_create_default_fetcher(self, mock_get_settings):
        """Тест создания дефолтного fetcher'а"""
        from src.config import TheNewsAPISettings
        
        mock_settings = MagicMock()
        mock_settings.default_provider = "thenewsapi"
        
        mock_provider_settings = TheNewsAPISettings(
            api_token="test_token",
            enabled=True
        )
        
        mock_settings.get_provider_settings.return_value = mock_provider_settings
        mock_get_settings.return_value = mock_settings
        
        fetcher = FetcherFactory.create_default_fetcher()
        
        assert fetcher is not None
        assert fetcher.PROVIDER_NAME == "thenewsapi"
    
    @patch('src.config.get_news_providers_settings')
    def test_create_fetcher_with_fallback(self, mock_get_settings):
        """Тест создания fetcher'а с fallback"""
        from src.config import TheNewsAPISettings
        
        mock_settings = MagicMock()
        mock_settings.default_provider = "thenewsapi"
        mock_settings.fallback_providers = ["newsapi"]
        
        # Первый провайдер не найден
        def mock_get_provider_settings(provider):
            if provider == "preferred_provider":
                return None
            elif provider == "thenewsapi":
                return TheNewsAPISettings(
                    api_token="test_token",
                    enabled=True
                )
            return None
        
        mock_settings.get_provider_settings.side_effect = mock_get_provider_settings
        mock_get_settings.return_value = mock_settings
        
        fetcher = FetcherFactory.create_fetcher_with_fallback("preferred_provider")
        
        assert fetcher is not None
        assert fetcher.PROVIDER_NAME == "thenewsapi"
    
    def test_news_module_imports_isolation(self):
        """Тест что модуль новостей не импортирует ненужные зависимости на уровне модуля"""
        # Проверяем что можем импортировать модуль без полных настроек
        from src.services.news.fetcher_fabric import FetcherFactory
        from src.services.news.fetchers.thenewsapi_com import TheNewsAPIFetcher
        from src.services.news.fetchers.newsapi_org import NewsAPIFetcher
        
        # Все импорты должны работать
        assert FetcherFactory is not None
        assert TheNewsAPIFetcher is not None
        assert NewsAPIFetcher is not None
    
    def test_fetcher_registry_auto_registration(self):
        """Тест автоматической регистрации провайдеров через метакласс"""
        from src.services.news.fetchers.base import FetcherRegistry
        
        # Проверяем что провайдеры автоматически зарегистрированы
        thenewsapi_class = FetcherRegistry.get_fetcher_class("thenewsapi")
        newsapi_class = FetcherRegistry.get_fetcher_class("newsapi")
        
        assert thenewsapi_class is not None
        assert newsapi_class is not None
        assert thenewsapi_class.PROVIDER_NAME == "thenewsapi"
        assert newsapi_class.PROVIDER_NAME == "newsapi" 