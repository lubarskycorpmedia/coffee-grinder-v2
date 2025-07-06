# scripts/debug_thenewsapi.py
"""
Отладочный скрипт для проверки TheNewsAPI
"""
import sys
import os
import json
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.news.fetchers.thenewsapi_com import TheNewsAPIFetcher
from src.config import get_settings


def debug_api_calls():
    """Отладка различных вызовов API"""
    print("🔍 Отладка TheNewsAPI")
    print("=" * 50)
    
    # Получаем настройки
    settings = get_settings()
    
    if not settings.THENEWSAPI_API_TOKEN:
        print("❌ THENEWSAPI_API_TOKEN не найден в настройках")
        return
    
    # Создаем fetcher
    fetcher = TheNewsAPIFetcher(settings.THENEWSAPI_API_TOKEN)
    
    # Тест 1: Простой запрос без фильтров
    print("\n1️⃣ Тест: Простой запрос без фильтров")
    print("-" * 40)
    
    try:
        result = fetcher.fetch_all_news(
            language="en",
            limit=5
        )
        
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
        else:
            articles = result.get("data", [])
            print(f"✅ Получено статей: {len(articles)}")
            if articles:
                print(f"   Первая статья: {articles[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    # Тест 2: Запрос с категориями
    print("\n2️⃣ Тест: Запрос с категориями")
    print("-" * 40)
    
    try:
        result = fetcher.fetch_all_news(
            language="en",
            categories="tech,business",
            limit=5
        )
        
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
        else:
            articles = result.get("data", [])
            print(f"✅ Получено статей: {len(articles)}")
            if articles:
                print(f"   Первая статья: {articles[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    # Тест 3: Запрос с поиском
    print("\n3️⃣ Тест: Запрос с поиском")
    print("-" * 40)
    
    try:
        result = fetcher.fetch_all_news(
            search="artificial intelligence",
            language="en",
            limit=5
        )
        
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
        else:
            articles = result.get("data", [])
            print(f"✅ Получено статей: {len(articles)}")
            if articles:
                print(f"   Первая статья: {articles[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    # Тест 4: Запрос с датой (как в fetch_news)
    print("\n4️⃣ Тест: Запрос с вчерашней датой")
    print("-" * 40)
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"   Дата: {yesterday}")
    
    try:
        result = fetcher.fetch_all_news(
            language="en",
            categories="general,politics,tech,business",
            published_after=yesterday,
            limit=5
        )
        
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
        else:
            articles = result.get("data", [])
            print(f"✅ Получено статей: {len(articles)}")
            if articles:
                print(f"   Первая статья: {articles[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    # Тест 5: Запрос с большим временным диапазоном
    print("\n5️⃣ Тест: Запрос за последние 7 дней")
    print("-" * 40)
    
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    print(f"   Дата: {week_ago}")
    
    try:
        result = fetcher.fetch_all_news(
            language="en",
            categories="tech",
            published_after=week_ago,
            limit=5
        )
        
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
        else:
            articles = result.get("data", [])
            print(f"✅ Получено статей: {len(articles)}")
            if articles:
                print(f"   Первая статья: {articles[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    # Тест 6: Проверка источников
    print("\n6️⃣ Тест: Получение источников")
    print("-" * 40)
    
    try:
        result = fetcher.get_sources(
            language="en",
            categories="tech"
        )
        
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
        else:
            sources = result.get("data", [])
            print(f"✅ Получено источников: {len(sources)}")
            if sources:
                print(f"   Первый источник: {sources[0].get('name', 'No name')}")
    except Exception as e:
        print(f"❌ Исключение: {e}")
    
    # Тест 7: Тест метода fetch_news (как в pipeline)
    print("\n7️⃣ Тест: Метод fetch_news (как в pipeline)")
    print("-" * 40)
    
    try:
        result = fetcher.fetch_news(
            query="artificial intelligence",
            categories="tech,business",
            language="en",
            limit=5
        )
        
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
        else:
            articles = result.get("articles", [])
            print(f"✅ Получено статей: {len(articles)}")
            if articles:
                print(f"   Первая статья: {articles[0].get('title', 'No title')[:50]}...")
                print(f"   Категория: {articles[0].get('category', 'No category')}")
    except Exception as e:
        print(f"❌ Исключение: {e}")


def test_raw_api_call():
    """Тест прямого вызова API"""
    print("\n🌐 Тест прямого вызова API")
    print("=" * 50)
    
    import requests
    
    settings = get_settings()
    
    if not settings.THENEWSAPI_API_TOKEN:
        print("❌ THENEWSAPI_API_TOKEN не найден в настройках")
        return
    
    # Прямой вызов API
    url = "https://api.thenewsapi.com/v1/news/all"
    params = {
        "api_token": settings.THENEWSAPI_API_TOKEN,
        "language": "en",
        "limit": 3
    }
    
    try:
        print(f"📡 Запрос: {url}")
        print(f"📋 Параметры: {json.dumps(params, indent=2)}")
        
        response = requests.get(url, params=params, timeout=30)
        
        print(f"📊 Статус: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Ответ: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"❌ Ошибка: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение: {e}")


if __name__ == "__main__":
    debug_api_calls()
    test_raw_api_call() 