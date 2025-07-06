# scripts/get_categories.py

import os
import sys
from collections import Counter

# Добавляем путь к src для импорта модулей
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
sys.path.insert(0, project_root)

from src.services.news.fetcher_fabric import create_news_fetcher


def load_environment():
    """Загружает переменные окружения"""
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
    
    # Проверяем API токен
    token = os.getenv('THENEWSAPI_API_TOKEN')
    if not token or token == 'your_token_here':
        print("❌ Отсутствует THENEWSAPI_API_TOKEN")
        return False
    
    print("✅ API токен найден")
    return True


def get_all_categories():
    """Получает все доступные категории из API"""
    print("🔍 Получаем список всех источников для анализа категорий...")
    
    try:
        # Создаем fetcher
        api_token = os.getenv('THENEWSAPI_API_TOKEN')
        fetcher = create_news_fetcher("thenewsapi", api_token=api_token)
        
        # Получаем все источники
        sources_response = fetcher.get_sources()
        
        if "error" in sources_response:
            print(f"❌ Ошибка при получении источников: {sources_response['error']}")
            return None
        
        sources = sources_response.get('data', [])
        print(f"✅ Получено {len(sources)} источников")
        
        # Собираем все категории
        all_categories = []
        for source in sources:
            categories = source.get('categories', [])
            if isinstance(categories, list):
                all_categories.extend(categories)
            elif isinstance(categories, str):
                # На случай если категории возвращаются как строка
                all_categories.extend(categories.split(','))
        
        # Подсчитываем частоту категорий
        category_counts = Counter(all_categories)
        
        print(f"\n📊 НАЙДЕНО {len(category_counts)} УНИКАЛЬНЫХ КАТЕГОРИЙ:")
        print("=" * 60)
        
        # Сортируем по алфавиту
        for category in sorted(category_counts.keys()):
            count = category_counts[category]
            print(f"📂 {category:<20} ({count:>4} источников)")
        
        print("=" * 60)
        print(f"📈 Всего источников проанализировано: {len(sources)}")
        print(f"🏷️  Всего уникальных категорий: {len(category_counts)}")
        
        # Показываем топ-10 самых популярных категорий
        print(f"\n🔥 ТОП-10 САМЫХ ПОПУЛЯРНЫХ КАТЕГОРИЙ:")
        print("-" * 40)
        for category, count in category_counts.most_common(10):
            print(f"🥇 {category:<20} ({count:>4} источников)")
        
        return sorted(category_counts.keys())
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None


def main():
    """Главная функция"""
    print("=" * 60)
    print("📂 ПОЛУЧЕНИЕ ВСЕХ ДОСТУПНЫХ КАТЕГОРИЙ")
    print("=" * 60)
    
    # Загружаем переменные окружения
    if not load_environment():
        print("\n❌ Не удалось загрузить API токен")
        return
    
    # Получаем категории
    categories = get_all_categories()
    
    if categories:
        print(f"\n✅ АНАЛИЗ ЗАВЕРШЕН УСПЕШНО!")
        print(f"💡 Теперь вы знаете все {len(categories)} доступных категорий")
        
        # Сохраняем в файл для справки
        categories_file = os.path.join(project_root, 'scripts', 'available_categories.txt')
        with open(categories_file, 'w', encoding='utf-8') as f:
            f.write("# Доступные категории TheNewsAPI.com\n")
            f.write(f"# Получено: {len(categories)} категорий\n\n")
            for category in categories:
                f.write(f"{category}\n")
        
        print(f"📝 Список сохранен в: {categories_file}")
    else:
        print("\n❌ Не удалось получить категории")


if __name__ == "__main__":
    main() 