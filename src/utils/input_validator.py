# /src/utils/input_validator.py

import re
import logging
from typing import Dict, Any, Optional, Union, List
from enum import Enum

from src.logger import setup_logger


class ThreatType(Enum):
    """Типы угроз безопасности"""
    SQL_INJECTION = "SQL_INJECTION"
    XSS = "XSS" 
    COMMAND_INJECTION = "COMMAND_INJECTION"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    FIELD_LENGTH_EXCEEDED = "FIELD_LENGTH_EXCEEDED"
    VALUE_LENGTH_EXCEEDED = "VALUE_LENGTH_EXCEEDED"
    INVALID_CHARACTERS = "INVALID_CHARACTERS"


class InputSecurityValidator:
    """
    Универсальный валидатор безопасности для входящих данных
    
    Защищает от:
    - SQL инъекций
    - XSS атак  
    - Command injection
    - Path traversal
    - Превышения лимитов длины
    
    Поведение: Очищает опасные символы и логирует угрозы
    """
    
    # Максимальные длины
    MAX_FIELD_NAME_LENGTH: int = 20
    MAX_FIELD_VALUE_LENGTH: int = 200
    MAX_FIELDS_COUNT: int = 100
    
    # Паттерны для детекции угроз
    SQL_INJECTION_PATTERNS = [
        r"['\"]\s*;?\s*--",           # SQL комментарии
        r"['\"]\s*/\*.*?\*/",         # SQL блочные комментарии
        r"\bunion\b.*?\bselect\b",    # UNION SELECT
        r"\bselect\b.*?\bfrom\b",     # SELECT FROM
        r"\bdrop\b.*?\btable\b",      # DROP TABLE
        r"\binsert\b.*?\binto\b",     # INSERT INTO
        r"\bupdate\b.*?\bset\b",      # UPDATE SET
        r"\bdelete\b.*?\bfrom\b",     # DELETE FROM
        r"['\"][^'\"]*['\"].*?['\"][^'\"]*['\"]",  # Множественные кавычки
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>", # Script теги
        r"javascript\s*:",            # JavaScript протокол
        r"on\w+\s*=",                # Event handlers (onclick, onload, etc.)
        r"<iframe[^>]*>",            # iframe теги
        r"<object[^>]*>",            # object теги
        r"<embed[^>]*>",             # embed теги
        r"<form[^>]*>",              # form теги
        r"document\.",               # DOM манипуляции
        r"window\.",                 # Window объект
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[|&;]",                    # Разделители команд
        r"\$\([^)]*\)",              # Command substitution $()
        r"`[^`]*`",                  # Command substitution ``
        r"\b(cmd|bash|sh|powershell|exec)\b",  # Команды оболочки
        r">\s*/dev/null",            # Перенаправление вывода
        r"2>&1",                     # Перенаправление ошибок
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",                    # Относительные пути ../
        r"\.\.\\",                   # Windows пути ..\
        r"/etc/passwd",              # Unix системные файлы
        r"/etc/shadow",
        r"c:\\windows",              # Windows системные пути
        r"c:\\system32",
        r"/proc/",                   # Proc файловая система
        r"/var/log",                 # Лог файлы
    ]
    
    # Разрешенные символы
    ALLOWED_FIELD_CHARS = re.compile(r'^[a-zA-Z0-9_]+$')
    ALLOWED_VALUE_CHARS = re.compile(r'^[a-zA-Z0-9_\-.,@/:?&=\s]*$')
    
    def __init__(self):
        """Инициализация валидатора"""
        self.logger = setup_logger(__name__)
    
    def _detect_threat_type(self, value: str) -> Optional[ThreatType]:
        """
        Определяет тип угрозы в строке
        
        Args:
            value: Строка для проверки
            
        Returns:
            Тип угрозы или None если угроза не обнаружена
        """
        value_lower = value.lower()
        
        # Проверка SQL инъекций
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE | re.DOTALL):
                return ThreatType.SQL_INJECTION
        
        # Проверка XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE | re.DOTALL):
                return ThreatType.XSS
        
        # Проверка Command Injection
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return ThreatType.COMMAND_INJECTION
        
        # Проверка Path Traversal
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return ThreatType.PATH_TRAVERSAL
        
        return None
    
    def _clean_dangerous_chars(self, value: str, is_field_name: bool = False) -> str:
        """
        Удаляет опасные символы из строки
        
        Args:
            value: Строка для очистки
            is_field_name: True если это название поля, False если значение
            
        Returns:
            Очищенная строка
        """
        if is_field_name:
            # Для названий полей - только буквы, цифры и подчеркивания
            return re.sub(r'[^a-zA-Z0-9_]', '', value)
        else:
            # Для значений - расширенный набор символов
            return re.sub(r'[^a-zA-Z0-9_\-.,@/:?&=\s]', '', value)
    
    def sanitize_field_name(self, field_name: str) -> str:
        """
        Очищает и валидирует название поля
        
        Args:
            field_name: Название поля для валидации
            
        Returns:
            Очищенное название поля
        """
        if not isinstance(field_name, str):
            field_name = str(field_name)
        
        original_value = field_name
        
        # Проверка длины
        if len(field_name) > self.MAX_FIELD_NAME_LENGTH:
            field_name = field_name[:self.MAX_FIELD_NAME_LENGTH]
            self.logger.warning(
                f"Security threat detected in field name: {ThreatType.FIELD_LENGTH_EXCEEDED.value} - "
                f"Original length: {len(original_value)}, truncated to: {self.MAX_FIELD_NAME_LENGTH}"
            )
        
        # Проверка угроз
        threat_type = self._detect_threat_type(field_name)
        if threat_type:
            cleaned_value = self._clean_dangerous_chars(field_name, is_field_name=True)
            self.logger.warning(
                f"Security threat detected in field name: {threat_type.value} - "
                f"Original: '{original_value}' -> Cleaned: '{cleaned_value}'"
            )
            field_name = cleaned_value
        
        # Проверка разрешенных символов
        if not self.ALLOWED_FIELD_CHARS.match(field_name):
            cleaned_value = self._clean_dangerous_chars(field_name, is_field_name=True)
            if cleaned_value != field_name:
                self.logger.warning(
                    f"Security threat detected in field name: {ThreatType.INVALID_CHARACTERS.value} - "
                    f"Original: '{original_value}' -> Cleaned: '{cleaned_value}'"
                )
            field_name = cleaned_value
        
        return field_name
    
    def sanitize_field_value(self, field_value: Union[str, int, float, bool, None]) -> str:
        """
        Очищает и валидирует значение поля
        
        Args:
            field_value: Значение поля для валидации
            
        Returns:
            Очищенное значение поля как строка
        """
        if field_value is None:
            return ""
        
        if not isinstance(field_value, str):
            field_value = str(field_value)
        
        original_value = field_value
        
        # Проверка длины
        if len(field_value) > self.MAX_FIELD_VALUE_LENGTH:
            field_value = field_value[:self.MAX_FIELD_VALUE_LENGTH]
            self.logger.warning(
                f"Security threat detected in field value: {ThreatType.VALUE_LENGTH_EXCEEDED.value} - "
                f"Original length: {len(original_value)}, truncated to: {self.MAX_FIELD_VALUE_LENGTH}"
            )
        
        # Проверка угроз
        threat_type = self._detect_threat_type(field_value)
        if threat_type:
            cleaned_value = self._clean_dangerous_chars(field_value, is_field_name=False)
            self.logger.warning(
                f"Security threat detected in field value: {threat_type.value} - "
                f"Original: '{original_value}' -> Cleaned: '{cleaned_value}'"
            )
            field_value = cleaned_value
        
        # Проверка разрешенных символов
        if not self.ALLOWED_VALUE_CHARS.match(field_value):
            cleaned_value = self._clean_dangerous_chars(field_value, is_field_name=False)
            if cleaned_value != field_value:
                self.logger.warning(
                    f"Security threat detected in field value: {ThreatType.INVALID_CHARACTERS.value} - "
                    f"Original: '{original_value}' -> Cleaned: '{cleaned_value}'"
                )
            field_value = cleaned_value
        
        return field_value.strip()
    
    def validate_config_dict(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидирует весь конфигурационный словарь
        
        Args:
            config_dict: Словарь конфигурации для валидации
            
        Returns:
            Очищенный и валидированный словарь
            
        Raises:
            ValueError: Если количество полей превышает лимит
        """
        if not isinstance(config_dict, dict):
            self.logger.error(f"Config must be a dictionary, got: {type(config_dict)}")
            return {}
        
        # Проверка количества полей
        if len(config_dict) > self.MAX_FIELDS_COUNT:
            self.logger.warning(
                f"Security threat detected: Too many fields ({len(config_dict)} > {self.MAX_FIELDS_COUNT}). "
                f"Only first {self.MAX_FIELDS_COUNT} fields will be processed."
            )
            # Берем только первые MAX_FIELDS_COUNT полей
            config_dict = dict(list(config_dict.items())[:self.MAX_FIELDS_COUNT])
        
        validated_config = {}
        
        for field_name, field_value in config_dict.items():
            # Валидируем название поля
            clean_field_name = self.sanitize_field_name(field_name)
            
            # Пропускаем пустые названия полей
            if not clean_field_name:
                self.logger.warning(f"Empty field name after sanitization, skipping: '{field_name}'")
                continue
            
            # Валидируем значение поля
            clean_field_value = self.sanitize_field_value(field_value)
            
            # Исключаем пустые значения (как требовалось в задаче)
            if clean_field_value:
                validated_config[clean_field_name] = clean_field_value
            else:
                self.logger.debug(f"Excluding empty value for field: '{clean_field_name}'")
        
        self.logger.info(f"Config validation completed. Original fields: {len(config_dict)}, "
                        f"validated fields: {len(validated_config)}")
        
        return validated_config


# Глобальный экземпляр валидатора для переиспользования
security_validator = InputSecurityValidator()


def validate_api_input(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Удобная функция для валидации входящих данных API
    
    Args:
        data: Список запросов в формате [{"provider": "name", "config": {...}}]
        
    Returns:
        Валидированный список запросов в том же формате
    """
    validated_requests = []
    
    for i, request in enumerate(data):
        if not isinstance(request, dict):
            security_validator.logger.warning(f"Invalid request format at index {i}: {request}")
            continue
            
        provider_name = request.get("provider")
        provider_config = request.get("config", {})
        
        if not provider_name:
            security_validator.logger.warning(f"Missing provider name in request at index {i}: {request}")
            continue
            
        if isinstance(provider_config, dict):
            validated_config = security_validator.validate_config_dict(provider_config)
            validated_requests.append({
                "provider": provider_name,
                "config": validated_config
            })
        else:
            security_validator.logger.warning(f"Invalid config for provider {provider_name} at index {i}: {provider_config}")
    
    return validated_requests 