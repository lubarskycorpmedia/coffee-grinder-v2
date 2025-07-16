# src/services/news/news_processor.py

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field

from src.config import get_news_providers_settings
from src.services.news.fetcher_fabric import FetcherFactory
from src.logger import setup_logger
from src.langchain.news_chain import NewsItem


@dataclass
class NewsProcessingResult:
    """Результат обработки новостей"""
    success: bool
    news_items: List[NewsItem] = field(default_factory=list)
    total_fetched: int = 0
    total_processed: int = 0
    duplicates_removed: int = 0
    errors: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class NewsProcessingError(Exception):
    """Исключение для ошибок обработки новостей"""
    pass


class NewsProcessor:
    """
    Класс для обработки новостей с различными провайдерами
    
    Поддерживает:
    - Получение новостей от различных провайдеров
    - Фильтрацию и валидацию данных
    - Дедупликацию новостей
    - Обработку ошибок
    """
    
    def __init__(self, 
                 news_provider: str = "thenewsapi",
                 fail_on_errors: bool = False,
                 enable_deduplication: bool = True,
                 max_items_per_request: int = 100):
        """
        Инициализация процессора новостей
        
        Args:
            news_provider: Название провайдера новостей
            fail_on_errors: Прерывать выполнение при ошибках
            enable_deduplication: Включить дедупликацию
            max_items_per_request: Максимальное количество элементов за запрос
        """
        self.news_provider = news_provider
        self.fail_on_errors = fail_on_errors
        self.enable_deduplication = enable_deduplication
        self.max_items_per_request = max_items_per_request
        
        # Инициализируем логгер
        self.logger = setup_logger(__name__)
        
        # Кеш для провайдеров
        self._fetcher_cache = {}
        
        self.logger.info(f"NewsProcessor initialized with provider: {news_provider}")
    
    def _get_news_fetcher(self):
        """Получить fetcher для новостей с кешированием"""
        if self.news_provider not in self._fetcher_cache:
            try:
                fetcher = FetcherFactory.create_fetcher_from_config(self.news_provider)
                self._fetcher_cache[self.news_provider] = fetcher
                self.logger.info(f"Created fetcher for provider: {self.news_provider}")
            except Exception as e:
                error_msg = f"Failed to create fetcher for provider {self.news_provider}: {str(e)}"
                self.logger.error(error_msg)
                if self.fail_on_errors:
                    raise NewsProcessingError(error_msg) from e
                return None
        
        return self._fetcher_cache[self.news_provider]
    
    def fetch_news(self, 
                   query: Optional[str] = None,
                   category: Optional[str] = None,
                   language: Optional[str] = None,
                   limit: int = 50) -> List[NewsItem]:
        """
        Получает новости от провайдера
        
        Args:
            query: Поисковый запрос
            category: Категория новостей
            language: Язык новостей (опционально)
            limit: Максимальное количество новостей
            
        Returns:
            Список новостей
        """
        self.logger.info(f"Fetching news from {self.news_provider}")
        
        try:
            fetcher = self._get_news_fetcher()
            
            # Получаем новости
            news_data = fetcher.fetch_news(
                query=query,
                category=category,
                language=language,
                limit=limit
            )
            
            # Конвертируем в NewsItem объекты
            news_items = []
            for article in news_data.get('articles', []):
                # Извлекаем source как строку
                source_data = article.get('source', '')
                if isinstance(source_data, dict):
                    # Если source - это dict, извлекаем name
                    source_name = source_data.get('name', '') or source_data.get('id', '') or ''
                else:
                    # Если source уже строка
                    source_name = str(source_data) if source_data else ''
                    
                news_item = NewsItem(
                    title=article.get('title', ''),
                    description=article.get('description', ''),
                    url=article.get('url', ''),
                    published_at=datetime.fromisoformat(article['published_at'].replace('Z', '+00:00')) if article.get('published_at') else datetime.now(timezone.utc),
                    source=source_name,
                    category=article.get('category', category or ''),
                    language=article.get('language', language or '')
                )
                news_items.append(news_item)
            
            self.logger.info(f"Fetched {len(news_items)} news items")
            return news_items
            
        except Exception as e:
            error_msg = f"Failed to fetch news: {str(e)}"
            self.logger.error(error_msg)
            if self.fail_on_errors:
                raise NewsProcessingError(error_msg) from e
            return []
    
    def search_news(self, 
                    query: str,
                    language: Optional[str] = None,
                    limit: int = 50,
                    **kwargs) -> List[NewsItem]:
        """
        Поиск новостей по запросу
        
        Args:
            query: Поисковый запрос
            language: Язык новостей (опционально)
            limit: Максимальное количество новостей
            **kwargs: Дополнительные параметры для поиска
            
        Returns:
            Список новостей
        """
        self.logger.info(f"Searching news with query: {query}")
        
        try:
            fetcher = self._get_news_fetcher()
            
            # Выполняем поиск
            articles = fetcher.search_news(
                query=query,
                language=language,
                limit=limit,
                **kwargs
            )
            
            # Конвертируем в NewsItem объекты
            news_items = []
            for article in articles:
                # Извлекаем source как строку
                source_data = article.get('source', '')
                if isinstance(source_data, dict):
                    # Если source - это dict, извлекаем name
                    source_name = source_data.get('name', '') or source_data.get('id', '') or ''
                else:
                    # Если source уже строка
                    source_name = str(source_data) if source_data else ''
                    
                news_item = NewsItem(
                    title=article.get('title', ''),
                    description=article.get('description', ''),
                    url=article.get('url', ''),
                    published_at=datetime.fromisoformat(article['published_at'].replace('Z', '+00:00')) if article.get('published_at') else datetime.now(timezone.utc),
                    source=source_name,
                    category=article.get('category', ''),
                    language=article.get('language', language or '')
                )
                news_items.append(news_item)
            
            self.logger.info(f"Found {len(news_items)} news items")
            return news_items
            
        except Exception as e:
            error_msg = f"Failed to search news: {str(e)}"
            self.logger.error(error_msg)
            if self.fail_on_errors:
                raise NewsProcessingError(error_msg) from e
            return []
    
    def validate_news_items(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Валидация и фильтрация новостных элементов
        
        Args:
            news_items: Список новостей для валидации
            
        Returns:
            Список валидных новостей
        """
        valid_items = []
        
        for item in news_items:
            try:
                # Основные проверки
                if not item.title or not item.url:
                    self.logger.warning(f"Skipping item with missing title or URL: {item}")
                    continue
                
                # Проверка на дубликаты URL
                if self.enable_deduplication:
                    if any(existing.url == item.url for existing in valid_items):
                        self.logger.debug(f"Skipping duplicate URL: {item.url}")
                        continue
                
                valid_items.append(item)
                
            except Exception as e:
                self.logger.warning(f"Error validating news item: {str(e)}")
                continue
        
        self.logger.info(f"Validated {len(valid_items)} out of {len(news_items)} news items")
        return valid_items
    
    def run_full_pipeline(self, 
                         query: Optional[str] = None,
                         category: Optional[str] = None,
                         language: Optional[str] = None,
                         limit: int = 50,
                         export_to_sheets: bool = True,
                         append_to_sheets: bool = True) -> Dict[str, Any]:
        """
        Запускает полный пайплайн обработки новостей
        
        Args:
            query: Поисковый запрос
            category: Категория новостей
            language: Язык новостей (опционально)
            limit: Максимальное количество новостей
            export_to_sheets: Экспортировать ли в Google Sheets
            append_to_sheets: Добавлять к существующим данным
            
        Returns:
            Словарь с результатами обработки
        """
        self.logger.info("Starting full news processing pipeline")
        
        start_time = datetime.now(timezone.utc)
        results = {
            "start_time": start_time.isoformat(),
            "query": query,
            "category": category,
            "language": language,
            "limit": limit,
            "fetched_count": 0,
            "processed_count": 0,
            "exported_count": 0,
            "duplicates_found": 0,
            "success": False,
            "errors": []
        }
        
        try:
            # Этап 1: Получение новостей
            self.logger.info("Step 1: Fetching news")
            news_items = self.fetch_news(
                query=query,
                category=category,
                language=language,
                limit=limit
            )
            
            results["fetched_count"] = len(news_items)
            
            if not news_items:
                results["errors"].append("No news items fetched")
                return results
            
            # Этап 2: Валидация и фильтрация
            self.logger.info("Step 2: Validating news items")
            valid_items = self.validate_news_items(news_items)
            
            results["processed_count"] = len(valid_items)
            results["duplicates_found"] = len(news_items) - len(valid_items)
            
            if not valid_items:
                results["errors"].append("No valid news items after filtering")
                return results
            
            # Этап 3: Экспорт (если требуется)
            if export_to_sheets:
                self.logger.info("Step 3: Exporting to Google Sheets")
                try:
                    from src.services.news.exporter import GoogleSheetsExporter
                    
                    exporter = GoogleSheetsExporter()
                    export_result = exporter.export_news_items(
                        news_items=valid_items,
                        append_mode=append_to_sheets
                    )
                    
                    if export_result.get("success"):
                        results["exported_count"] = export_result.get("exported_count", 0)
                    else:
                        results["errors"].append(f"Export failed: {export_result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    error_msg = f"Export error: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Финализация результатов
            end_time = datetime.now(timezone.utc)
            results["end_time"] = end_time.isoformat()
            results["processing_time"] = (end_time - start_time).total_seconds()
            results["duration_seconds"] = results["processing_time"]  # Совместимость с run.py
            results["success"] = True
            
            self.logger.info("News processing pipeline completed successfully")
            return results
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
            
            if self.fail_on_errors:
                raise NewsProcessingError(error_msg) from e
            
            return results
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Получить информацию о текущем провайдере
        
        Returns:
            Словарь с информацией о провайдере
        """
        try:
            fetcher = self._get_news_fetcher()
            if fetcher:
                return {
                    "provider": self.news_provider,
                    "status": "active",
                    "categories": fetcher.get_categories(),
                    "languages": fetcher.get_languages(),
                    "health": fetcher.check_health()
                }
            else:
                return {
                    "provider": self.news_provider,
                    "status": "error",
                    "error": "Failed to initialize fetcher"
                }
        except Exception as e:
            return {
                "provider": self.news_provider,
                "status": "error",
                "error": str(e)
            }


def create_news_processor(news_provider: str = "thenewsapi",
                         max_news_items: int = 50,
                         similarity_threshold: float = 0.85,
                         fail_on_errors: bool = False) -> NewsProcessor:
    """
    Фабричная функция для создания NewsProcessor
    
    Args:
        news_provider: Название провайдера новостей
        max_news_items: Максимальное количество новостей
        similarity_threshold: Порог схожести для дедупликации
        fail_on_errors: Прерывать выполнение при ошибках
        
    Returns:
        Экземпляр NewsProcessor
    """
    return NewsProcessor(
        news_provider=news_provider,
        fail_on_errors=fail_on_errors,
        enable_deduplication=True,
        max_items_per_request=max_news_items
    ) 