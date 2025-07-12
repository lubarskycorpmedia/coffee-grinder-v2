# tests/test_logger.py

import pytest
import logging
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.logger import setup_logger


class TestSetupLogger:
    """Тесты для функции setup_logger."""
    
    def test_setup_logger_default(self):
        """Тест настройки логгера с параметрами по умолчанию."""
        logger = setup_logger("test_logger")
        
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
    
    def test_setup_logger_with_file(self):
        """Тест настройки логгера с файлом."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file = tmp_file.name
        
        try:
            logger = setup_logger("test_logger_file", log_file=log_file)
            
            assert logger.name == "test_logger_file"
            assert len(logger.handlers) == 2  # console + file
            
            # Проверяем типы handlers
            handler_types = [type(h).__name__ for h in logger.handlers]
            assert "StreamHandler" in handler_types
            assert "RotatingFileHandler" in handler_types
        finally:
            os.unlink(log_file)
    
    def test_setup_logger_no_duplicate_handlers(self):
        """Тест предотвращения дублирования handlers."""
        logger1 = setup_logger("test_no_duplicate")
        initial_handlers_count = len(logger1.handlers)
        
        logger2 = setup_logger("test_no_duplicate")
        
        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handlers_count
    
    @patch('src.logger.get_log_level')
    def test_setup_logger_different_log_levels(self, mock_get_log_level):
        """Тест настройки разных уровней логирования."""
        mock_get_log_level.return_value = "DEBUG"
        
        logger = setup_logger("test_debug")
        
        assert logger.level == logging.DEBUG
        for handler in logger.handlers:
            assert handler.level == logging.DEBUG
    
    def test_logger_formatter(self):
        """Тест форматирования логов."""
        logger = setup_logger("test_formatter")
        
        # Проверяем, что у всех handlers есть форматтер
        for handler in logger.handlers:
            assert handler.formatter is not None
            formatter = handler.formatter
            assert "%(asctime)s" in formatter._fmt
            assert "%(name)s" in formatter._fmt
            assert "%(levelname)s" in formatter._fmt
            assert "%(message)s" in formatter._fmt
    
    def test_rotating_file_handler_config(self):
        """Тест конфигурации RotatingFileHandler."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file = tmp_file.name
        
        try:
            logger = setup_logger(
                "test_rotating", 
                log_file=log_file,
                max_bytes=1024,
                backup_count=3
            )
            
            # Находим RotatingFileHandler
            rotating_handler = None
            for handler in logger.handlers:
                if hasattr(handler, 'maxBytes'):
                    rotating_handler = handler
                    break
            
            assert rotating_handler is not None
            assert rotating_handler.maxBytes == 1024
            assert rotating_handler.backupCount == 3
            assert rotating_handler.encoding == 'utf-8'
        finally:
            os.unlink(log_file)
    
    def test_logger_output(self, caplog):
        """Тест вывода логов."""
        logger = setup_logger("test_output")
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        
        assert "Test message" in caplog.text
        assert "test_output" in caplog.text
    
    def test_setup_logger_without_settings(self):
        """Тест настройки логгера когда настройки недоступны."""
        # Симулируем ситуацию когда get_log_level() недоступен
        with patch('src.logger.get_log_level', side_effect=Exception("Settings not available")):
            logger = setup_logger("test_no_settings")
            
            assert logger.name == "test_no_settings"
            assert logger.level == logging.INFO  # Дефолтный уровень
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], logging.StreamHandler) 