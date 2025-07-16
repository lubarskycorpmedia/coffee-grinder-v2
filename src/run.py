# /src/run.py
# glue-скрипт: orchestrate()

import argparse
import sys
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.services.news.news_processor import NewsProcessor, create_news_processor
from src.config import get_news_providers_settings, get_ai_settings, get_google_settings
from src.logger import setup_logger


def create_argument_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Coffee Grinder v2 - News Processing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python -m src.run                          # Полный pipeline
  python -m src.run --dry-run                # Только проверка без экспорта
  python -m src.run --query "AI technology"  # Поиск по запросу
  python -m src.run --category tech --limit 20  # Категория и лимит
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Режим проверки: выполнить fetching и processing, но не экспортировать в Google Sheets"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Поисковый запрос для новостей"
    )
    
    parser.add_argument(
        "--category",
        type=str,
        help="Категория новостей (tech, business, sports, etc.)"
    )
    
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help="Язык новостей (по умолчанию: en)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Максимальное количество новостей для обработки (по умолчанию: 50)"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Провайдер новостей (по умолчанию: из конфигурации)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Подробное логирование"
    )
    
    return parser


def validate_environment() -> Dict[str, Any]:
    """
    Проверяет доступность всех необходимых настроек
    
    Returns:
        Словарь с результатами проверки
    """
    logger = setup_logger(__name__)
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Проверяем настройки новостных провайдеров
    try:
        providers_settings = get_news_providers_settings()
        enabled_providers = providers_settings.get_enabled_providers()
        
        if not enabled_providers:
            validation_results["errors"].append("Нет включенных провайдеров новостей")
            validation_results["valid"] = False
        else:
            logger.info(f"✓ News API настройки корректны. Включенные провайдеры: {list(enabled_providers.keys())}")
    except Exception as e:
        validation_results["errors"].append(f"Ошибка настроек новостей: {str(e)}")
        validation_results["valid"] = False
    
    # Проверяем настройки AI
    try:
        ai_settings = get_ai_settings()
        if not ai_settings.OPENAI_API_KEY:
            validation_results["errors"].append("OPENAI_API_KEY не настроен")
            validation_results["valid"] = False
        else:
            logger.info("✓ OpenAI настройки корректны")
    except Exception as e:
        validation_results["errors"].append(f"Ошибка настроек AI: {str(e)}")
        validation_results["valid"] = False
    
    # Проверяем настройки Google (опционально для dry-run)
    try:
        google_settings = get_google_settings()
        if not google_settings.GOOGLE_SHEET_ID:
            validation_results["warnings"].append("GOOGLE_SHEET_ID не настроен - экспорт будет недоступен")
        elif not google_settings.GOOGLE_ACCOUNT_KEY:
            validation_results["warnings"].append("GOOGLE_ACCOUNT_KEY не настроен - экспорт будет недоступен")
        else:
            logger.info("✓ Google Sheets настройки корректны")
    except Exception as e:
        validation_results["warnings"].append(f"Настройки Google Sheets недоступны: {str(e)}")
    
    return validation_results


async def run_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Запускает полный pipeline обработки новостей
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        Результаты выполнения pipeline
    """
    from src.services.news.runner import run_pipeline_from_args
    
    logger = setup_logger(__name__)
    logger.info("🔄 Запуск через унифицированный runner")
    
    try:
        results = await run_pipeline_from_args(args)
        
        # Логирование результатов
        if results["success"]:
            logger.info("🎉 Обработка завершена успешно!")
            if "providers_processed" in results:
                logger.info(f"📊 Обработано провайдеров: {results['providers_processed']}")
        else:
            logger.error("💔 Обработка завершена с ошибками:")
            if "error" in results:
                logger.error(f"  - {results['error']}")
        
        return results
        
    except Exception as e:
        error_msg = f"Критическая ошибка pipeline: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


def main() -> int:
    """
    Главная функция orchestrator
    
    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Настройка логирования
    logger = setup_logger(__name__)
    
    if args.verbose:
        logger.info("🔧 Подробное логирование включено")
    
    logger.info("☕ Coffee Grinder v2 - News Processing Pipeline")
    logger.info(f"⏰ Запуск: {datetime.now(timezone.utc).isoformat()}")
    
    # Запуск pipeline
    results = asyncio.run(run_pipeline(args))
    
    # Определяем код возврата
    exit_code = 0 if results["success"] else 1
    
    if exit_code == 0:
        logger.info("🎉 Работа завершена успешно")
    else:
        logger.error("💔 Работа завершена с ошибками")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

