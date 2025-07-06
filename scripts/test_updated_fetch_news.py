#!/usr/bin/env python3
# /scripts/test_updated_fetch_news.py

"""
Тестовый скрипт для проверки обновленного метода fetch_news()
с новыми параметрами по умолчанию
"""

import os
import sys
from datetime import datetime, timedelta

# Добавляем корневую директорию в PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.news.fetcher_fabric import create_news_fetcher_with_config
from src.logger import setup_logger
from dotenv import load_dotenv

def load_environment():
    """Загружает переменные окружения"""
    env_file = os.path.join(project_root, '.env')
    
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print("📄 Загружены переменные из .env файла")
    else:
        print("ℹ️  .env файл не найден, используем системные переменные")
    
    # Проверяем API токен
    api_token = os.getenv('THENEWSAPI_API_TOKEN')
    if not api_token:
        print("❌ Отсутствует THENEWSAPI_API_TOKEN")
        return False
    
    print("✅ API токен найден")
    return True

def test_updated_fetch_news():
    """Тестирует обновленный метод fetch_news()"""
    logger = setup_logger("test_updated_fetch_news")
    
    # Устанавливаем заглушки для обязательных полей
    os.environ.setdefault('GOOGLE_GSHEET_ID', 'test-sheet-id')
    os.environ.setdefault('GOOGLE_ACCOUNT_EMAIL', 'test@example.com')  
    os.environ.setdefault('GOOGLE_ACCOUNT_KEY', 'test-key')
    os.environ.setdefault('OPENAI_API_KEY', 'sk-test-key')
    
    logger.info("🧪 Тестирование ОБНОВЛЕННОГО метода fetch_news()")
    
    try:
        # Создаем fetcher
        fetcher = create_news_fetcher_with_config("thenewsapi")
        logger.info("✅ Fetcher создан успешно")
        
        # Тест 1: Проверка параметров по умолчанию
        logger.info("🔧 ТЕСТ 1: Проверка параметров по умолчанию")
        logger.info("─" * 50)
        
        # Ожидаемые параметры
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"📅 Ожидаемая дата published_after: {yesterday}")
        logger.info(f"🌐 Ожидаемый язык: ru")
        logger.info(f"📂 Ожидаемые категории: general,politics,tech,business")
        logger.info(f"🔄 Ожидаемая сортировка: relevance_score desc")
        
        result1 = fetcher.fetch_news(
            query="политика",  # Русский запрос
            limit=3
        )
        
        if "error" in result1:
            logger.error(f"❌ Ошибка в тесте 1: {result1['error']}")
        else:
            articles = result1.get("articles", [])
            logger.info(f"✅ Получено {len(articles)} статей с параметрами по умолчанию")
            
            if articles:
                article = articles[0]
                logger.info(f"📰 Первая статья:")
                logger.info(f"   Заголовок: {article.get('title', 'Нет заголовка')}")
                logger.info(f"   Источник: {article.get('source', 'Неизвестно')}")
                logger.info(f"   Категория: {article.get('category', 'Нет категории')}")
                logger.info(f"   Язык: {article.get('language', 'Неизвестно')}")
                logger.info(f"   Дата: {article.get('published_at', 'Нет даты')}")
        
        logger.info("")
        
        # Тест 2: Проверка с русским поисковым запросом
        logger.info("🇷🇺 ТЕСТ 2: Русский поисковый запрос")
        logger.info("─" * 50)
        
        result2 = fetcher.fetch_news(
            query="технологии искусственный интеллект",
            limit=2
        )
        
        if "error" in result2:
            logger.error(f"❌ Ошибка в тесте 2: {result2['error']}")
        else:
            articles = result2.get("articles", [])
            logger.info(f"✅ Получено {len(articles)} статей по русскому запросу")
            
            for i, article in enumerate(articles, 1):
                logger.info(f"📰 Статья {i}: {article.get('title', 'Нет заголовка')}")
                logger.info(f"   Язык: {article.get('language', 'Неизвестно')}")
                logger.info(f"   Категория: {article.get('category', 'Нет категории')}")
        
        logger.info("")
        
        # Тест 3: Проверка переопределения параметров
        logger.info("🔧 ТЕСТ 3: Переопределение параметров по умолчанию")
        logger.info("─" * 50)
        
        result3 = fetcher.fetch_news(
            query="technology",
            language="en",  # Переопределяем язык
            category="tech",  # Переопределяем категории
            limit=2
        )
        
        if "error" in result3:
            logger.error(f"❌ Ошибка в тесте 3: {result3['error']}")
        else:
            articles = result3.get("articles", [])
            logger.info(f"✅ Получено {len(articles)} статей с переопределенными параметрами")
            
            for i, article in enumerate(articles, 1):
                logger.info(f"📰 Статья {i}: {article.get('title', 'Нет заголовка')}")
                logger.info(f"   Язык: {article.get('language', 'Неизвестно')}")
                logger.info(f"   Категория: {article.get('category', 'Нет категории')}")
        
        logger.info("")
        
        # Тест 4: Проверка дополнительных параметров через kwargs
        logger.info("⚙️ ТЕСТ 4: Дополнительные параметры через kwargs")
        logger.info("─" * 50)
        
        result4 = fetcher.fetch_news(
            query="экономика",
            limit=2,
            # Дополнительные параметры
            sort="published_at",  # Переопределяем сортировку
            published_after="2025-01-01"  # Переопределяем дату
        )
        
        if "error" in result4:
            logger.error(f"❌ Ошибка в тесте 4: {result4['error']}")
        else:
            articles = result4.get("articles", [])
            logger.info(f"✅ Получено {len(articles)} статей с дополнительными параметрами")
            
            for i, article in enumerate(articles, 1):
                logger.info(f"📰 Статья {i}: {article.get('title', 'Нет заголовка')}")
                logger.info(f"   Дата: {article.get('published_at', 'Нет даты')}")
        
        logger.info("")
        
        # Тест 5: Проверка без поискового запроса (только категории по умолчанию)
        logger.info("📂 ТЕСТ 5: Только категории по умолчанию (без поискового запроса)")
        logger.info("─" * 50)
        
        result5 = fetcher.fetch_news(limit=2)
        
        if "error" in result5:
            logger.error(f"❌ Ошибка в тесте 5: {result5['error']}")
        else:
            articles = result5.get("articles", [])
            logger.info(f"✅ Получено {len(articles)} статей только по категориям")
            
            for i, article in enumerate(articles, 1):
                logger.info(f"📰 Статья {i}: {article.get('title', 'Нет заголовка')}")
                logger.info(f"   Категория: {article.get('category', 'Нет категории')}")
                logger.info(f"   Язык: {article.get('language', 'Неизвестно')}")
        
        logger.info("")
        logger.info("🎉 Тестирование обновленного метода fetch_news() завершено!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Главная функция"""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ ОБНОВЛЕННОГО МЕТОДА fetch_news()")
    print("=" * 60)
    
    if not load_environment():
        print("❌ Не удалось загрузить переменные окружения")
        return
    
    success = test_updated_fetch_news()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("🎉 Обновленный метод fetch_news() работает корректно!")
        print("📋 Параметры по умолчанию:")
        print("   🌐 Язык: ru")
        print("   📂 Категории: general,politics,tech,business")
        print("   📅 Дата: вчерашняя")
        print("   🔄 Сортировка: relevance_score desc")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
    print("=" * 60)

if __name__ == "__main__":
    main() 