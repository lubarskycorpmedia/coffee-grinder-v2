# scripts/check_data_completeness.py
"""
Проверка полноты данных в pipeline - убеждаемся что все поля сохраняются
"""
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.news.pipeline import create_news_pipeline_orchestrator
from src.config import get_google_settings
from dotenv import load_dotenv


def check_data_completeness():
    """Проверяет полноту данных в pipeline"""
    print("🔍 Проверка полноты данных в pipeline")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Для локального тестирования используем локальный путь
    local_service_account_path = ".config/google_service_account.json"
    if os.path.exists(local_service_account_path):
        os.environ['GOOGLE_SERVICE_ACCOUNT_PATH'] = local_service_account_path
        get_google_settings.cache_clear()
    
    # Создаем оркестратор
    orchestrator = create_news_pipeline_orchestrator(
        provider="thenewsapi",
        worksheet_name="DataCheck"
    )
    
    # Запускаем pipeline
    result = orchestrator.run_pipeline(
        query="technology",
        categories=["tech"],
        limit=2  # Небольшое количество для проверки
    )
    
    if not result.success:
        print("❌ Pipeline завершился с ошибкой")
        return
    
    # Получаем обработанные статьи
    dedup_result = result.results.get("deduplication")
    if not dedup_result or not dedup_result.success:
        print("❌ Этап дедупликации не выполнен")
        return
    
    processed_articles = dedup_result.data["processed_articles"]
    
    print(f"✅ Получено {len(processed_articles)} обработанных статей")
    print()
    
    # Проверяем каждую статью на полноту данных
    for i, article in enumerate(processed_articles, 1):
        print(f"📰 Статья {i}:")
        print(f"   Title: {article.title[:50]}...")
        print(f"   URL: {article.url}")
        print(f"   🖼️ Image URL: {article.image_url or 'НЕТ'}")
        print(f"   UUID: {article.uuid or 'НЕТ'}")
        print(f"   Keywords: {article.keywords[:50] if article.keywords else 'НЕТ'}...")
        print(f"   Snippet: {article.snippet[:50] if article.snippet else 'НЕТ'}...")
        print(f"   Source: {article.source}")
        print(f"   Category: {article.category}")
        print(f"   Language: {article.language}")
        print(f"   Published: {article.published_at}")
        print(f"   Relevance Score: {article.relevance_score}")
        print(f"   Similarity Score: {article.similarity_score}")
        print()
    
    # Проверяем наличие изображений
    articles_with_images = [a for a in processed_articles if a.image_url]
    articles_without_images = [a for a in processed_articles if not a.image_url]
    
    print("📊 Сводка по изображениям:")
    print(f"   ✅ С изображениями: {len(articles_with_images)}")
    print(f"   ❌ Без изображений: {len(articles_without_images)}")
    
    if articles_with_images:
        print("\\n🖼️ Примеры URL изображений:")
        for article in articles_with_images[:3]:
            print(f"   - {article.image_url}")
    
    # Проверяем другие поля
    fields_to_check = {
        "uuid": "UUID",
        "keywords": "Keywords", 
        "snippet": "Snippet",
        "relevance_score": "Relevance Score"
    }
    
    print("\\n📋 Сводка по другим полям:")
    for field, name in fields_to_check.items():
        filled_count = sum(1 for a in processed_articles if getattr(a, field))
        print(f"   {name}: {filled_count}/{len(processed_articles)} заполнено")


if __name__ == "__main__":
    check_data_completeness() 