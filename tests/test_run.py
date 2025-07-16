# /tests/test_run.py

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.run import main


class TestRun:
    """Тесты для упрощенного CLI launcher"""
    
    @patch('src.run.run_news_parsing_sync')
    def test_main_success(self, mock_run_parsing):
        """Тест успешного выполнения main"""
        # Мокаем успешный результат
        mock_run_parsing.return_value = {
            "success": True,
            "providers_processed": 2
        }
        
        # Вызываем main
        exit_code = main()
        
        # Проверяем результат
        assert exit_code == 0
        mock_run_parsing.assert_called_once()
    
    @patch('src.run.run_news_parsing_sync')
    def test_main_failure(self, mock_run_parsing):
        """Тест неуспешного выполнения main"""
        # Мокаем неуспешный результат
        mock_run_parsing.return_value = {
            "success": False,
            "error": "Test error"
        }
        
        # Вызываем main
        exit_code = main()
        
        # Проверяем результат
        assert exit_code == 1
        mock_run_parsing.assert_called_once()
    
    @patch('src.run.run_news_parsing_sync')
    def test_main_exception(self, mock_run_parsing):
        """Тест обработки исключения в main"""
        # Мокаем исключение
        mock_run_parsing.side_effect = Exception("Critical error")
        
        # Вызываем main
        exit_code = main()
        
        # Проверяем результат
        assert exit_code == 1
        mock_run_parsing.assert_called_once() 