# /tests/test_run.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import argparse

from src.run import (
    create_argument_parser,
    validate_environment,
    run_pipeline,
    main
)


class TestOrchestrator:
    """Интеграционные тесты для orchestrator"""
    
    def test_create_argument_parser(self):
        """Тест создания парсера аргументов"""
        parser = create_argument_parser()
        
        assert parser is not None
        assert isinstance(parser, argparse.ArgumentParser)
        
        # Тест парсинга аргументов
        args = parser.parse_args(['--dry-run', '--query', 'test', '--limit', '10'])
        assert args.dry_run is True
        assert args.query == 'test'
        assert args.limit == 10
        assert args.language == 'en'  # default
        assert args.provider == 'thenewsapi'  # default
    
    @patch('src.run.get_news_settings')
    @patch('src.run.get_ai_settings')
    @patch('src.run.get_google_settings')
    def test_validate_environment_success(self, mock_get_google_settings,
                                         mock_get_ai_settings, mock_get_news_settings):
        """Тест успешной валидации окружения"""
        # Мокаем настройки
        mock_news_settings = Mock()
        mock_news_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_get_news_settings.return_value = mock_news_settings
        
        mock_ai_settings = Mock()
        mock_ai_settings.OPENAI_API_KEY = "test_openai_key"
        mock_get_ai_settings.return_value = mock_ai_settings
        
        mock_google_settings = Mock()
        mock_google_settings.GOOGLE_GSHEET_ID = "test_sheet_id"
        mock_google_settings.GOOGLE_ACCOUNT_KEY = "test_account_key"
        mock_get_google_settings.return_value = mock_google_settings
        
        result = validate_environment()
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
    
    @patch('src.run.get_news_settings')
    @patch('src.run.get_ai_settings')
    @patch('src.run.get_google_settings')
    def test_validate_environment_missing_keys(self, mock_get_google_settings,
                                              mock_get_ai_settings, mock_get_news_settings):
        """Тест валидации с отсутствующими ключами"""
        # Мокаем настройки с отсутствующими ключами
        mock_news_settings = Mock()
        mock_news_settings.THENEWSAPI_API_TOKEN = None
        mock_get_news_settings.return_value = mock_news_settings
        
        mock_ai_settings = Mock()
        mock_ai_settings.OPENAI_API_KEY = None
        mock_get_ai_settings.return_value = mock_ai_settings
        
        mock_google_settings = Mock()
        mock_google_settings.GOOGLE_GSHEET_ID = None
        mock_google_settings.GOOGLE_ACCOUNT_KEY = None
        mock_get_google_settings.return_value = mock_google_settings
        
        result = validate_environment()
        
        assert result["valid"] is False
        assert len(result["errors"]) == 2  # news and ai errors
        assert len(result["warnings"]) == 1  # google warning
        assert "THENEWSAPI_API_TOKEN не настроен" in result["errors"]
        assert "OPENAI_API_KEY не настроен" in result["errors"]
    
    @patch('src.run.validate_environment')
    @patch('src.run.create_news_processor')
    def test_run_pipeline_success(self, mock_create_processor, mock_validate_env):
        """Тест успешного выполнения pipeline"""
        # Мокаем валидацию
        mock_validate_env.return_value = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Мокаем процессор
        mock_processor = Mock()
        mock_processor.run_full_pipeline.return_value = {
            "success": True,
            "fetched_count": 10,
            "processed_count": 8,
            "exported_count": 8,
            "duplicates_found": 2,
            "duration_seconds": 5.5,
            "errors": []
        }
        mock_create_processor.return_value = mock_processor
        
        # Создаем аргументы
        args = argparse.Namespace(
            dry_run=False,
            query="test",
            category="tech",
            language="en",
            limit=10,
            provider="thenewsapi"
        )
        
        result = run_pipeline(args)
        
        assert result["success"] is True
        assert result["fetched_count"] == 10
        assert result["processed_count"] == 8
        assert result["exported_count"] == 8
        assert result["duplicates_found"] == 2
        
        # Проверяем вызовы
        mock_create_processor.assert_called_once_with(
            news_provider="thenewsapi",
            max_news_items=10,
            fail_on_errors=False
        )
        
        mock_processor.run_full_pipeline.assert_called_once_with(
            query="test",
            category="tech",
            language="en",
            limit=10,
            export_to_sheets=True,  # не dry-run
            append_to_sheets=True
        )
    
    @patch('src.run.validate_environment')
    @patch('src.run.create_news_processor')
    def test_run_pipeline_dry_run(self, mock_create_processor, mock_validate_env):
        """Тест выполнения pipeline в dry-run режиме"""
        # Мокаем валидацию
        mock_validate_env.return_value = {
            "valid": True,
            "errors": [],
            "warnings": ["GOOGLE_GSHEET_ID не настроен"]
        }
        
        # Мокаем процессор
        mock_processor = Mock()
        mock_processor.run_full_pipeline.return_value = {
            "success": True,
            "fetched_count": 5,
            "processed_count": 4,
            "exported_count": 0,  # нет экспорта в dry-run
            "duplicates_found": 1,
            "duration_seconds": 3.2,
            "errors": []
        }
        mock_create_processor.return_value = mock_processor
        
        # Создаем аргументы для dry-run
        args = argparse.Namespace(
            dry_run=True,
            query=None,
            category=None,
            language="en",
            limit=50,
            provider="thenewsapi"
        )
        
        result = run_pipeline(args)
        
        assert result["success"] is True
        assert result["exported_count"] == 0
        
        # Проверяем, что экспорт отключен
        mock_processor.run_full_pipeline.assert_called_once_with(
            query=None,
            category=None,
            language="en",
            limit=50,
            export_to_sheets=False,  # dry-run режим
            append_to_sheets=True
        )
    
    @patch('src.run.validate_environment')
    def test_run_pipeline_validation_error(self, mock_validate_env):
        """Тест pipeline с ошибками валидации"""
        # Мокаем валидацию с ошибками
        mock_validate_env.return_value = {
            "valid": False,
            "errors": ["THENEWSAPI_API_TOKEN не настроен"],
            "warnings": []
        }
        
        args = argparse.Namespace(
            dry_run=False,
            query="test",
            category=None,
            language="en",
            limit=50,
            provider="thenewsapi"
        )
        
        result = run_pipeline(args)
        
        assert result["success"] is False
        assert "THENEWSAPI_API_TOKEN не настроен" in result["errors"]
    
    @patch('src.run.validate_environment')
    @patch('src.run.create_news_processor')
    def test_run_pipeline_processor_exception(self, mock_create_processor, mock_validate_env):
        """Тест обработки исключений в процессоре"""
        # Мокаем валидацию
        mock_validate_env.return_value = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Мокаем исключение в процессоре
        mock_create_processor.side_effect = Exception("Test processor error")
        
        args = argparse.Namespace(
            dry_run=False,
            query="test",
            category=None,
            language="en",
            limit=50,
            provider="thenewsapi"
        )
        
        result = run_pipeline(args)
        
        assert result["success"] is False
        assert len(result["errors"]) == 1
        assert "Test processor error" in result["errors"][0]
        assert result["fetched_count"] == 0
        assert result["processed_count"] == 0
        assert result["exported_count"] == 0
    
    @patch('src.run.run_pipeline')
    @patch('sys.argv', ['run.py', '--dry-run', '--verbose'])
    def test_main_success(self, mock_run_pipeline):
        """Тест главной функции при успешном выполнении"""
        mock_run_pipeline.return_value = {"success": True}
        
        exit_code = main()
        
        assert exit_code == 0
        mock_run_pipeline.assert_called_once()
    
    @patch('src.run.run_pipeline')
    @patch('sys.argv', ['run.py', '--query', 'test'])
    def test_main_failure(self, mock_run_pipeline):
        """Тест главной функции при ошибке"""
        mock_run_pipeline.return_value = {"success": False}
        
        exit_code = main()
        
        assert exit_code == 1
        mock_run_pipeline.assert_called_once()
    
    def test_argument_parser_defaults(self):
        """Тест значений по умолчанию парсера аргументов"""
        parser = create_argument_parser()
        args = parser.parse_args([])
        
        assert args.dry_run is False
        assert args.query is None
        assert args.category is None
        assert args.language == "en"
        assert args.limit == 50
        assert args.provider == "thenewsapi"
        assert args.verbose is False
    
    def test_argument_parser_all_options(self):
        """Тест парсера с всеми опциями"""
        parser = create_argument_parser()
        args = parser.parse_args([
            '--dry-run',
            '--query', 'AI technology',
            '--category', 'tech',
            '--language', 'ru',
            '--limit', '25',
            '--provider', 'thenewsapi',
            '--verbose'
        ])
        
        assert args.dry_run is True
        assert args.query == 'AI technology'
        assert args.category == 'tech'
        assert args.language == 'ru'
        assert args.limit == 25
        assert args.provider == 'thenewsapi'
        assert args.verbose is True 