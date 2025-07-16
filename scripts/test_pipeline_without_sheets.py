# scripts/test_pipeline_without_sheets.py
"""
Тестирование pipeline без Google Sheets экспорта
Демонстрирует работу fetcher + deduplication
"""
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.news.pipeline import NewsPipelineOrchestrator
from src.services.news.fetchers.thenewsapi_com import TheNewsAPIFetcher
from src.langchain.news_chain import NewsProcessingChain
from src.config import get_settings, get_faiss_settings


def test_pipeline_stages():
    """Тестирование отдельных этапов pipeline"""
    print("🧪 Тестирование этапов pipeline без Google Sheets")
    print("=" * 60)
    
    settings = get_settings()
    faiss_settings = get_faiss_settings()
    
    if not settings.THENEWSAPI_API_TOKEN:
        print("❌ THENEWSAPI_API_TOKEN не найден")
        return False
    
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY не найден")
        return False
    
    # Параметры тестирования
    test_params = {
        "query": "artificial intelligence",
        "categories": "tech,business",
        "limit": 5,
        "language": "en"
    }
    
    print(f"📋 Параметры: {test_params}")
    print()
    
    # ЭТАП 1: Fetcher
    print("1️⃣ Тестирование Fetcher")
    print("-" * 40)
    
    try:
        fetcher = TheNewsAPIFetcher(settings.THENEWSAPI_API_TOKEN)
        
        start_time = datetime.now()
        response = fetcher.fetch_news(**test_params)
        fetch_time = (datetime.now() - start_time).total_seconds()
        
        if "error" in response:
            print(f"❌ Ошибка fetcher: {response['error']}")
            return False
        
        articles = response.get("articles", [])
        print(f"✅ Fetcher успешно: {len(articles)} статей за {fetch_time:.2f}s")
        
        if articles:
            print(f"   📰 Первая статья: {articles[0].get('title', 'No title')[:60]}...")
            print(f"   📅 Дата: {articles[0].get('published_at', 'No date')}")
            print(f"   🏷️ Категория: {articles[0].get('category', 'No category')}")
        print()
        
    except Exception as e:
        print(f"❌ Исключение в fetcher: {e}")
        return False
    
    # ЭТАП 2: Deduplication
    print("2️⃣ Тестирование Deduplication")
    print("-" * 40)
    
    try:
        # Создаем NewsProcessingChain
        news_chain = NewsProcessingChain(
            similarity_threshold=faiss_settings.FAISS_SIMILARITY_THRESHOLD,
            max_news_items=faiss_settings.MAX_NEWS_ITEMS_FOR_PROCESSING
        )
        
        # Преобразуем статьи в NewsItem (как в pipeline)
        from src.services.news.news_processor import NewsItem
        
        news_items = []
        for article in articles:
            try:
                # Парсим дату
                published_at_str = article.get("published_at", "")
                if published_at_str:
                    if published_at_str.endswith("Z"):
                        published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                    elif "+" in published_at_str:
                        published_at = datetime.fromisoformat(published_at_str)
                    else:
                        published_at = datetime.fromisoformat(published_at_str + "+00:00")
                else:
                    published_at = datetime.now()
                
                # Извлекаем source как строку
                source_data = article.get("source", "")
                if isinstance(source_data, dict):
                    # Если source - это dict, извлекаем name
                    source_name = source_data.get("name", "") or source_data.get("id", "") or ""
                else:
                    # Если source уже строка
                    source_name = str(source_data) if source_data else ""
                
                news_item = NewsItem(
                    title=article.get("title", ""),
                    description=article.get("description", ""),
                    url=article.get("url", ""),
                    published_at=published_at,
                    source=source_name,
                    category=article.get("category"),
                    language=article.get("language", "en")
                )
                news_items.append(news_item)
            except Exception as e:
                print(f"⚠️ Ошибка парсинга статьи: {e}")
                continue
        
        print(f"📊 Подготовлено {len(news_items)} NewsItem объектов")
        
        # Обрабатываем через NewsChain
        ranking_criteria = """
        Ранжируй новости по важности для IT-аудитории:
        1. Влияние на индустрию
        2. Новизна информации
        3. Практическая значимость
        4. Авторитетность источника
        """
        
        start_time = datetime.now()
        processed_articles = news_chain.process_news(
            news_items=news_items,
            ranking_criteria=ranking_criteria,
            fail_on_errors=False
        )
        dedup_time = (datetime.now() - start_time).total_seconds()
        
        # Анализируем результат
        duplicates_count = sum(1 for item in processed_articles if item.is_duplicate)
        unique_count = len(processed_articles) - duplicates_count
        
        print(f"✅ Deduplication успешно за {dedup_time:.2f}s")
        print(f"   📊 Исходно: {len(news_items)} статей")
        print(f"   📊 Уникальных: {unique_count}")
        print(f"   📊 Дублей: {duplicates_count}")
        print()
        
        # Показываем топ-3 статьи
        unique_articles = [item for item in processed_articles if not item.is_duplicate]
        if unique_articles:
            print("🏆 Топ-3 статьи по рангу:")
            for i, article in enumerate(unique_articles[:3], 1):
                print(f"   {i}. {article.title[:50]}...")
                ranking_score = getattr(article, 'ranking_score', 0.0)
                print(f"      Ранг: {ranking_score:.2f}")
                print(f"      Источник: {article.source}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Исключение в deduplication: {e}")
        return False


