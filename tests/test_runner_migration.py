# tests/test_runner_migration.py

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

from src.services.news.runner import load_config_from_file


class TestRunnerMigration:
    """Тесты автоматической миграции конфигурации в runner.py"""
    
    def test_load_old_format_migrates_automatically(self):
        """Тест автоматической миграции старого формата {provider: config} в новый [{"provider": "...", "config": {...}}]"""
        old_format_data = {
            "thenewsapi_com": {
                "search": "test search",
                "limit": "50",
                "language": "en"
            },
            "newsdata_io": {
                "q": "crypto news", 
                "size": "100"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(old_format_data, f)
            temp_file_path = f.name
        
        try:
            # Мокаем валидатор
            with patch('src.services.news.runner.validate_api_input') as mock_validator:
                mock_validator.return_value = [
                    {"provider": "thenewsapi_com", "config": {"search": "test search", "limit": "50", "language": "en"}},
                    {"provider": "newsdata_io", "config": {"q": "crypto news", "size": "100"}}
                ]
                
                result = load_config_from_file(temp_file_path)
                
                # Проверяем что результат в новом формате
                assert isinstance(result, list)
                assert len(result) == 2
                assert result[0]["provider"] == "thenewsapi_com" 
                assert result[0]["config"]["search"] == "test search"
                assert result[1]["provider"] == "newsdata_io"
                assert result[1]["config"]["q"] == "crypto news"
                
                # Проверяем что файл был перезаписан в новом формате
                with open(temp_file_path, 'r') as f:
                    migrated_data = json.load(f)
                assert isinstance(migrated_data, list)
                assert len(migrated_data) == 2
                
        finally:
            os.unlink(temp_file_path)
    
    def test_load_new_format_unchanged(self):
        """Тест что новый формат остается без изменений"""
        new_format_data = [
            {
                "provider": "thenewsapi_com",
                "config": {
                    "search": "AI news",
                    "limit": "75"
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(new_format_data, f)
            temp_file_path = f.name
        
        try:
            # Мокаем валидатор
            with patch('src.services.news.runner.validate_api_input') as mock_validator:
                mock_validator.return_value = new_format_data
                
                result = load_config_from_file(temp_file_path)
                
                # Проверяем что результат не изменился
                assert isinstance(result, list)
                assert len(result) == 1
                assert result[0]["provider"] == "thenewsapi_com"
                assert result[0]["config"]["search"] == "AI news"
                
        finally:
            os.unlink(temp_file_path)
    
    def test_invalid_format_raises_error(self):
        """Тест что неподдерживаемый формат вызывает ошибку"""
        invalid_data = "invalid string format"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            temp_file_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Неподдерживаемый формат конфигурации"):
                load_config_from_file(temp_file_path)
        finally:
            os.unlink(temp_file_path) 