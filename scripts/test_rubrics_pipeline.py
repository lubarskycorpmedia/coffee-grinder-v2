#!/usr/bin/env python3
# /scripts/test_rubrics_pipeline.py

"""
Тестовый скрипт для проверки нового функционала run_all_rubrics с реальными данными
Требует настроенный .env файл с API ключами
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Добавляем корень проекта в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.news.rubrics_config import get_rubrics_config, get_active_rubrics
from src.services.news.pipeline import create_news_pipeline_orchestrator
from src.config import get_google_settings
from dotenv import load_dotenv


def test_rubrics_config():
    """Тестирует конфигурацию рубрик"""
    print("=== Тестирование конфигурации рубрик ===")
    
    # Получаем все рубрики
    all_rubrics = get_rubrics_config()
    print(f"Всего рубрик: {len(all_rubrics)}")
    
    # Получаем активные рубрики
    active_rubrics = get_active_rubrics()
    print(f"Активных рубрик: {len(active_rubrics)}")
    
    print("\nВсе рубрики:")
    for i, rubric in enumerate(all_rubrics, 1):
        status = "✅ АКТИВНА" if rubric in active_rubrics else "❌ неактивна"
        print(f"{i:2d}. {rubric['rubric']:20} | {rubric['category']:15} | {rubric['query']:30} | {status}")
    
    print("\nТолько активные рубрики:")
    for i, rubric in enumerate(active_rubrics, 1):
        print(f"{i:2d}. {rubric['rubric']:20} | {rubric['category']:15} | {rubric['query']:30}")
    
    return active_rubrics


def setup_environment():
    """Настройка окружения для реального тестирования"""
    print("\n=== Настройка окружения ===")
    
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
    return True


def test_pipeline_orchestrator():
    """Тестирует создание оркестратора pipeline"""
    print("\n=== Тестирование создания оркестратора ===")
    
    try:
        orchestrator = create_news_pipeline_orchestrator(
            provider="thenewsapi",
            worksheet_name="RubricsTest"
        )
        print("✅ Оркестратор создан успешно")
        
        # Проверяем статус
        status = orchestrator.get_pipeline_status()
        print(f"Провайдер: {status['provider']}")
        print(f"Лист: {status['worksheet_name']}")
        print(f"Компоненты инициализированы: {status['components']}")
        
        return orchestrator
    except Exception as e:
        print(f"❌ Ошибка создания оркестратора: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return None


def test_run_all_rubrics_real(orchestrator):
    """Тестирует метод run_all_rubrics с реальными API вызовами"""
    print("\n=== Тестирование метода run_all_rubrics (РЕАЛЬНЫЕ ДАННЫЕ) ===")
    
    if not orchestrator:
        print("❌ Оркестратор не создан, пропускаем тест")
        return None
    
    try:
        # Проверяем что метод существует
        if not hasattr(orchestrator, 'run_all_rubrics'):
            print("❌ Метод run_all_rubrics не найден")
            return None
        
        print("✅ Метод run_all_rubrics найден")
        
        # Получаем активные рубрики для проверки
        active_rubrics = get_active_rubrics()
        print(f"Будет обработано {len(active_rubrics)} активных рубрик")
        
        # Показываем что будет обработано
        print("\nРубрики для обработки:")
        for i, rubric in enumerate(active_rubrics, 1):
            print(f"{i:2d}. {rubric['rubric']} -> query: '{rubric['query']}', category: '{rubric['category']}'")
        
        # Параметры для реального тестирования
        test_limit = 3  # Небольшое количество для тестирования
        print(f"\n🚀 Запускаем реальный run_all_rubrics с limit={test_limit}...")
        print("⚠️  Это займет несколько минут, так как обрабатывается каждая рубрика!")
        
        start_time = datetime.now()
        
        # РЕАЛЬНЫЙ ВЫЗОВ API
        results = orchestrator.run_all_rubrics(limit=test_limit)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print(f"\n⏱️ Общее время выполнения: {total_time:.2f}s")
        print(f"📊 Обработано рубрик: {len(results)}")
        
        # Анализируем результаты
        analyze_rubrics_results(results)
        
        # Сохраняем результат в файл
        save_rubrics_result_to_file(results, f"rubrics_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании метода: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return None


def analyze_rubrics_results(results):
    """Анализирует результаты обработки всех рубрик"""
    print("\n📊 Анализ результатов по рубрикам:")
    print("=" * 60)
    
    successful_rubrics = 0
    failed_rubrics = 0
    total_articles = 0
    
    for i, result in enumerate(results, 1):
        rubric_name = result.get('rubric', 'Unknown')
        pipeline_result = result.get('pipeline_result')
        error = result.get('error')
        
        print(f"\n{i:2d}. {rubric_name}")
        print(f"    Query: '{result.get('query', '')}'")
        print(f"    Category: {result.get('category', '')}")
        
        if error:
            print(f"    ❌ Ошибка: {error}")
            failed_rubrics += 1
        elif pipeline_result:
            if pipeline_result.success:
                print(f"    ✅ Успешно")
                print(f"    Этапы: {pipeline_result.completed_stages}/{pipeline_result.total_stages}")
                print(f"    Время: {pipeline_result.total_execution_time:.2f}s")
                
                # Подсчитываем статьи
                fetcher_data = pipeline_result.results.get('fetcher', {}).data
                if fetcher_data:
                    articles_count = fetcher_data.get('articles_count', 0)
                    total_articles += articles_count
                    print(f"    Статей получено: {articles_count}")
                
                successful_rubrics += 1
            else:
                print(f"    ⚠️ Частично успешно")
                print(f"    Этапы: {pipeline_result.completed_stages}/{pipeline_result.total_stages}")
                if pipeline_result.errors:
                    print(f"    Ошибки: {'; '.join(pipeline_result.errors)}")
                failed_rubrics += 1
        else:
            print("    ❓ Неизвестный результат")
            failed_rubrics += 1
    
    print("\n" + "=" * 60)
    print("🎯 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Успешных рубрик: {successful_rubrics}")
    print(f"   Неудачных рубрик: {failed_rubrics}")
    print(f"   Всего обработано: {len(results)}")
    print(f"   Всего получено статей: {total_articles}")
    
    success_rate = (successful_rubrics / len(results)) * 100 if results else 0
    print(f"   Процент успеха: {success_rate:.1f}%")


def save_rubrics_result_to_file(results, filename):
    """Сохраняет результаты рубрик в файл для анализа"""
    try:
        # Преобразуем результаты в JSON-сериализуемый формат
        json_results = []
        
        for result in results:
            json_result = {
                "rubric": result.get("rubric"),
                "category": result.get("category"),
                "query": result.get("query"),
                "error": result.get("error")
            }
            
            pipeline_result = result.get("pipeline_result")
            if pipeline_result:
                json_result["pipeline_result"] = {
                    "success": pipeline_result.success,
                    "total_stages": pipeline_result.total_stages,
                    "completed_stages": pipeline_result.completed_stages,
                    "total_execution_time": pipeline_result.total_execution_time,
                    "errors": pipeline_result.errors,
                    "results": {}
                }
                
                for stage_name, stage_result in pipeline_result.results.items():
                    json_result["pipeline_result"]["results"][stage_name] = {
                        "success": stage_result.success,
                        "execution_time": stage_result.execution_time,
                        "error_message": stage_result.error_message,
                        "data": stage_result.data
                    }
            
            json_results.append(json_result)
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Результаты сохранены в файл: {filepath}")
        
    except Exception as e:
        print(f"\n⚠️ Не удалось сохранить результаты: {e}")


def test_run_all_rubrics_dry_run(orchestrator):
    """Тестирует метод run_all_rubrics (показывает что будет обработано)"""
    print("\n=== Предварительный просмотр run_all_rubrics ===")
    
    if not orchestrator:
        print("❌ Оркестратор не создан, пропускаем тест")
        return
    
    try:
        # Проверяем что метод существует
        if hasattr(orchestrator, 'run_all_rubrics'):
            print("✅ Метод run_all_rubrics найден")
            
            # Получаем активные рубрики для проверки
            active_rubrics = get_active_rubrics()
            print(f"Будет обработано {len(active_rubrics)} активных рубрик")
            
            # Показываем что будет обработано
            print("\nРубрики для обработки:")
            for i, rubric in enumerate(active_rubrics, 1):
                print(f"{i:2d}. {rubric['rubric']} -> query: '{rubric['query']}', category: '{rubric['category']}'")
            
            print(f"\n💡 Для каждой рубрики будет выполнен полный pipeline:")
            print("   1. Получение новостей из API")
            print("   2. Дедупликация и ранжирование через LangChain/FAISS")
            print("   3. Экспорт в Google Sheets")
            
        else:
            print("❌ Метод run_all_rubrics не найден")
    except Exception as e:
        print(f"❌ Ошибка при тестировании метода: {e}")


def main():
    """Основная функция"""
    print("🚀 Тестирование нового функционала рубрик с РЕАЛЬНЫМИ ДАННЫМИ")
    print("=" * 70)
    
    # Настраиваем окружение
    if not setup_environment():
        print("❌ Не удалось настроить окружение")
        return
    
    # Тестируем конфигурацию
    active_rubrics = test_rubrics_config()
    
    # Тестируем создание оркестратора
    orchestrator = test_pipeline_orchestrator()
    
    if not orchestrator:
        print("❌ Не удалось создать оркестратор")
        return
    
    # Показываем предварительный просмотр
    test_run_all_rubrics_dry_run(orchestrator)
    
    # Спрашиваем у пользователя о реальном запуске
    print("\n" + "=" * 70)
    print("⚠️  ВНИМАНИЕ! Сейчас будет запущен РЕАЛЬНЫЙ тест с API вызовами!")
    print("   Это займет несколько минут и потратит API квоты")
    print("   Будут обработаны все активные рубрики")
    
    response = input("\n🤔 Продолжить с реальными API вызовами? (y/N): ").strip().lower()
    
    if response in ['y', 'yes', 'да']:
        print("\n🚀 Запускаем реальный тест...")
        results = test_run_all_rubrics_real(orchestrator)
        
        if results:
            print("\n🎉 Реальный тест завершен успешно!")
            print(f"📊 Обработано рубрик: {len(results)}")
            
            successful_count = len([r for r in results if r.get('pipeline_result') and r['pipeline_result'].success])
            print(f"✅ Успешных: {successful_count}")
            print(f"❌ Неудачных: {len(results) - successful_count}")
        else:
            print("💥 Реальный тест завершился с ошибками")
    else:
        print("\n✋ Реальный тест отменен пользователем")
        print("💡 Для запуска реального теста используйте:")
        print("   orchestrator = create_news_pipeline_orchestrator()")
        print("   results = orchestrator.run_all_rubrics(limit=3)")
    
    print("\n" + "=" * 70)
    print("🎉 Тестирование завершено!")
    
    if active_rubrics:
        print(f"\n📊 Итого: {len(active_rubrics)} активных рубрик готовы к обработке")


if __name__ == "__main__":
    main() 