def test_full_pipeline_mock():
    """Тестирование полного pipeline с mock экспортом"""
    print("🚀 Тестирование полного pipeline (с mock экспортом)")
    print("=" * 60)
    
    # Создаем оркестратор
    orchestrator = NewsPipelineOrchestrator(
        provider="thenewsapi",
        worksheet_name="TestMock"
    )
    
    # Заменяем exporter на mock
    class MockExporter:
        def __init__(self):
            self.exported_articles = []
            self.spreadsheet_id = "mock_spreadsheet_id_12345"
        
        def export_news(self, articles, append=True):
            self.exported_articles = articles
            return True  # Возвращаем True как успешный экспорт
    
    # Подменяем exporter
    mock_exporter = MockExporter()
    orchestrator._exporter = mock_exporter
    
    # Запускаем pipeline
    test_params = {
        "query": "artificial intelligence",
        "categories": ["tech", "business"],
        "limit": 5
    }
    
    print(f"📋 Параметры: {test_params}")
    print()
    
    start_time = datetime.now()
    result = orchestrator.run_pipeline(**test_params)
    total_time = (datetime.now() - start_time).total_seconds()
    
    print(f"⏱️ Общее время: {total_time:.2f}s")
    print()
    
    # Анализируем результат
    print("📊 Результат pipeline:")
    print(f"   Успех: {'✅' if result.success else '❌'}")
    print(f"   Этапы: {result.completed_stages}/{result.total_stages}")
    print(f"   Время: {result.total_execution_time:.2f}s")
    print()
    
    if result.errors:
        print("⚠️ Ошибки:")
        for error in result.errors:
            print(f"   - {error}")
        print()
    
    # Детали этапов
    for stage_name, stage_result in result.results.items():
        status = "✅" if stage_result.success else "❌"
        print(f"   {stage_name}: {status} ({stage_result.execution_time:.2f}s)")
        if stage_result.error_message:
            print(f"      Ошибка: {stage_result.error_message}")
        if stage_result.data:
            if "articles_count" in stage_result.data:
                print(f"      Статей: {stage_result.data['articles_count']}")
            if "exported_count" in stage_result.data:
                print(f"      Экспортировано: {stage_result.data['exported_count']}")
    
    print()
    
    # Проверяем mock экспорт
    if mock_exporter.exported_articles:
        print(f"📤 Mock экспорт: {len(mock_exporter.exported_articles)} статей")
        print("   Первая статья:")
        first_article = mock_exporter.exported_articles[0]
        print(f"   📰 {first_article.title[:60]}...")
        print(f"   🏷️ Категория: {first_article.category}")
        ranking_score = getattr(first_article, 'ranking_score', 0.0)
        print(f"   📊 Ранг: {ranking_score:.2f}")
    
    return result.success


if __name__ == "__main__":
    print("🔥 Тестирование NewsPipelineOrchestrator без Google Sheets")
    print("=" * 70)
    
    # Тест 1: Отдельные этапы
    success1 = test_pipeline_stages()
    
    print("\n" + "="*70 + "\n")
    
    # Тест 2: Полный pipeline с mock
    success2 = test_full_pipeline_mock()
    
    print("\n" + "="*70)
    
    if success1 and success2:
        print("🎉 Все тесты прошли успешно!")
        print("💡 Pipeline готов к работе (нужно только настроить Google Sheets)")
    else:
        print("💥 Некоторые тесты не прошли")
        print("💡 Проверьте настройки API ключей") 