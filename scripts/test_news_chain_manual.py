#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы LangChain новостной цепочки
Использует реальные данные из .env файла и реальные API вызовы
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Добавляем корневую директорию в PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.news.fetcher_fabric import create_news_fetcher_with_config
from src.langchain.news_chain import NewsItem, NewsProcessingChain
from src.openai_client import OpenAIClient
from src.logger import setup_logger

# ============================================================================
# НАСТРОЙКИ ТЕСТОВ - РЕДАКТИРУЙТЕ ПАРАМЕТРЫ ЗДЕСЬ
# ============================================================================

# Параметры для получения новостей
NEWS_FETCH_PARAMS = {
    "search": "Trump",    # Поисковый запрос
    "language": "en",                      # Язык новостей
    "limit": 10,                           # Количество новостей для обработки
    "sort": "relevance_score",             # Сортировка
    "sort_order": "desc",                  # Порядок сортировки
    "categories": "general,politics,tech,business",         # Категории
    "published_on": "2025-06-05",         # Дата публикации
}

# Параметры для обработки цепочки
CHAIN_PARAMS = {
    "similarity_threshold": 0.85,          # Порог схожести для дедупликации
    "max_news_items": 5,                   # Максимальное количество новостей на выходе
    "ranking_criteria": "relevance,freshness,source_authority",  # Критерии ранжирования
}

# ============================================================================

