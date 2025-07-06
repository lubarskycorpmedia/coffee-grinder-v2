# /src/run.py
# glue-скрипт: orchestrate()

import argparse
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.services.news.news_processor import NewsProcessor, create_news_processor
from src.config import get_news_settings, get_ai_settings, get_google_settings
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
        default="thenewsapi",
        choices=["thenewsapi"],
        help="Провайдер новостей (по умолчанию: thenewsapi)"
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
    
    # Проверяем настройки новостей
    try:
        news_settings = get_news_settings()
        if not news_settings.THENEWSAPI_API_TOKEN:
            validation_results["errors"].append("THENEWSAPI_API_TOKEN не настроен")
            validation_results["valid"] = False
        else:
            logger.info("✓ News API настройки корректны")
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
        if not google_settings.GOOGLE_GSHEET_ID:
            validation_results["warnings"].append("GOOGLE_GSHEET_ID не настроен - экспорт будет недоступен")
        elif not google_settings.GOOGLE_ACCOUNT_KEY:
            validation_results["warnings"].append("GOOGLE_ACCOUNT_KEY не настроен - экспорт будет недоступен")
        else:
            logger.info("✓ Google Sheets настройки корректны")
    except Exception as e:
        validation_results["warnings"].append(f"Настройки Google Sheets недоступны: {str(e)}")
    
    return validation_results


def run_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Запускает полный pipeline обработки новостей
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        Результаты выполнения pipeline
    """
    logger = setup_logger(__name__)
    
    # Валидация окружения
    logger.info("🔍 Проверка настроек окружения...")
    validation = validate_environment()
    
    if validation["errors"]:
        logger.error("❌ Критические ошибки настроек:")
        for error in validation["errors"]:
            logger.error(f"  - {error}")
        return {"success": False, "errors": validation["errors"]}
    
    if validation["warnings"]:
        logger.warning("⚠️ Предупреждения:")
        for warning in validation["warnings"]:
            logger.warning(f"  - {warning}")
    
    # Создаем процессор новостей
    logger.info(f"🚀 Запуск pipeline (dry-run: {args.dry_run})")
    
    try:
        processor = create_news_processor(
            news_provider=args.provider,
            max_news_items=args.limit,
            fail_on_errors=False  # Продолжаем работу при ошибках
        )
        
        # Запускаем полный pipeline
        results = processor.run_full_pipeline(
            query=args.query,
            category=args.category,
            language=args.language,
            limit=args.limit,
            export_to_sheets=not args.dry_run,  # Экспорт только если не dry-run
            append_to_sheets=True
        )
        
        # Логируем результаты
        logger.info("📊 Результаты выполнения:")
        logger.info(f"  📰 Получено новостей: {results['fetched_count']}")
        logger.info(f"  🔄 Обработано новостей: {results['processed_count']}")
        logger.info(f"  📋 Экспортировано: {results['exported_count']}")
        logger.info(f"  🔍 Найдено дубликатов: {results['duplicates_found']}")
        logger.info(f"  ⏱️ Время выполнения: {results['duration_seconds']:.2f} сек")
        
        if args.dry_run:
            logger.info("🔍 Режим dry-run: экспорт в Google Sheets пропущен")
        
        if results["success"]:
            logger.info("✅ Pipeline выполнен успешно!")
        else:
            logger.error("❌ Pipeline завершен с ошибками")
            if results.get("errors"):
                for error in results["errors"]:
                    logger.error(f"  - {error}")
        
        return results
        
    except Exception as e:
        error_msg = f"Критическая ошибка pipeline: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return {
            "success": False,
            "errors": [error_msg],
            "fetched_count": 0,
            "processed_count": 0,
            "exported_count": 0
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
    results = run_pipeline(args)
    
    # Определяем код возврата
    exit_code = 0 if results["success"] else 1
    
    if exit_code == 0:
        logger.info("🎉 Работа завершена успешно")
    else:
        logger.error("💔 Работа завершена с ошибками")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

