# tests/test_healthcheck.py

import pytest
import sys
from unittest.mock import patch, MagicMock
from src.healthcheck import (
    check_configuration,
    check_dependencies,
    dry_run_check,
    healthcheck,
    main
)


# Убираем автоматический мок - будем мокать где нужно


class TestCheckConfiguration:
    """Тесты для функции check_configuration."""
    
    @patch('src.healthcheck.get_settings')
    def test_check_configuration_success(self, mock_get_settings):
        """Тест успешной проверки конфигурации."""
        mock_settings = MagicMock()
        mock_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_settings.OPENAI_API_KEY = "test_key"
        mock_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@email.com"
        mock_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_settings.DEDUP_THRESHOLD = 0.85
        mock_settings.MAX_RETRIES = 3
        mock_settings.ASK_NEWS_COUNT = 10
        mock_get_settings.return_value = mock_settings
        
        result = check_configuration()
        assert result is True
    
    @patch('src.healthcheck.get_settings')
    def test_check_configuration_missing_vars(self, mock_get_settings):
        """Тест проверки конфигурации с отсутствующими переменными."""
        mock_settings = MagicMock()
        mock_settings.THENEWSAPI_API_TOKEN = ""
        mock_settings.OPENAI_API_KEY = "test_key"
        mock_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@email.com"
        mock_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_get_settings.return_value = mock_settings
        
        result = check_configuration()
        assert result is False
    
    @patch('src.healthcheck.get_settings')
    def test_check_configuration_invalid_threshold(self, mock_get_settings):
        """Тест проверки конфигурации с неверным порогом дедупликации."""
        mock_settings = MagicMock()
        mock_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_settings.OPENAI_API_KEY = "test_key"
        mock_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@email.com"
        mock_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_settings.DEDUP_THRESHOLD = 1.5  # Неверное значение
        mock_settings.MAX_RETRIES = 3
        mock_settings.ASK_NEWS_COUNT = 10
        mock_get_settings.return_value = mock_settings
        
        result = check_configuration()
        assert result is False
    
    @patch('src.healthcheck.get_settings')
    def test_check_configuration_invalid_retries(self, mock_get_settings):
        """Тест проверки конфигурации с неверным количеством ретраев."""
        mock_settings = MagicMock()
        mock_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_settings.OPENAI_API_KEY = "test_key"
        mock_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@email.com"
        mock_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_settings.DEDUP_THRESHOLD = 0.85
        mock_settings.MAX_RETRIES = -1  # Неверное значение
        mock_settings.ASK_NEWS_COUNT = 10
        mock_get_settings.return_value = mock_settings
        
        result = check_configuration()
        assert result is False
    
    @patch('src.healthcheck.get_settings')
    def test_check_configuration_invalid_news_count(self, mock_get_settings):
        """Тест проверки конфигурации с неверным количеством новостей."""
        mock_settings = MagicMock()
        mock_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_settings.OPENAI_API_KEY = "test_key"
        mock_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@email.com"
        mock_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_settings.DEDUP_THRESHOLD = 0.85
        mock_settings.MAX_RETRIES = 3
        mock_settings.ASK_NEWS_COUNT = 0  # Неверное значение
        mock_get_settings.return_value = mock_settings
        
        result = check_configuration()
        assert result is False
    
    @patch('src.healthcheck.get_settings')
    def test_check_configuration_exception(self, mock_get_settings):
        """Тест обработки исключения в check_configuration."""
        mock_get_settings.side_effect = Exception("Configuration error")
        
        result = check_configuration()
        assert result is False


class TestCheckDependencies:
    """Тесты для функции check_dependencies."""
    
    def test_check_dependencies_success(self):
        """Тест успешной проверки зависимостей."""
        with patch('builtins.__import__') as mock_import:
            result = check_dependencies()
            assert result is True
    
    def test_check_dependencies_import_error(self):
        """Тест проверки зависимостей с ошибкой импорта."""
        with patch('builtins.__import__') as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            result = check_dependencies()
            assert result is False


class TestDryRunCheck:
    """Тесты для функции dry_run_check."""
    
    def test_dry_run_check_success(self):
        """Тест успешной проверки dry-run."""
        result = dry_run_check()
        assert result is True  # Пока всегда True, так как run.py не реализован
    
    @patch('src.healthcheck.get_logger')
    def test_dry_run_check_exception(self, mock_get_logger):
        """Тест обработки исключения в dry_run_check."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        # Мокаем logger.info чтобы он выбрасывал исключение
        mock_logger.info.side_effect = Exception("Logger error")
        
        result = dry_run_check()
        assert result is False
        mock_logger.error.assert_called_once()


class TestHealthcheck:
    """Тесты для функции healthcheck."""
    
    @patch('src.healthcheck.check_configuration')
    @patch('src.healthcheck.check_dependencies')
    @patch('src.healthcheck.dry_run_check')
    def test_healthcheck_all_pass(self, mock_dry_run, mock_deps, mock_config):
        """Тест успешной проверки всех компонентов."""
        mock_config.return_value = True
        mock_deps.return_value = True
        mock_dry_run.return_value = True
        
        result = healthcheck(dry_run=True)
        assert result is True
    
    @patch('src.healthcheck.check_configuration')
    @patch('src.healthcheck.check_dependencies')
    def test_healthcheck_config_fail(self, mock_deps, mock_config):
        """Тест провала проверки конфигурации."""
        mock_config.return_value = False
        mock_deps.return_value = True
        
        result = healthcheck(dry_run=False)
        assert result is False
    
    @patch('src.healthcheck.check_configuration')
    @patch('src.healthcheck.check_dependencies')
    def test_healthcheck_deps_fail(self, mock_deps, mock_config):
        """Тест провала проверки зависимостей."""
        mock_config.return_value = True
        mock_deps.return_value = False
        
        result = healthcheck(dry_run=False)
        assert result is False
    
    @patch('src.healthcheck.check_configuration')
    @patch('src.healthcheck.check_dependencies')
    def test_healthcheck_without_dry_run(self, mock_deps, mock_config):
        """Тест проверки без dry-run режима."""
        mock_config.return_value = True
        mock_deps.return_value = True
        
        result = healthcheck(dry_run=False)
        assert result is True


class TestMain:
    """Тесты для функции main."""
    
    @patch('src.healthcheck.healthcheck')
    @patch('sys.argv', ['healthcheck.py'])
    def test_main_success(self, mock_healthcheck):
        """Тест успешного выполнения main."""
        mock_healthcheck.return_value = True
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        mock_healthcheck.assert_called_once_with(dry_run=False)
    
    @patch('src.healthcheck.healthcheck')
    @patch('sys.argv', ['healthcheck.py', '--dry-run'])
    def test_main_dry_run(self, mock_healthcheck):
        """Тест выполнения main с dry-run флагом."""
        mock_healthcheck.return_value = True
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        mock_healthcheck.assert_called_once_with(dry_run=True)
    
    @patch('src.healthcheck.healthcheck')
    @patch('sys.argv', ['healthcheck.py'])
    def test_main_failure(self, mock_healthcheck):
        """Тест провала выполнения main."""
        mock_healthcheck.return_value = False
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1 