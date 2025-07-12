# /src/services/news/news_processor.py

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from src.services.news.fetcher_fabric import create_news_fetcher_from_config
from src.services.news.exporter import GoogleSheetsExporter, create_google_sheets_exporter
from src.langchain.news_chain import NewsProcessingChain, create_news_processing_chain, NewsItem
from src.openai_client import OpenAIClient
from src.config import get_news_providers_settings, get_ai_settings, get_google_settings
from src.logger import setup_logger


class NewsProcessingError(Exception):
    """Базовое исключение для ошибок обработки новостей"""
    pass


class NewsProcessor:
    """
    Главный класс для обработки новостей: получение -> обработка -> экспорт
    """
    
    def __init__(self, 
                 news_provider: str = "thenewsapi",
                 spreadsheet_id: Optional[str] = None,
                 worksheet_name: str = "News",
                 max_news_items: int = 50,
                 similarity_threshold: float = 0.85,
                 fail_on_errors: bool = False):
        """
        Инициализация процессора новостей
        
        Args:
            news_provider: Провайдер новостей ("thenewsapi", "newsapi")
            spreadsheet_id: ID Google таблицы
            worksheet_name: Имя листа в таблице
            max_news_items: Максимальное количество новостей для обработки
            similarity_threshold: Порог схожести для дедупликации
            fail_on_errors: Прерывать ли обработку при ошибках
        """
        self.news_provider = news_provider
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.max_news_items = max_news_items
        self.similarity_threshold = similarity_threshold
        self.fail_on_errors = fail_on_errors
        
        self._logger = None
        self._news_fetcher = None
        self._openai_client = None
        self._news_chain = None
        self._exporter = None
        
        # Проверяем настройки
        self._validate_settings()
    
    @property
    def logger(self):
        """Ленивое создание логгера"""
        if self._logger is None:
            self._logger = setup_logger(__name__)
        return self._logger
    
    def _validate_settings(self):
        """Проверяет наличие всех необходимых настроек"""
        try:
            # Проверяем настройки новостных провайдеров
            providers_settings = get_news_providers_settings()
            provider_settings = providers_settings.get_provider_settings(self.news_provider)
            
            if provider_settings is None:
                raise NewsProcessingError(f"Provider '{self.news_provider}' not found in configuration")
            
            if not provider_settings.enabled:
                raise NewsProcessingError(f"Provider '{self.news_provider}' is disabled")
            
            # Проверяем настройки AI
            ai_settings = get_ai_settings()
            if not ai_settings.OPENAI_API_KEY:
                raise NewsProcessingError("OPENAI_API_KEY is required")
            
            # Проверяем настройки Google (опционально)
            try:
                google_settings = get_google_settings()
                if not google_settings.GOOGLE_SHEET_ID:
                    self.logger.warning("GOOGLE_SHEET_ID not configured - export to Google Sheets will be disabled")
                if not google_settings.GOOGLE_ACCOUNT_KEY:
                    self.logger.warning("GOOGLE_ACCOUNT_KEY not configured - export to Google Sheets will be disabled")
            except Exception as e:
                self.logger.warning(f"Google settings validation failed: {e}")
                
        except Exception as e:
            raise NewsProcessingError(f"Settings validation failed: {str(e)}")
    
    def _get_news_fetcher(self):
        """Получает фетчер новостей"""
        if self._news_fetcher is None:
            self._news_fetcher = create_news_fetcher_from_config(self.news_provider)
        return self._news_fetcher
    
    def _get_openai_client(self):
        """Получает OpenAI клиент"""
        if self._openai_client is None:
            self._openai_client = OpenAIClient()
        return self._openai_client
    
    def _get_news_chain(self):
        """Получает цепочку обработки новостей"""
        if self._news_chain is None:
            self._news_chain = create_news_processing_chain(
                openai_client=self._get_openai_client(),
                similarity_threshold=self.similarity_threshold,
                max_news_items=self.max_news_items
            )
        return self._news_chain
    
    def _get_exporter(self):
        """Получает экспортер Google Sheets"""
        if self._exporter is None:
            self._exporter = create_google_sheets_exporter(
                spreadsheet_id=self.spreadsheet_id,
                worksheet_name=self.worksheet_name
            )
        return self._exporter
    
    def fetch_news(self, 
                   query: Optional[str] = None,
                   category: Optional[str] = None,
                   language: str = "en",
                   limit: int = 50) -> List[NewsItem]:
        """
        Получает новости от провайдера
        
        Args:
            query: Поисковый запрос
            category: Категория новостей
            language: Язык новостей
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
                news_item = NewsItem(
                    title=article.get('title', ''),
                    description=article.get('description', ''),
                    url=article.get('url', ''),
                    published_at=datetime.fromisoformat(article['published_at'].replace('Z', '+00:00')) if article.get('published_at') else datetime.now(timezone.utc),
                    source=article.get('source', ''),
                    category=article.get('category', category or ''),
                    language=language
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
    
    def process_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Обрабатывает новости (embeddings, дедупликация, ранжирование)
        
        Args:
            news_items: Список новостей для обработки
            
        Returns:
            Список обработанных новостей
        """
        if not news_items:
            self.logger.warning("No news items to process")
            return []
        
        self.logger.info(f"Processing {len(news_items)} news items")
        
        try:
            chain = self._get_news_chain()
            processed_news = chain.process_news(news_items, fail_on_errors=self.fail_on_errors)
            
            self.logger.info(f"Processed {len(processed_news)} news items")
            return processed_news
            
        except Exception as e:
            error_msg = f"Failed to process news: {str(e)}"
            self.logger.error(error_msg)
            if self.fail_on_errors:
                raise NewsProcessingError(error_msg) from e
            return news_items  # Возвращаем исходные новости
    
    def export_to_sheets(self, news_items: List[NewsItem], append: bool = True) -> bool:
        """
        Экспортирует новости в Google Sheets
        
        Args:
            news_items: Список новостей для экспорта
            append: Добавлять к существующим данным или перезаписывать
            
        Returns:
            True если экспорт успешен
        """
        if not news_items:
            self.logger.warning("No news items to export")
            return True
        
        self.logger.info(f"Exporting {len(news_items)} news items to Google Sheets")
        
        try:
            exporter = self._get_exporter()
            success = exporter.export_news(news_items, append=append)
            
            if success:
                self.logger.info("Export to Google Sheets completed successfully")
            else:
                self.logger.error("Export to Google Sheets failed")
            
            return success
            
        except Exception as e:
            error_msg = f"Failed to export to Google Sheets: {str(e)}"
            self.logger.error(error_msg)
            if self.fail_on_errors:
                raise NewsProcessingError(error_msg) from e
            return False
    
    def run_full_pipeline(self, 
                         query: Optional[str] = None,
                         category: Optional[str] = None,
                         language: str = "en",
                         limit: int = 50,
                         export_to_sheets: bool = True,
                         append_to_sheets: bool = True) -> Dict[str, Any]:
        """
        Запускает полный пайплайн обработки новостей
        
        Args:
            query: Поисковый запрос
            category: Категория новостей
            language: Язык новостей
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
            # Шаг 1: Получение новостей
            news_items = self.fetch_news(
                query=query,
                category=category,
                language=language,
                limit=limit
            )
            results["fetched_count"] = len(news_items)
            
            if not news_items:
                self.logger.warning("No news items fetched")
                results["success"] = True
                return results
            
            # Шаг 2: Обработка новостей
            processed_news = self.process_news(news_items)
            results["processed_count"] = len(processed_news)
            
            # Подсчитываем дубликаты
            duplicates = [item for item in processed_news if item.is_duplicate]
            results["duplicates_found"] = len(duplicates)
            
            # Шаг 3: Экспорт в Google Sheets (опционально)
            if export_to_sheets:
                export_success = self.export_to_sheets(processed_news, append=append_to_sheets)
                if export_success:
                    results["exported_count"] = len(processed_news)
            
            results["success"] = True
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
            
            if self.fail_on_errors:
                raise NewsProcessingError(error_msg) from e
        
        finally:
            end_time = datetime.now(timezone.utc)
            results["end_time"] = end_time.isoformat()
            results["duration_seconds"] = (end_time - start_time).total_seconds()
            
            self.logger.info(f"Pipeline completed in {results['duration_seconds']:.2f} seconds")
            self.logger.info(f"Results: {results['fetched_count']} fetched, {results['processed_count']} processed, {results['exported_count']} exported")
        
        return results
    
    def get_export_summary(self) -> Dict[str, Any]:
        """
        Получает сводную информацию об экспорте
        
        Returns:
            Словарь с информацией о таблице
        """
        try:
            exporter = self._get_exporter()
            return exporter.get_export_summary()
        except Exception as e:
            self.logger.error(f"Failed to get export summary: {str(e)}")
            return {"error": str(e)}


def create_news_processor(news_provider: str = "thenewsapi",
                         **kwargs) -> NewsProcessor:
    """
    Удобная функция для создания процессора новостей
    
    Args:
        news_provider: Провайдер новостей
        **kwargs: Дополнительные параметры для NewsProcessor
        
    Returns:
        Экземпляр NewsProcessor
    """
    return NewsProcessor(news_provider=news_provider, **kwargs) 