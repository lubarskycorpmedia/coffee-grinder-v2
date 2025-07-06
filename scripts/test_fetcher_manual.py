#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы fetcher'а новостей
Использует реальные данные из .env файла
"""

import os
import sys
import json
from typing import Dict, Any

# Добавляем корневую директорию в PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.news.fetcher_fabric import create_news_fetcher
from src.logger import setup_logger

# ============================================================================
# НАСТРОЙКИ ТЕСТОВ - РЕДАКТИРУЙТЕ ПАРАМЕТРЫ ЗДЕСЬ
# ============================================================================

# ТЕСТ 1: Параметры для Headlines (/v1/news/headlines)
# Доступно только на Standard план и выше
HEADLINES_PARAMS = {
    "locale": "us",                    # Коды стран: us, ca, gb, de и т.д.
    "language": "en",                  # Коды языков: en, es, fr, de и т.д.
    "headlines_per_category": 3,       # Количество заголовков (макс. 10)
    "include_similar": True,           # Включать похожие статьи
    # "domains": "cnn.com,bbc.com",    # Домены для включения (раскомментируйте если нужно)
    # "exclude_domains": "",           # Домены для исключения
    # "source_ids": "",                # ID источников для включения
    # "exclude_source_ids": "",        # ID источников для исключения
    # "published_on": "2025-01-15",    # Конкретная дата (YYYY-MM-DD)
}

# ТЕСТ 2: Параметры для All News (/v1/news/all)
# Доступно на всех планах
ALL_NEWS_PARAMS = {
    "search": "Trump",         # Поисковый запрос (поддерживает +, -, |, скобки)
    "language": "ru",                  # Коды языков
    "limit": 3,                        # Количество результатов (макс. 100)
    "sort": "relevance_score",         # Сортировка: published_at, relevance_score
    "sort_order": "desc",              # Порядок: asc, desc
    # "locale": "us",                  # Коды стран (раскомментируйте если нужно)
    # "domains": "",                   # Домены для включения
    # "exclude_domains": "",           # Домены для исключения
    # "source_ids": "",                # ID источников для включения
    # "exclude_source_ids": "",        # ID источников для исключения
    "categories": "general,politics,tech,business",   # Категории для включения
    # "exclude_categories": "sports",  # Категории для исключения
    # "published_after": "2025-01-01", # Дата начала (YYYY-MM-DD)
    # "published_before": "2025-01-15", # Дата окончания (YYYY-MM-DD)
    "published_on": "2025-07-06",    # Конкретная дата (YYYY-MM-DD)
    # "page": 1,                       # Номер страницы
}

# ТЕСТ 3: Параметры для Sources (/v1/news/sources)
# Доступно на всех планах
SOURCES_PARAMS = {
    "language": "en",                  # Коды языков
    "locale": "us",                    # Коды стран
    # "categories": "business,tech",   # Категории для фильтрации (раскомментируйте если нужно)
}

# ============================================================================
# ВАЛИДАЦИЯ ПАРАМЕТРОВ
# ============================================================================

def validate_params():
    """Проверяет корректность заданных параметров"""
    errors = []
    
    # Проверяем Headlines параметры
    if "headlines_per_category" in HEADLINES_PARAMS:
        hpc = HEADLINES_PARAMS["headlines_per_category"]
        if not isinstance(hpc, int) or hpc < 1 or hpc > 10:
            errors.append("headlines_per_category должно быть числом от 1 до 10")
    
    # Проверяем All News параметры
    if "limit" in ALL_NEWS_PARAMS:
        limit = ALL_NEWS_PARAMS["limit"]
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            errors.append("limit должно быть числом от 1 до 100")
    
    if "sort" in ALL_NEWS_PARAMS:
        valid_sorts = ["published_at", "relevance_score"]
        if ALL_NEWS_PARAMS["sort"] not in valid_sorts:
            errors.append(f"sort должно быть одним из: {valid_sorts}")
    
    if "sort_order" in ALL_NEWS_PARAMS:
        valid_orders = ["asc", "desc"]
        if ALL_NEWS_PARAMS["sort_order"] not in valid_orders:
            errors.append(f"sort_order должно быть одним из: {valid_orders}")
    
    # Проверяем даты (базовая проверка формата YYYY-MM-DD)
    import re
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    
    for params_dict in [HEADLINES_PARAMS, ALL_NEWS_PARAMS, SOURCES_PARAMS]:
        for key in ["published_on", "published_after", "published_before"]:
            if key in params_dict and params_dict[key]:
                if not re.match(date_pattern, params_dict[key]):
                    errors.append(f"{key} должно быть в формате YYYY-MM-DD")
    
    return errors

# ============================================================================


def test_fetcher_with_real_api():
    """Тестирует fetcher с реальным API"""
    # Устанавливаем заглушки для обязательных полей (чтобы не мешали тестированию fetcher'а)
    os.environ.setdefault('GOOGLE_GSHEET_ID', 'test-sheet-id')
    os.environ.setdefault('GOOGLE_ACCOUNT_EMAIL', 'test@example.com')  
    os.environ.setdefault('GOOGLE_ACCOUNT_KEY', 'test-key')
    os.environ.setdefault('OPENAI_API_KEY', 'sk-test-key')
    
    logger = setup_logger("test_fetcher")
    
    # Проверяем наличие API ключа
    api_token = os.getenv('THENEWSAPI_API_TOKEN')
    if not api_token:
        logger.error("❌ Отсутствует THENEWSAPI_API_TOKEN в переменных окружения")
        logger.info("💡 Создайте .env файл с THENEWSAPI_API_TOKEN=your_token_here")
        return False
    
    # Валидируем параметры
    validation_errors = validate_params()
    if validation_errors:
        logger.error("❌ Ошибки в параметрах тестов:")
        for error in validation_errors:
            logger.error(f"   - {error}")
        logger.info("💡 Исправьте параметры в начале скрипта и перезапустите")
        return False
    
    logger.info("🚀 Тестирование fetcher'а с реальным API...")
    logger.info("✅ Параметры тестов валидны")
    
    try:
        # Создаем fetcher
        fetcher = create_news_fetcher("thenewsapi")
        logger.info("✅ Fetcher создан успешно")
        
        # Тестируем получение заголовков (может не работать на бесплатном плане)
        logger.info("📰 ТЕСТ 1: Получение заголовков")
        logger.info("─" * 50)
        
        # Фильтруем только заданные параметры (убираем None и пустые строки)
        filtered_headlines_params = {k: v for k, v in HEADLINES_PARAMS.items() 
                                   if v is not None and v != ""}
        
        logger.info("📋 Параметры запроса:")
        for key, value in filtered_headlines_params.items():
            logger.info(f"  - {key}: {value}")
        
        headlines = fetcher.fetch_headlines(**filtered_headlines_params)
        
        if "error" in headlines:
            logger.warning(f"⚠️ Заголовки недоступны на вашем плане: {headlines['error']}")
            logger.info("💡 Это нормально для бесплатного плана TheNewsAPI")
        else:
            logger.info(f"✅ Получено {len(headlines.get('data', {}).get('general', []))} заголовков")
            
            # Показываем первые несколько новостей
            general_news = headlines.get('data', {}).get('general', [])
            for i, news in enumerate(general_news[:2], 1):
                logger.info(f"📄 Новость {i}: {news.get('title', 'Без заголовка')}")
                logger.info(f"   Источник: {news.get('source', 'Неизвестно')}")
                logger.info(f"   URL: {news.get('url', 'Нет URL')}")
                if news.get('description'):
                    logger.info(f"   Описание: {news.get('description')}")
                logger.info("")
        
        logger.info("")
        
        # Тестируем поиск новостей (обычно работает на бесплатном плане)
        logger.info("🔍 ТЕСТ 2: Поиск новостей")
        logger.info("─" * 50)
        
        # Фильтруем только заданные параметры (убираем None и пустые строки)
        filtered_search_params = {k: v for k, v in ALL_NEWS_PARAMS.items() 
                                if v is not None and v != ""}
        
        logger.info("📋 Параметры запроса:")
        for key, value in filtered_search_params.items():
            logger.info(f"  - {key}: {value}")
        
        search_results = fetcher.fetch_all_news(**filtered_search_params)
        
        success_count = 0
        
        if "error" in search_results:
            logger.warning(f"⚠️ Поиск недоступен: {search_results['error']}")
        else:
            found_news = search_results.get('data', [])
            logger.info(f"✅ Найдено {len(found_news)} новостей по запросу")
            success_count += 1
            
            for i, news in enumerate(found_news[:2], 1):
                logger.info(f"🔍 Найденная новость {i}: {news.get('title', 'Без заголовка')}")
                logger.info(f"   Источник: {news.get('source', 'Неизвестно')}")
                logger.info(f"   URL: {news.get('url', 'Нет URL')}")
                
                # Показываем ВСЕ поля из API
                logger.info("   📄 Все поля из API:")
                for key, value in news.items():
                    if key not in ['title', 'source', 'url']:  # Уже показали выше
                        logger.info(f"     {key}: {value}")
                logger.info("")
        
        logger.info("")
        
        # Тестируем получение источников
        logger.info("📡 ТЕСТ 3: Получение списка источников")
        logger.info("─" * 50)
        
        # Фильтруем только заданные параметры (убираем None и пустые строки)
        filtered_sources_params = {k: v for k, v in SOURCES_PARAMS.items() 
                                 if v is not None and v != ""}
        
        logger.info("📋 Параметры запроса:")
        for key, value in filtered_sources_params.items():
            logger.info(f"  - {key}: {value}")
        
        sources = fetcher.get_sources(**filtered_sources_params)
        
        if "error" in sources:
            logger.warning(f"⚠️ Источники недоступны: {sources['error']}")
        else:
            sources_list = sources.get('data', [])
            logger.info(f"✅ Получено {len(sources_list)} источников")
            success_count += 1
            
            for i, source in enumerate(sources_list[:3], 1):
                logger.info(f"📡 Источник {i}: {source.get('name', 'Без названия')}")
                logger.info(f"   URL: {source.get('url', 'Нет URL')}")
                if source.get('description'):
                    logger.info(f"   Описание: {source.get('description')}")
                logger.info(f"   Домен: {source.get('domain', 'Нет домена')}")
                logger.info(f"   Страна: {source.get('country', 'Неизвестно')}")
                logger.info(f"   Язык: {source.get('language', 'Неизвестно')}")
                logger.info("")
        
        logger.info("")
        
        # Оценка результатов
        if success_count > 0:
            logger.info("🎉 Тестирование завершено успешно!")
            logger.info(f"✅ Работает {success_count} из 3 эндпоинтов")
            return True
        else:
            logger.warning("⚠️ Все эндпоинты недоступны на вашем плане")
            logger.info("💡 Рассмотрите возможность обновления плана TheNewsAPI")
            return False
        
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка: {e}")
        return False



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
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value or value == 'your_token_here':
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        print("❌ Отсутствуют обязательные переменные:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ Все необходимые переменные окружения найдены")
    return True


def main():
    """Главная функция тестирования"""
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ СБОРЩИКА НОВОСТЕЙ")
    print("=" * 60)
    
    # Показываем текущие настройки
    print("\n📋 ТЕКУЩИЕ НАСТРОЙКИ ТЕСТОВ:")
    print(f"📰 Headlines: {len([k for k, v in HEADLINES_PARAMS.items() if v is not None and v != ''])} параметров")
    print(f"🔍 All News: {len([k for k, v in ALL_NEWS_PARAMS.items() if v is not None and v != ''])} параметров")
    print(f"📡 Sources: {len([k for k, v in SOURCES_PARAMS.items() if v is not None and v != ''])} параметров")
    print("💡 Для изменения параметров отредактируйте секцию 'НАСТРОЙКИ ТЕСТОВ' в начале скрипта")
    
    # Загружаем переменные окружения
    if not load_environment():
        print("\n❌ Не удалось загрузить необходимые переменные окружения")
        print("💡 Для локальной разработки создайте .env файл в корне проекта")
        print("💡 Для запуска в контейнере убедитесь, что переменные переданы через docker-compose")
        return
    
    # Тестируем с реальным API
    print("\n🔑 Тестируем с реальным API...")
    success = test_fetcher_with_real_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("🎉 Fetcher работает корректно с реальным API!")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
        print("💡 Проверьте API ключ и подключение к интернету")
    print("=" * 60)


if __name__ == "__main__":
    main() 