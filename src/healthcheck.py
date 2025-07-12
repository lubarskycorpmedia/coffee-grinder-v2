# src/healthcheck.py

import sys
import argparse
from typing import Optional
from src.logger import setup_logger
from src.config import get_news_providers_settings, get_ai_settings, get_google_settings


def check_configuration() -> bool:
    """
    Проверка корректности конфигурации.
    
    Returns:
        True если конфигурация корректна, False иначе
    """
    logger = setup_logger(__name__)
    
    try:
        # Проверяем настройки новостных провайдеров
        try:
            providers_settings = get_news_providers_settings()
            enabled_providers = providers_settings.get_enabled_providers()
            
            if not enabled_providers:
                logger.error("Нет включенных провайдеров новостей")
                return False
            
            logger.info(f"✓ Настройки новостей корректны. Включенные провайдеры: {list(enabled_providers.keys())}")
        except Exception as e:
            logger.error(f"Ошибка настроек новостей: {e}")
            return False
        
        # Проверяем настройки AI
        try:
            ai_settings = get_ai_settings()
            if not ai_settings.OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY не настроен")
                return False
            logger.info("✓ Настройки AI корректны")
        except Exception as e:
            logger.error(f"Ошибка настроек AI: {e}")
            return False
        
        # Проверяем настройки Google (опционально)
        try:
            google_settings = get_google_settings()
            if not google_settings.GOOGLE_SHEET_ID:
                logger.warning("GOOGLE_SHEET_ID не настроен - экспорт будет недоступен")
            elif not google_settings.GOOGLE_ACCOUNT_KEY:
                logger.warning("GOOGLE_ACCOUNT_KEY не настроен - экспорт будет недоступен")
            else:
                logger.info("✓ Настройки Google Sheets корректны")
        except Exception as e:
            logger.warning(f"Настройки Google Sheets недоступны: {e}")
        
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
    logger = setup_logger(__name__)
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
    logger = setup_logger(__name__)
    try:
        # Проверяем, что можем импортировать основные модули
        from src.services.news.news_processor import create_news_processor
        from src.run import validate_environment
        
        # Проверяем валидацию окружения
        validation = validate_environment()
        if validation["errors"]:
            logger.error(f"Ошибки валидации окружения: {validation['errors']}")
            return False
        
        if validation["warnings"]:
            logger.warning(f"Предупреждения валидации: {validation['warnings']}")
        
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
    logger = setup_logger(__name__)
    logger.info("🔍 Запуск проверки здоровья сервиса...")
    
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
            logger.error(f"❌ Проверка '{check_name}' провалена")
            all_passed = False
        else:
            logger.info(f"✅ Проверка '{check_name}' пройдена")
    
    if all_passed:
        logger.info("🎉 Все проверки здоровья пройдены успешно")
    else:
        logger.error("💔 Некоторые проверки здоровья провалены")
    
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