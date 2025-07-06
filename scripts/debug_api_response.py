"""
Отладка полного ответа API для проверки всех доступных полей
"""
import sys
import os
import json
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.news.fetchers.thenewsapi_com import TheNewsAPIFetcher
from src.config import get_settings
from dotenv import load_dotenv


def debug_full_api_response():
    """Отладка полного ответа API"""
    print("🔍 Отладка полного ответа TheNewsAPI")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем настройки
    settings = get_settings()
    
    if not settings.THENEWSAPI_API_TOKEN:
        print("❌ THENEWSAPI_API_TOKEN не найден в настройках")
        return
    
    # Создаем fetcher
    fetcher = TheNewsAPIFetcher(settings.THENEWSAPI_API_TOKEN)
    
    # Получаем новости с минимальными фильтрами
    print("📰 Получение новостей...")
    
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    response = fetcher.fetch_all_news(
        search="technology",
        language="en",
        categories="tech",
        published_after=week_ago,
        limit=2  # Только 2 статьи для детального анализа
    )
    
    if "error" in response:
        print(f"❌ Ошибка API: {response['error']}")
        return
    
    articles = response.get("data", [])
    print(f"✅ Получено {len(articles)} статей")
    
    if not articles:
        print("⚠️ Нет статей для анализа")
        return
    
    # Анализируем структуру первой статьи
    print("\\n🔍 Анализ структуры первой статьи:")
    print("=" * 40)
    
    first_article = articles[0]
    
    # Выводим все доступные поля
    print("📋 Все доступные поля:")
    for key, value in first_article.items():
        value_preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
        print(f"   {key}: {value_preview}")
    
    # Проверяем наличие полей с изображениями
    print("\\n🖼️ Поля с изображениями:")
    image_fields = [
        "image", "image_url", "urlToImage", "imageUrl", 
        "thumbnail", "thumbnail_url", "media", "images"
    ]
    
    found_image_fields = []
    for field in image_fields:
        if field in first_article:
            found_image_fields.append(field)
            print(f"   ✅ {field}: {first_article[field]}")
    
    if not found_image_fields:
        print("   ❌ Поля с изображениями не найдены")
        print("   🔍 Возможные поля:")
        for key in first_article.keys():
            if any(img_word in key.lower() for img_word in ['image', 'photo', 'picture', 'media']):
                print(f"      - {key}: {first_article[key]}")
    
    # Сохраняем полный ответ в файл для детального анализа
    output_file = "debug_api_full_response.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(response, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\\n💾 Полный ответ сохранен в файл: {output_file}")
    print("\\n📊 Сводка:")
    print(f"   Всего статей: {len(articles)}")
    print(f"   Найдено полей с изображениями: {len(found_image_fields)}")
    if found_image_fields:
        print(f"   Поля: {', '.join(found_image_fields)}")


if __name__ == "__main__":
    debug_full_api_response() 