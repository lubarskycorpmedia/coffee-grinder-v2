# /scripts/debug_with_raw_response.py

import sys
import os

# Добавляем корневую папку в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.news.fetcher_fabric import create_news_fetcher_from_config
from dotenv import load_dotenv

def main():
    # Загружаем переменные окружения
    load_dotenv()
    
    # Создаем fetcher для MediaStack
    fetcher = create_news_fetcher_from_config("mediastack")
    
    print("🔍 Тестирование с включенным raw response логированием")
    print("=" * 60)
    
    # Временно включаем raw response логирование
    # Изменяем метод _make_request для логирования
    original_make_request = fetcher._make_request
    
    def debug_make_request(endpoint, params):
        print(f"🔧 Вызов API: {endpoint}")
        print(f"🔧 Параметры: {params}")
        
        # Вызываем оригинальный метод
        url = f"{fetcher.base_url}/{endpoint}"
        params["access_key"] = fetcher.access_key
        
        result = fetcher._make_request_with_retries(
            session=fetcher.session,
            url=url,
            params=params,
            timeout=30
        )
        
        if "error" in result:
            print(f"❌ Ошибка HTTP: {result['error']}")
            return result
        
        response = result["response"]
        print(f"✅ HTTP Status: {response.status_code}")
        print(f"📊 Raw Response: {response.text}")
        
        try:
            data = response.json()
            
            if "error" in data:
                error_info = data["error"]
                error_msg = error_info.get("message", "Unknown API error")
                error_code = error_info.get("code", "unknown_error")
                print(f"❌ API Error [{error_code}]: {error_msg}")
                
                from src.services.news.fetchers.base import NewsAPIError
                return {"error": NewsAPIError(f"[{error_code}] {error_msg}", response.status_code, 1)}
            
            print(f"✅ Данных получено: {len(data.get('data', []))}")
            return data
            
        except Exception as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            from src.services.news.fetchers.base import NewsAPIError
            return {"error": NewsAPIError(f"Failed to parse JSON: {str(e)}", response.status_code, 1)}
    
    # Подменяем метод
    fetcher._make_request = debug_make_request
    
    # Тестируем запрос
    print("📋 Запрос новостей от washington-post")
    response = fetcher.fetch_news(domains="washingtonpost.com", limit=5)
    
    print("\n📋 Результат:")
    if "error" in response:
        print(f"   ❌ Ошибка: {response['error']}")
    else:
        articles = response.get("articles", [])
        print(f"   ✅ Получено статей: {len(articles)}")
        if articles:
            print(f"   📰 Первая статья: {articles[0].get('title', 'Без заголовка')}")

if __name__ == "__main__":
    main() 