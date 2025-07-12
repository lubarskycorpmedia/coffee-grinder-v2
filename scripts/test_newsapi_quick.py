# /scripts/test_newsapi_quick.py

import sys
import os
from dotenv import load_dotenv

# Добавляем корневую папку в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """Быстрое тестирование NewsAPI провайдера"""
    load_dotenv()
    
    print("🔍 Быстрое тестирование NewsAPI провайдера")
    print("=" * 50)
    
    try:
        # Создаем fetcher для NewsAPI
        from src.services.news.fetcher_fabric import create_news_fetcher_from_config
        fetcher = create_news_fetcher_from_config("newsapi")
        
        print("✅ Fetcher создан успешно")
        
        # Тестируем health check
        print("\n🏥 Проверка health check...")
        health = fetcher.check_health()
        print(f"Health status: {health}")
        
        # Тестируем получение категорий
        print("\n📂 Получение категорий...")
        categories = fetcher.get_categories()
        print(f"Доступные категории: {categories}")
        
        # Тестируем получение языков
        print("\n🌐 Получение языков...")
        languages = fetcher.get_languages()
        print(f"Доступные языки: {languages}")
        
        # Тестируем получение источников
        print("\n📰 Получение источников...")
        sources = fetcher.get_sources()
        sources_list = sources.get('sources', [])
        print(f"Найдено источников: {len(sources_list)}")
        if sources_list:
            print("Первые 5 источников:")
            for source in sources_list[:5]:
                print(f"  - {source['name']} ({source['id']})")
        
        # Тестируем получение топ новостей
        print("\n🔥 Получение топ новостей...")
        top_news = fetcher.fetch_news(rubric="general")
        print(f"Найдено новостей: {len(top_news)}")
        if top_news:
            print("Первые 2 новости:")
            for article in top_news[:2]:
                print(f"  - {article['title'][:100]}...")
        
        # Тестируем поиск новостей
        print("\n🔍 Поиск новостей по запросу 'technology'...")
        search_results = fetcher.search_news("technology", limit=5)
        print(f"Найдено новостей: {len(search_results)}")
        if search_results:
            print("Первые 2 результата:")
            for article in search_results[:2]:
                print(f"  - {article['title'][:100]}...")
        
        print("\n✅ Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 