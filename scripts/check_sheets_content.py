# /scripts/check_sheets_content.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from src.services.news.exporter import GoogleSheetsExporter

def check_sheets_content():
    """Проверка содержимого Google Sheets"""
    
    print("🔍 Проверка содержимого Google Sheets")
    print("=" * 50)
    
    # Загружаем переменные окружения
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
    
    try:
        # Создаем экспортер для TestPipeline worksheet
        exporter = GoogleSheetsExporter(worksheet_name="TestPipeline")
        print("✅ Экспортер создан успешно")
        
        # Получаем worksheet
        worksheet = exporter._get_worksheet()
        print(f"📋 Worksheet: {worksheet.title}")
        print(f"📊 Общее количество строк: {worksheet.row_count}")
        print(f"📊 Общее количество колонок: {worksheet.col_count}")
        
        # Получаем все данные
        all_values = worksheet.get_all_values()
        print(f"📊 Строк с данными: {len(all_values)}")
        
        if all_values:
            print(f"📊 Заголовки: {all_values[0]}")
            print()
            
            # Показываем последние 10 строк
            print("📋 Последние 10 строк:")
            for i, row in enumerate(all_values[-10:], len(all_values) - 9):
                if len(row) > 1 and row[1]:  # Если есть title
                    print(f"  {i:3d}: {row[0][:19]} | {row[1][:60]}...")
                else:
                    print(f"  {i:3d}: [пустая строка]")
            
            print()
            
            # Подсчитываем непустые строки (исключая заголовки)
            non_empty_rows = 0
            for i, row in enumerate(all_values[1:], 2):  # Начинаем с 2-й строки
                if len(row) > 1 and row[1]:  # Если есть title
                    non_empty_rows += 1
            
            print(f"📊 Непустых строк данных: {non_empty_rows}")
            
            # Проверяем последние добавленные строки
            print("\n🔍 Анализ последних добавленных строк:")
            recent_rows = []
            for i, row in enumerate(all_values[1:], 2):
                if len(row) > 1 and row[1]:
                    recent_rows.append((i, row))
            
            # Показываем последние 5 записей
            for i, (row_num, row) in enumerate(recent_rows[-5:], 1):
                print(f"  {i}: Строка {row_num}: {row[1][:60]}...")
                print(f"      Timestamp: {row[0]}")
                print(f"      URL: {row[3][:50]}...")
                print()
        
        # Проверяем фильтры
        try:
            # Получаем информацию о фильтрах
            spreadsheet = exporter._spreadsheet
            sheet_metadata = spreadsheet.get_worksheet_by_id(worksheet.id)
            print(f"📊 Метаданные листа получены")
        except Exception as e:
            print(f"⚠️ Не удалось получить метаданные: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_sheets_content() 