# tests/test_config.py

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError
from src.config import Settings, get_settings, get_env_file


class TestSettings:
    """Тесты для класса Settings."""
    
    def test_topics_list_property(self):
        """Тест разбора строки TOPICS в список."""
        settings = Settings(
            THENEWSAPI_API_TOKEN="test_token",
            OPENAI_API_KEY="test_key",
            GOOGLE_GSHEET_ID="test_id",
            GOOGLE_ACCOUNT_EMAIL="test@email.com",
            GOOGLE_ACCOUNT_KEY="test_key"
        )
        
        expected_topics = [
            "us", "left_reaction", "ukraine", "world", 
            "tech", "crazy", "marasmus", "coffee_grounds"
        ]
        assert settings.topics_list == expected_topics
    
    def test_topics_list_with_spaces(self):
        """Тест обработки пробелов в TOPICS."""
        settings = Settings(
            THENEWSAPI_API_TOKEN="test_token",
            OPENAI_API_KEY="test_key", 
            GOOGLE_GSHEET_ID="test_id",
            GOOGLE_ACCOUNT_EMAIL="test@email.com",
            GOOGLE_ACCOUNT_KEY="test_key"
        )
        settings.TOPICS = "tech, world , ukraine"
        
        expected_topics = ["tech", "world", "ukraine"]
        assert settings.topics_list == expected_topics
    
    def test_default_values(self):
        """Тест значений по умолчанию."""
        settings = Settings(
            THENEWSAPI_API_TOKEN="test_token",
            OPENAI_API_KEY="test_key",
            GOOGLE_GSHEET_ID="test_id", 
            GOOGLE_ACCOUNT_EMAIL="test@email.com",
            GOOGLE_ACCOUNT_KEY="test_key"
        )
        
        assert settings.ASK_NEWS_COUNT == 10
        assert settings.DAYS_BACK == 1
        assert settings.DEDUP_THRESHOLD == 0.85
        assert settings.MAX_RETRIES == 3
        assert settings.BACKOFF_FACTOR == 2.0
        assert settings.LOG_LEVEL == "INFO"
        assert settings.LLM_MODEL == "gpt-4o-mini"
        assert settings.EMBEDDING_MODEL == "text-embedding-3-small"
    
    def test_ranking_prompt_template(self):
        """Тест наличия шаблона промпта для ранжирования."""
        settings = Settings(
            THENEWSAPI_API_TOKEN="test_token",
            OPENAI_API_KEY="test_key",
            GOOGLE_GSHEET_ID="test_id",
            GOOGLE_ACCOUNT_EMAIL="test@email.com", 
            GOOGLE_ACCOUNT_KEY="test_key"
        )
        
        assert "title" in settings.RANKING_PROMPT_TEMPLATE
        assert "description" in settings.RANKING_PROMPT_TEMPLATE
        assert "popularity" in settings.RANKING_PROMPT_TEMPLATE
        assert "1 до 5" in settings.RANKING_PROMPT_TEMPLATE
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_required_fields(self):
        """Тест обработки отсутствующих обязательных полей."""
        with pytest.raises(ValidationError):
            Settings()
    
    def test_ci_environment(self):
        """Тест настройки для CI окружения."""
        with patch.dict(os.environ, {"CI": "true"}, clear=True):
            # Проверяем, что функция get_env_file возвращает None при CI=true
            assert get_env_file() is None
    
    def test_normal_environment(self):
        """Тест настройки для обычного окружения."""
        with patch.dict(os.environ, {}, clear=True):
            # Проверяем, что функция get_env_file возвращает .env в обычном окружении
            assert get_env_file() == ".env"


class TestGetSettings:
    """Тесты для функции get_settings."""
    
    def test_get_settings_caching(self):
        """Тест кэширования настроек."""
        # Очищаем кэш для чистого теста
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {
            'THENEWSAPI_API_TOKEN': 'test_token',
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_GSHEET_ID': 'test_id',
            'GOOGLE_ACCOUNT_EMAIL': 'test@email.com',
            'GOOGLE_ACCOUNT_KEY': 'test_key'
        }):
            # Первый вызов
            result1 = get_settings()
            # Второй вызов
            result2 = get_settings()
            
            # Должны вернуться одинаковые объекты из-за кэширования
            assert result1 is result2 