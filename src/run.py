# /src/run.py
# Минимальная обертка для cron запуска

import sys
from datetime import datetime, timezone

from src.services.news.runner import run_news_parsing_sync
from src.logger import setup_logger


def main() -> int:
    """
    Главная функция для cron запуска
    
    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    # Настройка логирования
    logger = setup_logger(__name__)
    
    logger.info("☕ Coffee Grinder v2 - News Processing Pipeline")
    logger.info(f"⏰ Запуск: {datetime.now(timezone.utc).isoformat()}")
    
    try:
        # Запуск обработки новостей с настройками по умолчанию
        results = run_news_parsing_sync()
        
        # Определяем код возврата
        exit_code = 0 if results["success"] else 1
        
        if exit_code == 0:
            logger.info("🎉 Обработка завершена успешно")
            if "providers_processed" in results:
                logger.info(f"📊 Обработано провайдеров: {results['providers_processed']}")
        else:
            logger.error("💔 Обработка завершена с ошибками")
            if "error" in results:
                logger.error(f"  - {results['error']}")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