def load_environment():
    """Загружает переменные окружения с поддержкой .env файла"""
    # Явно указываем путь к .env в корне проекта
    env_file = os.path.join(project_root, '.env')
    
    if os.path.exists(env_file):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("📄 Загружены переменные из .env файла")
        except ImportError:
            print("⚠️  python-dotenv не установлен, используем системные переменные")
    else:
        print("ℹ️  .env файл не найден, используем системные переменные")
    
    # Проверяем наличие обязательных переменных
    required_vars = {
        'THENEWSAPI_API_TOKEN': 'API токен для TheNewsAPI',
        'OPENAI_API_KEY': 'API ключ для OpenAI',
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value == 'your_token_here' or value.startswith('sk-test'):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        print("❌ Отсутствуют или некорректны обязательные переменные:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Все необходимые переменные окружения найдены")
    return True


def convert_api_news_to_news_items(api_news: List[Dict]) -> List[NewsItem]:
    """Конвертирует новости из API в объекты NewsItem"""
    news_items = []
    
    for news in api_news:
        try:
            # Парсим дату публикации
            published_at = datetime.fromisoformat(
                news.get('published_at', '').replace('Z', '+00:00')
            ) if news.get('published_at') else datetime.now()
            
            news_item = NewsItem(
                title=news.get('title', ''),
                description=news.get('description', ''),
                url=news.get('url', ''),
                published_at=published_at,
                source=news.get('source', ''),
                category=news.get('category'),
                language=news.get('language')
            )
            
            news_items.append(news_item)
            
        except Exception as e:
            print(f"⚠️ Ошибка при конвертации новости: {e}")
            continue
    
    return news_items


def print_news_item_details(news_item: NewsItem, index: int):
    """Выводит детальную информацию о новости"""
    print(f"📄 Новость {index}:")
    print(f"   Заголовок: {news_item.title}")
    print(f"   Описание: {news_item.description[:100]}..." if len(news_item.description) > 100 else f"   Описание: {news_item.description}")
    print(f"   Источник: {news_item.source}")
    print(f"   URL: {news_item.url}")
    print(f"   Дата: {news_item.published_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Категория: {news_item.category}")
    print(f"   Язык: {news_item.language}")
    print(f"   Релевантность: {news_item.relevance_score:.2f}")
    print(f"   Схожесть: {news_item.similarity_score:.2f}")
    print(f"   Дубликат: {'Да' if news_item.is_duplicate else 'Нет'}")
    if news_item.duplicate_of:
        print(f"   Дубликат от: {news_item.duplicate_of}")
    if news_item.embedding is not None:
        print(f"   Эмбеддинг: {len(news_item.embedding)} измерений")
    print()


def test_news_processing_chain():
    """Тестирует полную цепочку обработки новостей"""
    logger = setup_logger("test_news_chain")
    
    logger.info("🚀 Тестирование LangChain новостной цепочки...")
    logger.info("=" * 60)
    
    try:
        # Шаг 1: Получаем новости через fetcher
        logger.info("📰 ШАГ 1: Получение новостей через fetcher")
        logger.info("─" * 50)
        
        # Показываем параметры запроса
        logger.info("📋 Параметры запроса новостей:")
        for key, value in NEWS_FETCH_PARAMS.items():
            logger.info(f"  - {key}: {value}")
        
        fetcher = create_news_fetcher_with_config("thenewsapi")
        raw_news = fetcher.fetch_all_news(**NEWS_FETCH_PARAMS)
        
        if "error" in raw_news:
            logger.error(f"❌ Ошибка получения новостей: {raw_news['error']}")
            return False
        
        api_news = raw_news.get('data', [])
        logger.info(f"✅ Получено {len(api_news)} новостей из API")
        
        if not api_news:
            logger.warning("⚠️ Новости не найдены, проверьте параметры запроса")
            return False
        
        # Конвертируем в объекты NewsItem
        news_items = convert_api_news_to_news_items(api_news)
        logger.info(f"✅ Конвертировано {len(news_items)} новостей в NewsItem")
        
        print("\n📋 Первые 3 новости до обработки:")
        for i, news_item in enumerate(news_items[:3], 1):
            print_news_item_details(news_item, i)
        
        # Шаг 2: Создаем OpenAI клиент
        logger.info("🤖 ШАГ 2: Создание OpenAI клиента")
        logger.info("─" * 50)
        
        openai_client = OpenAIClient()
        logger.info("✅ OpenAI клиент создан успешно")
        
        # Шаг 3: Создаем цепочку обработки
        logger.info("🔗 ШАГ 3: Создание цепочки обработки")
        logger.info("─" * 50)
        
        # Показываем параметры цепочки
        logger.info("📋 Параметры цепочки:")
        for key, value in CHAIN_PARAMS.items():
            logger.info(f"  - {key}: {value}")
        
        chain = NewsProcessingChain(
            openai_client=openai_client,
            similarity_threshold=CHAIN_PARAMS["similarity_threshold"],
            max_news_items=CHAIN_PARAMS["max_news_items"]
        )
        logger.info("✅ Цепочка обработки создана успешно")
        
        # Шаг 4: Обрабатываем новости через цепочку
        logger.info("⚙️ ШАГ 4: Обработка новостей через цепочку")
        logger.info("─" * 50)
        
        logger.info("🔄 Запуск обработки (это может занять некоторое время)...")
        
        processed_news = chain.process_news(
            news_items=news_items,
            ranking_criteria=CHAIN_PARAMS["ranking_criteria"]
        )
        
        logger.info(f"✅ Обработка завершена! Получено {len(processed_news)} новостей")
        
        # Шаг 5: Анализируем результаты
        logger.info("📊 ШАГ 5: Анализ результатов")
        logger.info("─" * 50)
        
        # Статистика по дедупликации
        total_news = len(news_items)
        unique_news = len([n for n in news_items if not n.is_duplicate])
        duplicates = total_news - unique_news
        
        logger.info(f"📈 Статистика обработки:")
        logger.info(f"  - Входящих новостей: {total_news}")
        logger.info(f"  - Уникальных новостей: {unique_news}")
        logger.info(f"  - Найдено дубликатов: {duplicates}")
        logger.info(f"  - Итоговых новостей: {len(processed_news)}")
        
        # Показываем обработанные новости
        print("\n🎯 ИТОГОВЫЕ ОБРАБОТАННЫЕ НОВОСТИ:")
        print("=" * 60)
        
        for i, news_item in enumerate(processed_news, 1):
            print_news_item_details(news_item, i)
        
        # Показываем найденные дубликаты (если есть)
        duplicates_found = [n for n in news_items if n.is_duplicate]
        if duplicates_found:
            print("\n🔍 НАЙДЕННЫЕ ДУБЛИКАТЫ:")
            print("=" * 60)
            for i, news_item in enumerate(duplicates_found, 1):
                print_news_item_details(news_item, i)
        
        # Шаг 6: Тестируем отдельные компоненты
        logger.info("🧪 ШАГ 6: Тестирование отдельных компонентов")
        logger.info("─" * 50)
        
        # Тестируем генерацию эмбеддингов
        test_text = "Artificial intelligence is transforming the technology industry"
        logger.info(f"🔤 Тестируем эмбеддинги для текста: '{test_text}'")
        
        embeddings = chain.embeddings.embed_documents([test_text])
        logger.info(f"✅ Сгенерирован эмбеддинг размером {len(embeddings[0])} измерений")
        
        # Тестируем ранжирование
        logger.info("🏆 Тестируем ранжирование одной новости")
        if processed_news:
            test_news = processed_news[0]
            ranked_news = chain.rank_news([test_news], CHAIN_PARAMS["ranking_criteria"])
            logger.info(f"✅ Ранжирование выполнено, оценка: {ranked_news[0].relevance_score:.2f}")
        
        logger.info("\n🎉 Тестирование завершено успешно!")
        logger.info("✅ Все компоненты цепочки работают корректно")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return False


def main():
    """Главная функция тестирования"""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ LANGCHAIN НОВОСТНОЙ ЦЕПОЧКИ")
    print("=" * 60)
    
    # Показываем текущие настройки
    print("\n📋 ТЕКУЩИЕ НАСТРОЙКИ ТЕСТОВ:")
    print(f"📰 Параметры новостей: {len(NEWS_FETCH_PARAMS)} параметров")
    print(f"🔗 Параметры цепочки: {len(CHAIN_PARAMS)} параметров")
    print("💡 Для изменения параметров отредактируйте секцию 'НАСТРОЙКИ ТЕСТОВ' в начале скрипта")
    
    # Загружаем переменные окружения
    if not load_environment():
        print("\n❌ Не удалось загрузить необходимые переменные окружения")
        print("💡 Убедитесь, что в .env файле указаны корректные THENEWSAPI_API_TOKEN и OPENAI_API_KEY")
        return
    
    # Устанавливаем заглушки для других полей
    os.environ.setdefault('GOOGLE_GSHEET_ID', 'test-sheet-id')
    os.environ.setdefault('GOOGLE_ACCOUNT_EMAIL', 'test@example.com')  
    os.environ.setdefault('GOOGLE_ACCOUNT_KEY', 'test-key')
    
    # Тестируем цепочку
    print("\n🔑 Тестируем с реальными API...")
    success = test_news_processing_chain()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("🎉 LangChain новостная цепочка работает корректно!")
        print("💡 Теперь можно интегрировать в основное приложение")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
        print("💡 Проверьте API ключи и подключение к интернету")
    print("=" * 60)


if __name__ == "__main__":
    main() 