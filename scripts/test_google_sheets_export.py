#!/usr/bin/env python3
# /scripts/test_google_sheets_export.py
"""
Тестовый скрипт для проверки экспорта в Google Sheets
"""

import sys
import os
from datetime import datetime, timezone
from typing import List

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.news.exporter import GoogleSheetsExporter
from src.langchain.news_chain import NewsItem
from src.logger import setup_logger
from src.config import get_google_settings
from dotenv import load_dotenv


def create_test_news_items() -> List[NewsItem]:
    """Создает тестовые новости для экспорта"""
    # Создаем базовые новости
    item1 = NewsItem(
        title="Test News Article 1",
        description="This is a test news article for Google Sheets export testing",
        url="https://example.com/news/1",
        published_at=datetime.now(timezone.utc),
        source="Test Source",
        category="technology",
        language="en"
    )
    item1.relevance_score = 8.5
    item1.similarity_score = 0.0
    item1.is_duplicate = False
    item1.duplicate_of = None
    
    item2 = NewsItem(
        title="Test News Article 2",
        description="Another test news article to verify batch export functionality",
        url="https://example.com/news/2",
        published_at=datetime.now(timezone.utc),
        source="Test Source 2",
        category="business",
        language="en"
    )
    item2.relevance_score = 9.2
    item2.similarity_score = 0.0
    item2.is_duplicate = False
    item2.duplicate_of = None
    
    item3 = NewsItem(
        title="Duplicate Test Article",
        description="This is a duplicate test article",
        url="https://example.com/news/3",
        published_at=datetime.now(timezone.utc),
        source="Test Source",
        category="technology",
        language="en"
    )
    item3.relevance_score = 7.5
    item3.similarity_score = 0.95
    item3.is_duplicate = True
    item3.duplicate_of = "Test News Article 1"
    
    return [item1, item2, item3]


def test_google_sheets_export():
    """Тестирует экспорт в Google Sheets"""
    logger = setup_logger(__name__)
    
    print("=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ ЭКСПОРТА В GOOGLE SHEETS")
    print("=" * 60)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Для локального тестирования используем локальный путь
    local_service_account_path = ".config/google_service_account.json"
    if os.path.exists(local_service_account_path):
        os.environ['GOOGLE_SERVICE_ACCOUNT_PATH'] = local_service_account_path
        print(f"🔧 Используем локальный service account: {local_service_account_path}")
    
        # Очищаем кэш настроек, чтобы подхватить новую переменную
        get_google_settings.cache_clear()
    
    # Проверяем наличие необходимых переменных
    required_vars = [
        'GOOGLE_SHEET_ID',
        'GOOGLE_SERVICE_ACCOUNT_PATH'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        return False
    
    print("✅ Все необходимые переменные окружения найдены")
    
    try:
        # Создаем экспортер
        print("\n📊 Создание экспортера Google Sheets...")
        
        # Получаем ID таблицы из переменных окружения
        spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
        
        # Создаём временный экспортер с прямым указанием настроек
        from src.config import GoogleSettings
        
        # Создаём настройки с локальным путём
        google_settings = GoogleSettings(
            GOOGLE_SHEET_ID=spreadsheet_id,
            GOOGLE_SERVICE_ACCOUNT_PATH=os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH'),
            GOOGLE_ACCOUNT_EMAIL=os.getenv('GOOGLE_ACCOUNT_EMAIL', ''),
            GOOGLE_ACCOUNT_KEY=os.getenv('GOOGLE_ACCOUNT_KEY', '')
        )
        
        # Создаём экспортер без инициализации клиента
        exporter = GoogleSheetsExporter.__new__(GoogleSheetsExporter)
        exporter.worksheet_name = "Лист1"  # Используем существующий лист
        exporter.max_retries = 3
        exporter.retry_delay = 1.0
        exporter._logger = None
        exporter._client = None
        exporter._spreadsheet = None
        exporter._worksheet = None
        exporter.settings = google_settings
        exporter.spreadsheet_id = spreadsheet_id
        
        # Теперь инициализируем клиент с правильными настройками
        exporter._setup_client()
        
        # Создаем тестовые данные
        print("📝 Создание тестовых новостей...")
        test_news = create_test_news_items()
        print(f"   Создано {len(test_news)} тестовых новостей")
        
        # Экспортируем данные
        print("\n🚀 Экспорт данных в Google Sheets...")
        success = exporter.export_news(test_news, append=True)
        
        if success:
            print("✅ Экспорт выполнен успешно!")
            
            # Получаем сводку
            summary = exporter.get_export_summary()
            print(f"📈 Сводка экспорта:")
            print(f"   📊 Всего записей: {summary['data_rows']}")
            print(f"   📋 Лист: {summary['worksheet_name']}")
            print(f"   🔗 ID таблицы: {summary['spreadsheet_id']}")
            print(f"   ⏰ Последний экспорт: {summary['last_updated']}")
        
            # Тестируем повторный экспорт (append)
            print("\n🔄 Тестирование повторного экспорта (append)...")
            additional_item_obj = NewsItem(
                title="Additional Test Article",
                description="This article tests append functionality",
                url="https://example.com/news/4",
                published_at=datetime.now(timezone.utc),
                source="Append Test Source",
                category="test",
                language="en"
            )
            additional_item_obj.relevance_score = 8.8
            additional_item_obj.similarity_score = 0.0
            additional_item_obj.is_duplicate = False
            additional_item_obj.duplicate_of = None
            
            additional_item = [additional_item_obj]
            
            append_success = exporter.export_news(additional_item, append=True)
            if append_success:
                print("✅ Повторный экспорт (append) выполнен успешно!")
            else:
                print("❌ Ошибка при повторном экспорте")
                
        else:
            print("❌ Ошибка при экспорте данных")
            return False
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {str(e)}")
        print(f"❌ Критическая ошибка: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
    print("💡 Проверьте Google Sheets таблицу для подтверждения данных")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_google_sheets_export()
    sys.exit(0 if success else 1) 