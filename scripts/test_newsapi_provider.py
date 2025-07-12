# scripts/test_newsapi_provider.py

"""
Тестовый скрипт для проверки работы NewsAPI.org провайдера
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.news.fetcher_fabric import create_news_fetcher_from_config
from src.config import get_news_providers_settings
from src.logger import setup_logger

def test_newsapi_provider():
    """Тест работы NewsAPI провайдера"""
    logger = setup_logger(__name__)
    
    try:
        # Проверяем конфигурацию
        logger.info("Проверяем конфигурацию провайдеров...")
        providers_settings = get_news_providers_settings()
        
        newsapi_settings = providers_settings.get_provider_settings("newsapi")
        if not newsapi_settings:
            logger.error("NewsAPI провайдер не найден в конфигурации")
            return False
        
        if not newsapi_settings.enabled:
            logger.error("NewsAPI провайдер отключен в конфигурации")
            return False
        
        logger.info(f"NewsAPI настройки: enabled={newsapi_settings.enabled}, priority={newsapi_settings.priority}")
        
        # Создаем fetcher
        logger.info("Создаем NewsAPI fetcher...")
        fetcher = create_news_fetcher_from_config("newsapi")
        logger.info(f"Fetcher создан: {fetcher.PROVIDER_NAME}")
        
        # Проверяем health check
        logger.info("Проверяем состояние провайдера...")
        health_result = fetcher.check_health()
        logger.info(f"Health check результат: {health_result}")
        
        if health_result.get('status') != 'healthy':
            logger.error(f"Провайдер не работает: {health_result.get('message')}")
            return False
        
        # Получаем категории и языки
        logger.info("Получаем поддерживаемые категории и языки...")
        categories = fetcher.get_categories()
        languages = fetcher.get_languages()
        
        logger.info(f"Поддерживаемые категории: {categories}")
        logger.info(f"Поддерживаемые языки: {languages}")
        
        # Тестируем получение источников
        logger.info("Получаем список источников...")
        sources_result = fetcher.get_sources(language="en", category="business")
        
        if "error" in sources_result:
            logger.error(f"Ошибка при получении источников: {sources_result['error']}")
            return False
        
        sources = sources_result.get("sources", [])
        logger.info(f"Получено источников: {len(sources)}")
        
        if sources:
            logger.info(f"Пример источника: {sources[0]['name']} ({sources[0]['id']})")
        
        # Тестируем получение новостей
        logger.info("Получаем новости по категории business...")
        news = fetcher.fetch_news(rubric="business", language="en", limit=5)
        
        logger.info(f"Получено новостей: {len(news)}")
        
        if news:
            first_article = news[0]
            logger.info(f"Пример новости:")
            logger.info(f"  Заголовок: {first_article.get('title', 'N/A')}")
            logger.info(f"  Источник: {first_article.get('source', {}).get('name', 'N/A')}")
            logger.info(f"  Дата: {first_article.get('published_at', 'N/A')}")
            logger.info(f"  URL: {first_article.get('url', 'N/A')}")
        
        # Тестируем поиск новостей
        logger.info("Тестируем поиск новостей по запросу 'technology'...")
        search_results = fetcher.search_news("technology", language="en", limit=3)
        
        logger.info(f"Найдено новостей по поиску: {len(search_results)}")
        
        if search_results:
            first_result = search_results[0]
            logger.info(f"Пример найденной новости:")
            logger.info(f"  Заголовок: {first_result.get('title', 'N/A')}")
            logger.info(f"  Источник: {first_result.get('source', {}).get('name', 'N/A')}")
        
        logger.info("✅ Все тесты NewsAPI провайдера прошли успешно!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании NewsAPI провайдера: {e}")
        return False

if __name__ == "__main__":
    success = test_newsapi_provider()
    sys.exit(0 if success else 1) 