#!/usr/bin/env python3
"""
Скрипт для тестирования интеграции MediaStack API
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.news.fetchers.mediastack_com import MediaStackFetcher
from src.services.news.pipeline import create_news_pipeline_orchestrator
from src.config import MediaStackSettings


def test_mediastack_fetcher():
    """Тестирует MediaStack fetcher напрямую"""
    print("=== Тестирование MediaStack Fetcher ===")
    
    # Создаем настройки (без реального API ключа)
    settings = MediaStackSettings(
        access_key="test_key",
        enabled=True,
        priority=4
    )
    
    # Создаем fetcher
    fetcher = MediaStackFetcher(settings)
    
    print(f"Провайдер: {fetcher.PROVIDER_NAME}")
    print(f"Базовый URL: {fetcher.base_url}")
    print(f"Размер страницы: {fetcher.page_size}")
    print(f"Поддерживаемые категории: {fetcher.get_categories()}")
    print(f"Поддерживаемые языки: {fetcher.get_languages()}")
    print(f"Поддерживаемые страны: {len(fetcher.get_supported_countries())} стран")
    
    # Тестируем health check (будет ошибка из-за неверного ключа)
    health = fetcher.check_health()
    print(f"Health check: {health}")


def test_mediastack_pipeline():
    """Тестирует MediaStack через pipeline"""
    print("\n=== Тестирование MediaStack через Pipeline ===")
    
    # Создаем pipeline с MediaStack
    pipeline = create_news_pipeline_orchestrator(provider='mediastack')
    
    # Получаем статус
    status = pipeline.get_pipeline_status()
    print(f"Pipeline статус: {status}")
    
    # Проверяем fetcher
    fetcher = pipeline.fetcher
    print(f"Fetcher инициализирован: {fetcher.PROVIDER_NAME}")
    
    # Примеры параметров для разных эндпоинтов
    print("\n=== Примеры использования MediaStack API ===")
    
    print("1. Получение новостей:")
    print("   pipeline.run_pipeline(query='bitcoin', categories=['business'], limit=10)")
    
    print("\n2. Получение исторических новостей:")
    print("   fetcher.fetch_historical_news(date='2023-01-01', categories='technology')")
    
    print("\n3. Получение источников:")
    print("   fetcher.get_sources(search='cnn', countries='us', limit=5)")
    
    print("\n4. Поиск новостей:")
    print("   fetcher.search_news(query='AI technology', language='en', limit=20)")


def demonstrate_mediastack_features():
    """Демонстрирует возможности MediaStack API"""
    print("\n=== Возможности MediaStack API ===")
    
    print("📰 Основные эндпоинты:")
    print("  • /v1/news - Live новости (с задержкой 30 мин на Free плане)")
    print("  • /v1/news - Исторические новости (Standard+ планы)")
    print("  • /v1/sources - Список источников новостей")
    
    print("\n🔧 Параметры фильтрации:")
    print("  • keywords - Поиск по ключевым словам")
    print("  • categories - Фильтр по категориям")
    print("  • countries - Фильтр по странам")
    print("  • languages - Фильтр по языкам")
    print("  • sources - Включить/исключить источники")
    print("  • date - Дата или диапазон дат")
    print("  • sort - Сортировка (published_desc, published_asc, popularity)")
    print("  • limit - Количество результатов (max 100)")
    print("  • offset - Смещение для пагинации")
    
    print("\n📊 Поддерживаемые данные:")
    print("  • 7,500+ источников новостей")
    print("  • 50+ стран")
    print("  • 13 языков")
    print("  • Тысячи статей ежедневно")
    
    print("\n💡 Особенности:")
    print("  • Включение/исключение через префикс '-' (например: 'cnn,-bbc')")
    print("  • Поддержка диапазонов дат: '2023-01-01,2023-01-31'")
    print("  • Автоматическая стандартизация формата ответов")
    print("  • Retry логика для обработки ошибок")
    print("  • Сохранение оригинальных данных в поле 'raw_data'")


if __name__ == "__main__":
    try:
        test_mediastack_fetcher()
        test_mediastack_pipeline()
        demonstrate_mediastack_features()
        
        print("\n✅ Интеграция MediaStack успешно завершена!")
        print("\n📝 Для использования:")
        print("1. Получите API ключ на https://mediastack.com/")
        print("2. Установите переменную окружения MEDIASTACK_API_KEY")
        print("3. Используйте provider='mediastack' в pipeline")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc() 