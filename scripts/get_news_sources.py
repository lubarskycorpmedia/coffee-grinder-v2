# /scripts/test_sources_availability.py

import sys
import os
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Добавляем корневую папку в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import get_news_providers_settings, get_google_settings
from src.services.news.fetcher_fabric import FetcherFactory
from src.services.news.exporter import create_google_sheets_exporter
from src.logger import setup_logger
from dotenv import load_dotenv

# Инициализируем логгер
logger = setup_logger(__name__)

# Массив доменов для тестирования
DOMAINS_TO_TEST = [
    # "New York",
    "ground.news",
    "nytimes.com", 
    "washingtonpost.com",
    "bloomberg.com",
    "thehill.com",
    "reuters.com",
    "wsj.com",
    "newsnationnow.com",
    "breitbart.com",
    "ft.com",
    "axios.com",
    "foxnews.com",
    "newsmax.com",
    "nypost.com",
    "washingtontimes.com",
    "washingtonexaminer.com",
    "dailywire.com",
    "dailysignal.com",
    "time.com",
    "msnbc.com",
    "newsweek.com",
    "cnn.com",
    "politico.com",
    "theguardian.com",
    "theatlantic.com",
    "forbes.com",
    "understandingwar.org"
]

def test_source_availability(fetcher, domain: str, provider_name: str) -> str:
    """
    Тестирует доступность источника в провайдере новостей
    
    Args:
        fetcher: Экземпляр fetcher'а
        domain: Домен для проверки
        provider_name: Название провайдера
    
    Returns:
        Результат проверки: "да" или "нет"
    """
    try:
        # Для MediaStack и NewsData используем специализированные методы проверки источников
        if provider_name in ["mediastack", "newsdata"]:
            # Используем метод check_source_by_domain для прямой проверки источника
            if hasattr(fetcher, 'check_source_by_domain'):
                result = fetcher.check_source_by_domain(domain)
                # Приводим результат к "да"/"нет"
                return "да" if result == "да" else "нет"
            else:
                # Fallback на старый метод если новый метод недоступен
                logger.warning(f"Method check_source_by_domain not found for {provider_name}, using fallback")
                return _test_source_via_news_fetch(fetcher, domain, provider_name)
        
        # Для NewsAPI.org и TheNewsAPI используем старый метод через fetch_news
        else:
            return _test_source_via_news_fetch(fetcher, domain, provider_name)
        
    except Exception as e:
        logger.error(f"Error testing source availability for {domain} in {provider_name}: {e}")
        return "нет"


def _test_source_via_news_fetch(fetcher, domain: str, provider_name: str) -> str:
    """
    Тестирует доступность источника через получение новостей (старый метод)
    
    Args:
        fetcher: Экземпляр fetcher'а
        domain: Домен для проверки
        provider_name: Название провайдера
    
    Returns:
        Результат проверки: "да" или "нет"
    """
    try:
        # Используем единый универсальный метод fetch_news для всех провайдеров
        # Передаем только домен, отключаем любые временные фильтры
        response = fetcher.fetch_news(
            domains=domain,
            published_after=None,  # Отключаем фильтр по дате начала
            published_before=None  # Отключаем фильтр по дате окончания
        )
        
        # Проверяем на ошибку
        if "error" in response:
            return "нет"
        
        # Проверяем наличие статей в стандартизированном формате
        articles = response.get("articles", [])
        return "да" if articles else "нет"
        
    except Exception as e:
        return "нет"


def normalize_domain(domain: str) -> str:
    """
    Нормализует домен: убирает www, https, слеши, приводит к нижнему регистру
    
    Args:
        domain: Исходный домен
        
    Returns:
        Нормализованный домен
    """
    domain = domain.lower().strip()
    domain = domain.replace("https://", "").replace("http://", "")
    domain = domain.replace("www.", "")
    domain = domain.rstrip("/")
    return domain


