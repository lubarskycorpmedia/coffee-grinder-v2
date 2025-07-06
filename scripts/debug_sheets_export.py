# /scripts/debug_sheets_export.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone
from src.services.news.exporter import GoogleSheetsExporter
from src.langchain.news_chain import NewsItem

def debug_sheets_export():
    """Отладка экспорта в Google Sheets"""
    
    print("🔍 Отладка экспорта в Google Sheets")
    print("=" * 50)
    
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
    print(f"✅ Загружены переменные окружения из {env_path}")
    
    # Создаем тестовые данные
    test_items = []
    for i in range(3):
        item = NewsItem(
            title=f"Test Article {i+1}",
            description=f"Description for test article {i+1}",
            url=f"https://example.com/article{i+1}",
            published_at=datetime.now(timezone.utc),
            source="test-source",
            category="test",
            language="en",
            image_url=f"https://example.com/image{i+1}.jpg",
            uuid=f"test-uuid-{i+1}",
            keywords=f"keyword{i+1}",
            snippet=f"Snippet for article {i+1}"
        )
        # Устанавливаем дополнительные поля
        item.relevance_score = 5.0
        item.similarity_score = 0.0
        item.is_duplicate = False
        item.duplicate_of = None
        test_items.append(item)
    
    print(f"📊 Создано {len(test_items)} тестовых статей")
    
    # Создаем экспортер
    try:
        exporter = GoogleSheetsExporter(worksheet_name="DebugTest")
        print("✅ Экспортер создан успешно")
        
        # Получаем worksheet для проверки
        worksheet = exporter._get_worksheet()
        print(f"📋 Worksheet: {worksheet.title}")
        print(f"📊 Строк до экспорта: {worksheet.row_count}")
        
        # Подготавливаем данные
        rows_data = exporter._prepare_export_data(test_items)
        print(f"📊 Подготовлено строк данных: {len(rows_data)}")
        
        # Показываем первую строку данных
        if rows_data:
            print(f"🔍 Первая строка: {rows_data[0][:5]}...")  # Показываем первые 5 полей
        
        # Экспортируем
        print("\n🚀 Запуск экспорта...")
        success = exporter.export_news(test_items, append=True)
        
        if success:
            print("✅ Экспорт завершен успешно")
            
            # Проверяем результат
            worksheet = exporter._get_worksheet()  # Обновляем worksheet
            print(f"📊 Строк после экспорта: {worksheet.row_count}")
            
            # Читаем последние строки
            try:
                all_values = worksheet.get_all_values()
                print(f"📊 Всего значений в таблице: {len(all_values)}")
                
                # Показываем последние 5 строк
                if len(all_values) > 1:
                    print("\n📋 Последние строки в таблице:")
                    for i, row in enumerate(all_values[-5:], 1):
                        print(f"  {i}: {row[1][:50]}...")  # Показываем title (2-я колонка)
                
            except Exception as e:
                print(f"❌ Ошибка при чтении данных: {e}")
        else:
            print("❌ Экспорт не удался")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sheets_export() 