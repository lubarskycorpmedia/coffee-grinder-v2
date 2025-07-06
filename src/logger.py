# /src/logger.py
# Настройка логирования 

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
from src.config import get_settings


def setup_logger(
    name: str = "coffee_grinder",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Настройка логгера с выводом в stdout и опциональной ротацией файлов.
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов (опционально)
        max_bytes: Максимальный размер файла лога в байтах
        backup_count: Количество резервных файлов
        
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    
    # Пытаемся получить настройки, если не получается - используем дефолтные
    try:
        settings = get_settings()
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    except Exception:
        # Если не можем получить настройки (например, в тестах), используем INFO
        log_level = logging.INFO
    
    logger.setLevel(log_level)
    
    # Избегаем дублирования handlers при повторном вызове
    if logger.handlers:
        return logger
    
    # Форматтер для логов
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler для stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Опциональный файловый handler с ротацией
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Глобальный логгер создается только при необходимости
def get_logger() -> logging.Logger:
    """Возвращает глобальный логгер для приложения"""
    return setup_logger() 