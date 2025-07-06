# tests/test_news_module_isolation.py

import pytest
import os
from unittest.mock import patch

from src.services.news.fetcher_fabric import create_news_fetcher


class TestNewsModuleIsolation:
    """Тесты для проверки изоляции модуля новостей"""
    
    def test_create_news_fetcher_without_config_dependencies(self):
        """Тест что модуль новостей может работать без полных настроек"""
        # Убираем все переменные окружения кроме нужной
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'test_token'
        }, clear=True):
            # Создаем fetcher только с нужными параметрами
            fetcher = create_news_fetcher(
                provider="thenewsapi",
                api_token="test_token"
            )
            
            # Проверяем что fetcher создался успешно
            assert fetcher is not None
            assert fetcher.api_token == "test_token"
            assert fetcher.max_retries == 3  # дефолт
            assert fetcher.backoff_factor == 0.5  # дефолт
    
    def test_create_news_fetcher_without_google_openai_vars(self):
        """Тест что модуль новостей не зависит от Google/OpenAI переменных"""
        # Специально не устанавливаем GOOGLE_GSHEET_ID и OPENAI_API_KEY
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'test_token'
        }, clear=True):
            # Должен работать без ошибок
            fetcher = create_news_fetcher(
                provider="thenewsapi",
                api_token="isolated_token",
                max_retries=5,
                backoff_factor=1.0
            )
            
            assert fetcher.api_token == "isolated_token"
            assert fetcher.max_retries == 5
            assert fetcher.backoff_factor == 1.0
    
    def test_create_news_fetcher_missing_required_token(self):
        """Тест что модуль корректно требует только необходимые параметры"""
        # Не передаем API токен для thenewsapi
        with pytest.raises(ValueError) as exc_info:
            create_news_fetcher(provider="thenewsapi")
        
        assert "api_token is required for thenewsapi provider" in str(exc_info.value)
    
    def test_create_newsapi_fetcher_no_dependencies(self):
        """Тест что NewsAPI fetcher не требует дополнительных зависимостей"""
        # NewsAPI fetcher не требует параметров
        fetcher = create_news_fetcher(provider="newsapi")
        
        assert fetcher is not None
    
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