def update_google_sheets(results: Dict[str, str], provider_name: str):
    """
    Обновляет Google Sheets с результатами тестирования
    Создает exporter напрямую с локальными настройками
    
    Args:
        results: Словарь {домен: результат}
        provider_name: Название провайдера (из config.py)
    """
    try:
        # Очищаем кэш настроек, чтобы подхватить локальную переменную окружения
        from src.config import get_settings
        get_settings.cache_clear()
        get_google_settings.cache_clear()
        
        # Создаем exporter напрямую с локальными настройками
        exporter = create_google_sheets_exporter(worksheet_name="Источники")
        
        # Получаем worksheet для прямой работы
        worksheet = exporter._get_worksheet()
        
        # Проверяем, создался ли лист с автоматическими заголовками от экспортера
        try:
            headers = worksheet.row_values(1)
            
            # Если лист создался с заголовками новостей, очищаем его и создаем правильные заголовки
            if headers and len(headers) > 2 and "Timestamp" in headers:
                # Это лист с заголовками новостей - очищаем его
                worksheet.clear()
                headers = ["Источники"]
                worksheet.update(values=[headers], range_name='A1')
            elif not headers:
                # Пустой лист - создаем заголовки
                headers = ["Источники"]
                worksheet.update(values=[headers], range_name='A1')
            # Если headers содержит только ["Источники"] или ["Источники", "provider"], то всё в порядке
        except:
            # Создаем заголовки если лист пустой
            headers = ["Источники"]
            worksheet.update(values=[headers], range_name='A1')
        
        # Находим колонку для текущего провайдера или создаем новую
        provider_col = None
        for i, header in enumerate(headers, 1):
            if header == provider_name:
                provider_col = i
                break
        
        if provider_col is None:
            # Добавляем новую колонку для провайдера
            provider_col = len(headers) + 1
            # Обновляем заголовок
            cell_address = f"{chr(64 + provider_col)}1"  # A, B, C, etc.
            worksheet.update(values=[[provider_name]], range_name=cell_address)
        
        # Получаем существующие источники из колонки A (пропускаем пустые строки)
        existing_sources_raw = []
        try:
            all_values = worksheet.col_values(1)[1:]  # Пропускаем заголовок
            existing_sources_raw = [s.strip() for s in all_values if s.strip()]
        except:
            pass
        
        # Нормализуем существующие источники
        existing_sources_normalized = [normalize_domain(s) for s in existing_sources_raw]
        
        # Создаем упорядоченный список источников
        ordered_sources = []
        
        # 1. Сначала добавляем источники из DOMAINS_TO_TEST в том же порядке
        for domain in DOMAINS_TO_TEST:
            normalized = normalize_domain(domain)
            ordered_sources.append(domain)  # Сохраняем оригинальный формат для отображения
        
        # 2. Затем добавляем источники из таблицы, которых нет в DOMAINS_TO_TEST
        domains_to_test_normalized = [normalize_domain(d) for d in DOMAINS_TO_TEST]
        for i, existing_normalized in enumerate(existing_sources_normalized):
            if existing_normalized not in domains_to_test_normalized:
                ordered_sources.append(existing_sources_raw[i])  # Добавляем в оригинальном формате
        
        # Перезаписываем колонку A с новым порядком источников
        sources_data = [[source] for source in ordered_sources]
        if sources_data:
            range_to_update = f"A2:A{len(sources_data) + 1}"
            worksheet.update(values=sources_data, range_name=range_to_update)
        
        # Записываем результаты в колонку провайдера
        provider_col_letter = chr(64 + provider_col)
        
        for i, source in enumerate(ordered_sources, 2):  # Начинаем со строки 2
            normalized_source = normalize_domain(source)
            
            # Ищем результат для этого источника в наших данных
            found_result = None
            for test_domain, result in results.items():
                if normalize_domain(test_domain) == normalized_source:
                    found_result = result
                    break
            
            if found_result is not None:
                # Форматируем результат с эмодзи
                if found_result == "да":
                    formatted_result = "✅ да"
                elif found_result == "нет":
                    formatted_result = "❌ нет"
                else:
                    formatted_result = f"⚠️ {found_result}"  # для ошибок и других статусов
                
                cell_address = f"{provider_col_letter}{i}"
                worksheet.update(values=[[formatted_result]], range_name=cell_address)
        
        print(f"✅ Результаты записаны в Google Sheets на лист 'Источники'")
        
    except Exception as e:
        print(f"❌ Ошибка при записи в Google Sheets: {e}")

def main():
    """Основная функция скрипта"""
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(description="Тестирование доступности источников новостей")
    parser.add_argument(
        "--provider", 
        type=str, 
        choices=["thenewsapi", "newsapi", "newsdata", "mediastack"],
        help="Провайдер новостей для тестирования (по умолчанию из config.py)"
    )
    args = parser.parse_args()
    
    # Загружаем переменные окружения как в test_real_pipeline.py
    load_dotenv()
    
    # Настройка локального пути к service account ДО любых импортов (как в test_real_pipeline.py)
    local_service_account_path = ".config/google_service_account.json"
    if os.path.exists(local_service_account_path):
        os.environ['GOOGLE_SERVICE_ACCOUNT_PATH'] = local_service_account_path
        print(f"🔧 Используем локальный service account: {local_service_account_path}")
        # Очищаем кэш настроек, чтобы подхватить новую переменную
        get_google_settings.cache_clear()
    
    logger = setup_logger(__name__)
    
    try:
        # Получаем настройки
        providers_settings = get_news_providers_settings()
        
        # Определяем провайдер: из аргументов или дефолтный
        provider_name = args.provider if args.provider else providers_settings.default_provider
        
        print(f"🔍 Тестирование доступности источников в {provider_name.upper()}")
        print("=" * 60)
        
        # Создаем fetcher
        from src.services.news.fetcher_fabric import create_news_fetcher_from_config
        fetcher = create_news_fetcher_from_config(provider_name)
        
        print(f"🔧 Провайдер: {provider_name}")
        print(f"📰 Тестируется {len(DOMAINS_TO_TEST)} источников")
        print()
        
        # Тестируем каждый домен
        results = {}
        
        for i, domain in enumerate(DOMAINS_TO_TEST, 1):
            print(f"[{i:2d}/{len(DOMAINS_TO_TEST)}] Проверяю {domain}...", end=" ", flush=True)
            
            result = test_source_availability(fetcher, domain, provider_name)
            results[domain] = result
            
            print(f"→ {result}")
            
            # Задержка между запросами (3 секунды)
            if i < len(DOMAINS_TO_TEST):
                time.sleep(3)
        
        print()
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
        print("=" * 40)
        
        # Подсчитываем статистику
        available_count = sum(1 for r in results.values() if r == "да")
        unavailable_count = sum(1 for r in results.values() if r == "нет")
        error_count = len(results) - available_count - unavailable_count
        
        for domain, result in results.items():
            status_icon = "✅" if result == "да" else "❌" if result == "нет" else "⚠️"
            print(f"{status_icon} {domain:<25} → {result}")
        
        print()
        print(f"📈 Статистика:")
        print(f"   Доступно: {available_count}")
        print(f"   Недоступно: {unavailable_count}")
        print(f"   Ошибки: {error_count}")
        print()
        
        # Записываем результаты в Google Sheets
        print("💾 Сохранение результатов в Google Sheets...")
        update_google_sheets(results, provider_name)
        
        print("✅ Тестирование завершено!")
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении скрипта: {e}")
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 