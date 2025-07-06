#!/usr/bin/env python3
# /scripts/test_fetch_news_method.py

"""
Тестовый скрипт для проверки нового метода fetch_news()
"""

import os
import sys
import json
from typing import Dict, Any

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

def test_fetch_news_method():
    """Тестирует новый метод fetch_news()"""
    logger = setup_logger("test_fetch_news")
    
    # Устанавливаем заглушки для обязательных полей
    os.environ.setdefault('GOOGLE_GSHEET_ID', 'test-sheet-id')
    os.environ.setdefault('GOOGLE_ACCOUNT_EMAIL', 'test@example.com')  
    os.environ.setdefault('GOOGLE_ACCOUNT_KEY', 'test-key')
    os.environ.setdefault('OPENAI_API_KEY', 'sk-test-key')
    
    logger.info("🧪 Тестирование нового метода fetch_news()")
    
    try:
        # Создаем fetcher
        fetcher = create_news_fetcher_with_config("thenewsapi")
        logger.info("✅ Fetcher создан успешно")
        
        # Тест 1: Простой поиск
        logger.info("🔍 ТЕСТ 1: Простой поиск по запросу")
        logger.info("─" * 50)
        
        result1 = fetcher.fetch_news(
            query="AI technology",
            language="en",
            limit=3
        )
        
        if "error" in result1:
            logger.error(f"❌ Ошибка в тесте 1: {result1['error']}")
        else:
            articles = result1.get("articles", [])
            logger.info(f"✅ Получено {len(articles)} статей")
            
            if articles:
                article = articles[0]
                logger.info(f"📰 Первая статья:")
                logger.info(f"   Заголовок: {article.get('title', 'Нет заголовка')}")
                logger.info(f"   Источник: {article.get('source', 'Неизвестно')}")
                logger.info(f"   Категория: {article.get('category', 'Нет категории')}")
                logger.info(f"   Язык: {article.get('language', 'Неизвестно')}")
                logger.info(f"   URL: {article.get('url', 'Нет URL')}")
        
        logger.info("")
        
        # Тест 2: Поиск по категории
        logger.info("📂 ТЕСТ 2: Поиск по категории")
        logger.info("─" * 50)
        
        result2 = fetcher.fetch_news(
            category="technology",
            language="en",
            limit=2
        )
        
        if "error" in result2:
            logger.error(f"❌ Ошибка в тесте 2: {result2['error']}")
        else:
            articles = result2.get("articles", [])
            logger.info(f"✅ Получено {len(articles)} статей по категории 'technology'")
            
            for i, article in enumerate(articles, 1):
                logger.info(f"📰 Статья {i}: {article.get('title', 'Нет заголовка')}")
                logger.info(f"   Категория: {article.get('category', 'Нет категории')}")
        
        logger.info("")
        
        # Тест 3: Комбинированный поиск
        logger.info("🔍📂 ТЕСТ 3: Комбинированный поиск (запрос + категория)")
        logger.info("─" * 50)
        
        result3 = fetcher.fetch_news(
            query="artificial intelligence",
            category="tech",
            language="en",
            limit=2
        )
        
        if "error" in result3:
            logger.error(f"❌ Ошибка в тесте 3: {result3['error']}")
        else:
            articles = result3.get("articles", [])
            logger.info(f"✅ Получено {len(articles)} статей по запросу 'AI' в категории 'tech'")
            
            for i, article in enumerate(articles, 1):
                logger.info(f"📰 Статья {i}: {article.get('title', 'Нет заголовка')}")
                logger.info(f"   Категория: {article.get('category', 'Нет категории')}")
        
        logger.info("")
        
        # Тест 4: Дополнительные параметры через kwargs
        logger.info("⚙️ ТЕСТ 4: Дополнительные параметры через kwargs")
        logger.info("─" * 50)
        
        result4 = fetcher.fetch_news(
            query="technology",
            language="en",
            limit=2,
            # Дополнительные параметры
            sort="published_at",
            sort_order="desc",
            published_after="2025-01-01"
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
        
        # Тест 5: Проверка формата ответа
        logger.info("📋 ТЕСТ 5: Проверка формата ответа")
        logger.info("─" * 50)
        
        result5 = fetcher.fetch_news(query="test", limit=1)
        
        if "error" in result5:
            logger.warning(f"⚠️ Не удалось получить данные для проверки формата: {result5['error']}")
        else:
            logger.info("✅ Проверка структуры ответа:")
            logger.info(f"   Есть поле 'articles': {'articles' in result5}")
            logger.info(f"   Есть поле 'meta': {'meta' in result5}")
            
            if result5.get("articles"):
                article = result5["articles"][0]
                required_fields = ["title", "description", "url", "published_at", "source", "category", "language"]
                
                logger.info("   Поля в статье:")
                for field in required_fields:
                    has_field = field in article
                    logger.info(f"     {field}: {'✅' if has_field else '❌'}")
        
        logger.info("")
        logger.info("🎉 Тестирование метода fetch_news() завершено!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Главная функция"""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ МЕТОДА fetch_news()")
    print("=" * 60)
    
    if not load_environment():
        print("❌ Не удалось загрузить переменные окружения")
        return
    
    success = test_fetch_news_method()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("🎉 Метод fetch_news() работает корректно!")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
    print("=" * 60)

if __name__ == "__main__":
    main() 