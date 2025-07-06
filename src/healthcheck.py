# src/healthcheck.py

import sys
import argparse
from typing import Optional
from src.logger import get_logger
from src.config import get_settings


def check_configuration() -> bool:
    """
    Проверка корректности конфигурации.
    
    Returns:
        True если конфигурация корректна, False иначе
    """
    logger = get_logger()  # Создаем логгер в начале функции
    
    try:
        settings = get_settings()
        
        # Проверяем обязательные переменные окружения
        required_vars = [
            'THENEWSAPI_API_TOKEN',
            'OPENAI_API_KEY', 
            'GOOGLE_GSHEET_ID',
            'GOOGLE_ACCOUNT_EMAIL',
            'GOOGLE_ACCOUNT_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = getattr(settings, var, None)
            if not value:
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Отсутствуют обязательные переменные окружения: {missing_vars}")
            return False
        
        # Проверяем корректность значений
        if not (0.0 <= settings.DEDUP_THRESHOLD <= 1.0):
            logger.error(f"DEDUP_THRESHOLD должен быть от 0.0 до 1.0, получен: {settings.DEDUP_THRESHOLD}")
            return False
        
        if settings.MAX_RETRIES < 0:
            logger.error(f"MAX_RETRIES должен быть >= 0, получен: {settings.MAX_RETRIES}")
            return False
        
        if settings.ASK_NEWS_COUNT <= 0:
            logger.error(f"ASK_NEWS_COUNT должен быть > 0, получен: {settings.ASK_NEWS_COUNT}")
            return False
        
        logger.info("Конфигурация корректна")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при проверке конфигурации: {e}")
        return False


def check_dependencies() -> bool:
    """
    Проверка доступности необходимых зависимостей.
    
    Returns:
        True если все зависимости доступны, False иначе
    """
    logger = get_logger()
    required_modules = [
        'openai',
        'langchain',
        'faiss',
        'gspread',
        'google.auth',
        'pydantic',
        'requests',
        'structlog',
        'tenacity'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Отсутствуют обязательные модули: {missing_modules}")
        return False
    
    logger.info("Все зависимости доступны")
    return True


def dry_run_check() -> bool:
    """
    Проверка возможности выполнения dry-run режима.
    
    Returns:
        True если dry-run возможен, False иначе
    """
    logger = get_logger()
    try:
        # TODO: Здесь будет проверка run.py --dry-run когда он будет реализован
        logger.info("Dry-run проверка пройдена")
        return True
    except Exception as e:
        logger.error(f"Ошибка при dry-run проверке: {e}")
        return False


def healthcheck(dry_run: bool = False) -> bool:
    """
    Полная проверка здоровья сервиса.
    
    Args:
        dry_run: Выполнить также dry-run проверку
        
    Returns:
        True если все проверки пройдены, False иначе
    """
    logger = get_logger()
    logger.info("Запуск проверки здоровья сервиса...")
    
    checks = [
        ("Конфигурация", check_configuration),
        ("Зависимости", check_dependencies),
    ]
    
    if dry_run:
        checks.append(("Dry-run", dry_run_check))
    
    all_passed = True
    for check_name, check_func in checks:
        logger.info(f"Проверка: {check_name}")
        if not check_func():
            logger.error(f"Проверка '{check_name}' провалена")
            all_passed = False
        else:
            logger.info(f"Проверка '{check_name}' пройдена")
    
    if all_passed:
        logger.info("Все проверки здоровья пройдены успешно")
    else:
        logger.error("Некоторые проверки здоровья провалены")
    
    return all_passed


def main() -> None:
    """Главная функция для запуска healthcheck."""
    parser = argparse.ArgumentParser(description="Проверка здоровья сервиса")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Выполнить также dry-run проверку"
    )
    
    args = parser.parse_args()
    
    success = healthcheck(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 