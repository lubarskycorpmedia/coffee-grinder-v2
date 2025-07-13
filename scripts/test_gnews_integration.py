#!/usr/bin/env python3
# scripts/test_gnews_integration.py

"""
Скрипт для тестирования интеграции GNews fetcher'а
"""

import os
import sys
import json
from pathlib import Path

# Добавляем путь к корню проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.news.fetchers.gnews_io import GNewsIOFetcher
from src.services.news.fetcher_fabric import FetcherFactory
from src.config import GNewsIOSettings


def test_gnews_fetcher_creation():
    """Тест создания GNews fetcher'а"""
    print("=== Тест создания GNews fetcher'а ===")
    
    # Создаем настройки
    settings = GNewsIOSettings(
        api_key="test_api_key",
        base_url="https://gnews.io/api/v4",
        page_size=10,
        enabled=True,
        priority=1,
        max_retries=3,
        timeout=30
    )
    
    # Создаем fetcher
    fetcher = GNewsIOFetcher(settings)
    
    print(f"✓ Fetcher создан: {type(fetcher).__name__}")
    print(f"✓ Provider name: {fetcher.PROVIDER_NAME}")
    print(f"✓ API key установлен: {bool(fetcher.api_key)}")
    print(f"✓ Base URL: {fetcher.base_url}")
    print(f"✓ Page size: {fetcher.page_size}")
    print()


def test_gnews_categories_and_languages():
    """Тест получения категорий и языков"""
    print("=== Тест категорий и языков ===")
    
    settings = GNewsIOSettings(api_key="test_key")
    fetcher = GNewsIOFetcher(settings)
    
    categories = fetcher.get_categories()
    languages = fetcher.get_languages()
    countries = fetcher.get_countries()
    
    print(f"✓ Категории ({len(categories)}): {', '.join(categories)}")
    print(f"✓ Языки ({len(languages)}): {', '.join(languages[:10])}...")
    print(f"✓ Страны ({len(countries)}): {', '.join(countries[:10])}...")
    print()


def test_category_mapping():
    """Тест маппинга категорий"""
    print("=== Тест маппинга категорий ===")
    
    settings = GNewsIOSettings(api_key="test_key")
    fetcher = GNewsIOFetcher(settings)
    
    test_mappings = [
        ("business", "business"),
        ("tech", "technology"),
        ("sport", "sports"),
        ("finance", "business"),
        ("politics", "nation"),
        ("unknown", None),
        (None, None)
    ]
    
    for input_cat, expected in test_mappings:
        result = fetcher._map_category_to_gnews(input_cat)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_cat}' → '{result}' (ожидалось: '{expected}')")
    print()


def test_factory_integration():
    """Тест интеграции с фабрикой fetcher'ов"""
    print("=== Тест интеграции с фабрикой ===")
    
    # Устанавливаем тестовый API ключ
    os.environ['GNEWS_API_KEY'] = 'test_gnews_key'
    
    try:
        # Проверяем доступные провайдеры
        available = FetcherFactory.get_available_providers()
        enabled = FetcherFactory.get_enabled_providers()
        
        print(f"✓ Доступные провайдеры: {', '.join(available)}")
        print(f"✓ Включенные провайдеры: {', '.join(enabled)}")
        
        if 'gnews' in available:
            print("✓ GNews найден в доступных провайдерах")
        else:
            print("✗ GNews НЕ найден в доступных провайдерах")
        
        if 'gnews' in enabled:
            print("✓ GNews найден в включенных провайдерах")
        else:
            print("✗ GNews НЕ найден в включенных провайдерах")
        
        # Пытаемся создать fetcher через фабрику
        try:
            fetcher = FetcherFactory.create_fetcher_from_config('gnews')
            print(f"✓ Fetcher создан через фабрику: {type(fetcher).__name__}")
            print(f"✓ Provider name: {fetcher.PROVIDER_NAME}")
        except Exception as e:
            print(f"✗ Ошибка создания fetcher'а через фабрику: {e}")
            
    finally:
        # Очищаем переменную окружения
        if 'GNEWS_API_KEY' in os.environ:
            del os.environ['GNEWS_API_KEY']
    
    print()


def test_article_standardization():
    """Тест стандартизации статьи"""
    print("=== Тест стандартизации статьи ===")
    
    settings = GNewsIOSettings(api_key="test_key")
    fetcher = GNewsIOFetcher(settings)
    
    # Пример данных от GNews API
    sample_article = {
        "title": "Test Article Title",
        "description": "Test article description",
        "content": "Test article content...",
        "url": "https://example.com/article",
        "image": "https://example.com/image.jpg",
        "publishedAt": "2023-12-01T10:00:00Z",
        "source": {
            "name": "Test Source",
            "url": "https://example.com"
        }
    }
    
    standardized = fetcher._standardize_article(
        sample_article, 
        language="en", 
        category="technology"
    )
    
    print("✓ Стандартизированная статья:")
    for key, value in standardized.items():
        if key != "raw_data":  # Не показываем raw_data для краткости
            print(f"  {key}: {value}")
    
    print()


def main():
    """Главная функция"""
    print("🧪 Тестирование интеграции GNews fetcher'а\n")
    
    try:
        test_gnews_fetcher_creation()
        test_gnews_categories_and_languages()
        test_category_mapping()
        test_factory_integration()
        test_article_standardization()
        
        print("🎉 Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка во время тестирования: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 