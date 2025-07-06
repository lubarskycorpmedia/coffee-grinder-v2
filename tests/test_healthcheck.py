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
    
    @patch('src.healthcheck.get_google_settings')
    @patch('src.healthcheck.get_ai_settings')
    @patch('src.healthcheck.get_news_settings')
    def test_check_configuration_success(self, mock_get_news_settings, mock_get_ai_settings, mock_get_google_settings):
        """Тест успешной проверки конфигурации."""
        # Мокаем настройки новостей
        mock_news_settings = MagicMock()
        mock_news_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_get_news_settings.return_value = mock_news_settings
        
        # Мокаем настройки AI
        mock_ai_settings = MagicMock()
        mock_ai_settings.OPENAI_API_KEY = "test_key"
        mock_get_ai_settings.return_value = mock_ai_settings
        
        # Мокаем настройки Google
        mock_google_settings = MagicMock()
        mock_google_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_google_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_get_google_settings.return_value = mock_google_settings
        
        result = check_configuration()
        assert result is True
    
    @patch('src.healthcheck.get_google_settings')
    @patch('src.healthcheck.get_ai_settings')
    @patch('src.healthcheck.get_news_settings')
    def test_check_configuration_missing_vars(self, mock_get_news_settings, mock_get_ai_settings, mock_get_google_settings):
        """Тест проверки конфигурации с отсутствующими переменными."""
        # Мокаем настройки новостей с пустым токеном
        mock_news_settings = MagicMock()
        mock_news_settings.THENEWSAPI_API_TOKEN = ""
        mock_get_news_settings.return_value = mock_news_settings
        
        # Мокаем настройки AI
        mock_ai_settings = MagicMock()
        mock_ai_settings.OPENAI_API_KEY = "test_key"
        mock_get_ai_settings.return_value = mock_ai_settings
        
        # Мокаем настройки Google
        mock_google_settings = MagicMock()
        mock_google_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_google_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_get_google_settings.return_value = mock_google_settings
        
        result = check_configuration()
        assert result is False
    
    @patch('src.healthcheck.get_google_settings')
    @patch('src.healthcheck.get_ai_settings')
    @patch('src.healthcheck.get_news_settings')
    def test_check_configuration_missing_ai_key(self, mock_get_news_settings, mock_get_ai_settings, mock_get_google_settings):
        """Тест проверки конфигурации с отсутствующим AI ключом."""
        # Мокаем настройки новостей
        mock_news_settings = MagicMock()
        mock_news_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_get_news_settings.return_value = mock_news_settings
        
        # Мокаем настройки AI с пустым ключом
        mock_ai_settings = MagicMock()
        mock_ai_settings.OPENAI_API_KEY = ""
        mock_get_ai_settings.return_value = mock_ai_settings
        
        # Мокаем настройки Google
        mock_google_settings = MagicMock()
        mock_google_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_google_settings.GOOGLE_ACCOUNT_KEY = "test_key"
        mock_get_google_settings.return_value = mock_google_settings
        
        result = check_configuration()
        assert result is False
    
    @patch('src.healthcheck.get_google_settings')
    @patch('src.healthcheck.get_ai_settings')
    @patch('src.healthcheck.get_news_settings')
    def test_check_configuration_news_exception(self, mock_get_news_settings, mock_get_ai_settings, mock_get_google_settings):
        """Тест обработки исключения в настройках новостей."""
        mock_get_news_settings.side_effect = Exception("News settings error")
        
        result = check_configuration()
        assert result is False
    
    @patch('src.healthcheck.get_google_settings')
    @patch('src.healthcheck.get_ai_settings')
    @patch('src.healthcheck.get_news_settings')
    def test_check_configuration_ai_exception(self, mock_get_news_settings, mock_get_ai_settings, mock_get_google_settings):
        """Тест обработки исключения в настройках AI."""
        # Мокаем настройки новостей
        mock_news_settings = MagicMock()
        mock_news_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_get_news_settings.return_value = mock_news_settings
        
        # AI настройки выбрасывают исключение
        mock_get_ai_settings.side_effect = Exception("AI settings error")
        
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
    
    @patch('src.run.validate_environment')
    def test_dry_run_check_success(self, mock_validate_environment):
        """Тест успешной проверки dry-run."""
        mock_validate_environment.return_value = {
            "errors": [],
            "warnings": []
        }
        
        result = dry_run_check()
        assert result is True
    
    @patch('src.run.validate_environment')
    def test_dry_run_check_with_errors(self, mock_validate_environment):
        """Тест dry-run проверки с ошибками валидации."""
        mock_validate_environment.return_value = {
            "errors": ["Missing API key"],
            "warnings": []
        }
        
        result = dry_run_check()
        assert result is False
    
    @patch('src.run.validate_environment')
    def test_dry_run_check_exception(self, mock_validate_environment):
        """Тест обработки исключения в dry_run_check."""
        mock_validate_environment.side_effect = Exception("Validation error")
        
        result = dry_run_check()
        assert result is False


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