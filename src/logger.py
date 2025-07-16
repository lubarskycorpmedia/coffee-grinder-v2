# /src/logger.py
# Настройка логирования 

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
from src.config import get_log_level


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
        log_level_str = get_log_level()
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
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
    
    # Файловый handler с ротацией (по умолчанию включен)
    if log_file is None:
        # Дефолтный путь для файла логов
        import os
        os.makedirs("/app/logs", exist_ok=True)
        log_file = "/app/logs/app.log"
    
    if log_file:
        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Если не можем создать файл, просто продолжаем без файлового логирования
            print(f"Warning: Could not create log file {log_file}: {e}")
    
    return logger


# Глобальный логгер создается только при необходимости
def get_logger() -> logging.Logger:
    """Возвращает глобальный логгер для приложения"""
    return setup_logger() 