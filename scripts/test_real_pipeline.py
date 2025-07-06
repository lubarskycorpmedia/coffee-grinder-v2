# scripts/test_real_pipeline.py
"""
Тестирование реального pipeline обработки новостей
Требует настроенный .env файл с API ключами
"""
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.news.pipeline import create_news_pipeline_orchestrator
from src.config import get_google_settings
from dotenv import load_dotenv


def test_real_pipeline():
    """Тестирование полного pipeline с реальными API вызовами"""
    print("🔥 Тестирование реального NewsPipelineOrchестrator")
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
    
    # Проверяем наличие .env файла
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_file):
        print("❌ Файл .env не найден!")
        print("💡 Создайте .env файл на основе .env.example")
        print("   Необходимые переменные:")
        print("   - THENEWSAPI_API_TOKEN")
        print("   - OPENAI_API_KEY")
        print("   - GOOGLE_SHEET_ID")
        print("   - GOOGLE_SERVICE_ACCOUNT_PATH")
        print("   - GOOGLE_ACCOUNT_EMAIL")
        print("   - GOOGLE_ACCOUNT_KEY")
        return False
    
    print(f"✅ Файл .env найден: {env_file}")
    print()
    
    # Создаем оркестратор
    try:
        orchestrator = create_news_pipeline_orchestrator(
            provider="thenewsapi",
            worksheet_name="TestPipeline"
        )
        print("✅ Оркестратор создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания оркестратора: {e}")
        return False
    
    # Параметры для тестирования
    test_params = {
        "query": "Putin | Zelensky",
        "categories": ["general", "politics"],
        "limit": 5,  # Небольшое количество для тестирования
    }
    
    print(f"📋 Параметры тестирования:")
    for key, value in test_params.items():
        print(f"   {key}: {value}")
    print()
    
    # Запускаем pipeline
    print("🚀 Запуск pipeline...")
    start_time = datetime.now()
    
    try:
        result = orchestrator.run_pipeline(**test_params)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️ Общее время выполнения: {execution_time:.2f}s")
        print()
        
        # Анализируем результат
        analyze_pipeline_result(result)
        
        return result.success
        
    except Exception as e:
        print(f"❌ Ошибка выполнения pipeline: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return False


def analyze_pipeline_result(result):
    """Анализирует и выводит результат pipeline"""
    print("📊 Анализ результата pipeline:")
    print(f"   Общий успех: {'✅ ДА' if result.success else '❌ НЕТ'}")
    print(f"   Этапы: {result.completed_stages}/{result.total_stages}")
    print(f"   Время выполнения: {result.total_execution_time:.2f}s")
    print()
    
    if result.errors:
        print("⚠️ Ошибки:")
        for error in result.errors:
            print(f"   - {error}")
        print()
    
    # Анализ каждого этапа
    print("🔍 Детали этапов:")
    
    # Этап 1: Fetcher
    fetcher_result = result.results.get("fetcher")
    if fetcher_result:
        print(f"   1️⃣ Fetcher: {'✅' if fetcher_result.success else '❌'}")
        print(f"      Время: {fetcher_result.execution_time:.2f}s")
        if fetcher_result.success and fetcher_result.data:
            print(f"      Получено статей: {fetcher_result.data.get('articles_count', 0)}")
        if fetcher_result.error_message:
            print(f"      Ошибка: {fetcher_result.error_message}")
        print()
    
    # Этап 2: Deduplication
    dedup_result = result.results.get("deduplication")
    if dedup_result:
        print(f"   2️⃣ Дедупликация: {'✅' if dedup_result.success else '❌'}")
        print(f"      Время: {dedup_result.execution_time:.2f}s")
        if dedup_result.success and dedup_result.data:
            data = dedup_result.data
            print(f"      Исходно статей: {data.get('original_count', 0)}")
            print(f"      После дедупликации: {data.get('deduplicated_count', 0)}")
            print(f"      Найдено дублей: {data.get('duplicates_count', 0)}")
        if dedup_result.error_message:
            print(f"      Ошибка: {dedup_result.error_message}")
        print()
    
    # Этап 3: Export
    export_result = result.results.get("export")
    if export_result:
        print(f"   3️⃣ Экспорт: {'✅' if export_result.success else '❌'}")
        print(f"      Время: {export_result.execution_time:.2f}s")
        if export_result.success and export_result.data:
            data = export_result.data
            print(f"      Экспортировано статей: {data.get('exported_count', 0)}")
            if 'sheet_url' in data:
                print(f"      URL таблицы: {data['sheet_url']}")
        if export_result.error_message:
            print(f"      Ошибка: {export_result.error_message}")
        print()


def test_components_individually():
    """Тестирование компонентов по отдельности"""
    print("🔧 Тестирование компонентов по отдельности")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Для локального тестирования используем локальный путь
    local_service_account_path = ".config/google_service_account.json"
    if os.path.exists(local_service_account_path):
        os.environ['GOOGLE_SERVICE_ACCOUNT_PATH'] = local_service_account_path
        # Очищаем кэш настроек, чтобы подхватить новую переменную
        get_google_settings.cache_clear()
    
    try:
        orchestrator = create_news_pipeline_orchestrator()
        
        # Тест 1: Fetcher
        print("1️⃣ Тестирование Fetcher...")
        try:
            fetcher = orchestrator.fetcher
            print(f"   ✅ Fetcher создан: {type(fetcher).__name__}")
            
            # Пробуем получить новости
            response = fetcher.fetch_news(
                query="test",
                categories="tech",
                limit=2,
                language="en"
            )
            
            if response.get("status") == "success":
                articles_count = len(response.get("articles", []))
                print(f"   ✅ Получено статей: {articles_count}")
            else:
                print(f"   ⚠️ Ответ fetcher: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Ошибка Fetcher: {e}")
        
        print()
        
        # Тест 2: News Chain
        print("2️⃣ Тестирование News Chain...")
        try:
            news_chain = orchestrator.news_chain
            print(f"   ✅ News Chain создан: {type(news_chain).__name__}")
            print(f"   📊 Similarity threshold: {news_chain.similarity_threshold}")
            print(f"   📊 Max items: {news_chain.max_news_items}")
        except Exception as e:
            print(f"   ❌ Ошибка News Chain: {e}")
        
        print()
        
        # Тест 3: Exporter
        print("3️⃣ Тестирование Exporter...")
        try:
            exporter = orchestrator.exporter
            print(f"   ✅ Exporter создан: {type(exporter).__name__}")
            print(f"   📊 Spreadsheet ID: {exporter.spreadsheet_id}")
            print(f"   📊 Worksheet: {exporter.worksheet_name}")
        except Exception as e:
            print(f"   ❌ Ошибка Exporter: {e}")
            print("   💡 Проверьте настройки Google Sheets в .env")
        
        print()
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании компонентов: {e}")


def save_result_to_file(result, filename="pipeline_test_result.json"):
    """Сохраняет результат в файл для анализа"""
    try:
        # Преобразуем результат в JSON-сериализуемый формат
        result_dict = {
            "success": result.success,
            "total_stages": result.total_stages,
            "completed_stages": result.completed_stages,
            "total_execution_time": result.total_execution_time,
            "errors": result.errors,
            "results": {}
        }
        
        for stage_name, stage_result in result.results.items():
            result_dict["results"][stage_name] = {
                "success": stage_result.success,
                "execution_time": stage_result.execution_time,
                "error_message": stage_result.error_message,
                "data": stage_result.data
            }
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Результат сохранен в файл: {filepath}")
        
    except Exception as e:
        print(f"⚠️ Не удалось сохранить результат: {e}")


if __name__ == "__main__":
    print("🧪 Тестирование реального pipeline обработки новостей")
    print("=" * 60)
    
    # Тестируем компоненты по отдельности
    test_components_individually()
    
    print("\n" + "="*60 + "\n")
    
    # Тестируем полный pipeline
    success = test_real_pipeline()
    
    if success:
        print("\n🎉 Тест pipeline завершен успешно!")
    else:
        print("\n💥 Тест pipeline завершился с ошибками")
        print("💡 Проверьте:")
        print("   1. Настройки .env файла")
        print("   2. Доступность API (TheNewsAPI, OpenAI)")
        print("   3. Настройки Google Sheets")
        print("   4. Интернет соединение") 