"""
Главный оркестратор для полного pipeline обработки новостей
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.config import get_pipeline_settings, get_faiss_settings
from src.logger import setup_logger
from src.services.news.fetcher_fabric import create_news_fetcher_with_config
from src.langchain.news_chain import NewsProcessingChain, NewsItem, create_news_processing_chain
from src.services.news.exporter import GoogleSheetsExporter, create_google_sheets_exporter
from src.services.news.rubrics_config import get_active_rubrics


@dataclass
class StageResult:
    """Результат выполнения отдельного этапа pipeline"""
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class PipelineResult:
    """Результат выполнения полного pipeline"""
    success: bool
    total_stages: int
    completed_stages: int
    total_execution_time: float
    results: Dict[str, StageResult]
    errors: List[str]


class NewsPipelineOrchestrator:
    """
    Главный оркестратор для полного pipeline обработки новостей
    
    Выполняет последовательность:
    1. Fetcher - получение новостей из API
    2. LangChain - дедупликация и ранжирование через FAISS
    3. Export - экспорт в Google Sheets
    """
    
    def __init__(self, 
                 provider: str = "thenewsapi",
                 worksheet_name: str = "News",
                 ranking_criteria: Optional[str] = None):
        """
        Инициализация оркестратора
        
        Args:
            provider: Провайдер новостей (по умолчанию "thenewsapi")
            worksheet_name: Имя листа в Google Sheets
            ranking_criteria: Критерии ранжирования для LLM
        """
        self.provider = provider
        self.worksheet_name = worksheet_name
        self.ranking_criteria = ranking_criteria or self._get_default_ranking_criteria()
        
        # Загружаем настройки
        self.pipeline_settings = get_pipeline_settings()
        self.faiss_settings = get_faiss_settings()
        
        # Инициализируем логгер
        self.logger = setup_logger(__name__)
        
        # Компоненты pipeline (создаются лениво)
        self._fetcher = None
        self._news_chain = None
        self._exporter = None
        
        self.logger.info(f"NewsPipelineOrchestrator initialized with provider: {provider}")
    
    def _get_default_ranking_criteria(self) -> str:
        """Возвращает дефолтные критерии ранжирования"""
        return """
        Критерии оценки важности новостей:
        
        ВЫСОКАЯ ВАЖНОСТЬ (7-10):
        - Геополитические события и международные конфликты
        - Крупные экономические события (изменения курсов валют, кризисы)
        - Технологические прорывы и инновации
        - Катастрофы и чрезвычайные ситуации
        - Решения правительств, влияющие на экономику
        
        СРЕДНЯЯ ВАЖНОСТЬ (4-6):
        - Отраслевые новости и корпоративные события
        - Региональные политические события
        - Спортивные события международного уровня
        - Научные открытия и исследования
        
        НИЗКАЯ ВАЖНОСТЬ (1-3):
        - Локальные события без широкого влияния
        - Слухи и неподтвержденная информация
        - Развлекательные новости
        - Повторяющиеся рутинные события
        """
    
    @property
    def fetcher(self):
        """Ленивое создание fetcher'а"""
        if self._fetcher is None:
            self._fetcher = create_news_fetcher_with_config(provider=self.provider)
            self.logger.info(f"Created fetcher for provider: {self.provider}")
        return self._fetcher
    
    @property
    def news_chain(self):
        """Ленивое создание цепочки обработки новостей"""
        if self._news_chain is None:
            self._news_chain = create_news_processing_chain(
                similarity_threshold=self.faiss_settings.FAISS_SIMILARITY_THRESHOLD,
                max_news_items=self.faiss_settings.MAX_NEWS_ITEMS_FOR_PROCESSING
            )
            self.logger.info("Created news processing chain")
        return self._news_chain
    
    @property
    def exporter(self):
        """Ленивое создание экспортера"""
        if self._exporter is None:
            self._exporter = create_google_sheets_exporter(
                worksheet_name=self.worksheet_name
            )
            self.logger.info(f"Created Google Sheets exporter for worksheet: {self.worksheet_name}")
        return self._exporter
    
    def run_pipeline(self, 
                    query: str, 
                    categories: List[str],
                    limit: Optional[int] = None,
                    language: str = "en") -> PipelineResult:
        """
        Запускает полный pipeline обработки новостей
        
        Args:
            query: Поисковый запрос
            categories: Список категорий новостей
            limit: Количество новостей (по умолчанию из настроек)
            language: Язык поиска (всегда "en" согласно требованиям)
            
        Returns:
            PipelineResult с детальными результатами выполнения
        """
        start_time = time.time()
        
        # Параметры pipeline
        limit = limit or self.pipeline_settings.DEFAULT_LIMIT
        language = self.pipeline_settings.DEFAULT_LANGUAGE  # Всегда "en"
        categories_str = ",".join(categories)
        
        self.logger.info(f"Starting pipeline: query='{query}', categories={categories}, limit={limit}")
        
        # Инициализируем результат
        results = {
            "fetcher": StageResult(success=False, execution_time=0.0),
            "deduplication": StageResult(success=False, execution_time=0.0),
            "export": StageResult(success=False, execution_time=0.0)
        }
        errors = []
        completed_stages = 0
        
        try:
            # ЭТАП 1: Получение новостей
            self.logger.info("Stage 1: Fetching news")
            stage_result = self._run_fetch_stage(query, categories_str, limit, language)
            results["fetcher"] = stage_result
            
            if not stage_result.success:
                if not self.pipeline_settings.ENABLE_PARTIAL_RESULTS:
                    return self._create_pipeline_result(False, 3, completed_stages, results, errors, start_time)
                else:
                    errors.append(f"Fetcher stage failed: {stage_result.error_message}")
            else:
                completed_stages += 1
                fetched_articles = stage_result.data["articles"]
                
                # ЭТАП 2: Дедупликация и ранжирование
                self.logger.info("Stage 2: Deduplication and ranking")
                stage_result = self._run_deduplication_stage(fetched_articles)
                results["deduplication"] = stage_result
                
                if not stage_result.success:
                    if not self.pipeline_settings.ENABLE_PARTIAL_RESULTS:
                        return self._create_pipeline_result(False, 3, completed_stages, results, errors, start_time)
                    else:
                        errors.append(f"Deduplication stage failed: {stage_result.error_message}")
                        # Используем исходные статьи для экспорта
                        processed_articles = fetched_articles
                else:
                    completed_stages += 1
                    processed_articles = stage_result.data["processed_articles"]
                
                # ЭТАП 3: Экспорт в Google Sheets
                self.logger.info("Stage 3: Export to Google Sheets")
                stage_result = self._run_export_stage(processed_articles)
                results["export"] = stage_result
                
                if not stage_result.success:
                    errors.append(f"Export stage failed: {stage_result.error_message}")
                else:
                    completed_stages += 1
        
        except Exception as e:
            self.logger.error(f"Unexpected error in pipeline: {str(e)}")
            errors.append(f"Unexpected pipeline error: {str(e)}")
        
        # Определяем общий успех
        overall_success = completed_stages == 3 and len(errors) == 0
        
        return self._create_pipeline_result(overall_success, 3, completed_stages, results, errors, start_time)
    
    def _run_fetch_stage(self, query: str, categories: str, limit: int, language: str) -> StageResult:
        """Выполняет этап получения новостей"""
        start_time = time.time()
        
        try:
            # Получаем новости через fetcher
            response = self.fetcher.fetch_news(
                query=query,
                categories=categories,
                limit=limit,
                language=language
            )
            
            execution_time = time.time() - start_time
            
            # Проверяем на наличие ошибки
            if "error" in response:
                error_msg = str(response.get("error", "Unknown fetch error"))
                self.logger.error(f"Fetch stage failed: {error_msg}")
                return StageResult(
                    success=False,
                    execution_time=execution_time,
                    error_message=error_msg
                )
            
            # Получаем статьи
            articles = response.get("articles", [])
            
            if not articles:
                error_msg = "No articles found"
                self.logger.warning(f"Fetch stage warning: {error_msg}")
                return StageResult(
                    success=False,
                    execution_time=execution_time,
                    error_message=error_msg
                )
            
            # Преобразуем в NewsItem объекты
            news_items = []
            for article in articles:
                try:
                    # Парсим дату публикации
                    published_at_str = article.get("published_at", "")
                    if published_at_str:
                        # Обрабатываем разные форматы даты
                        if published_at_str.endswith("Z"):
                            published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                        elif "+" in published_at_str or published_at_str.endswith("00:00"):
                            published_at = datetime.fromisoformat(published_at_str)
                        else:
                            # Пытаемся парсить как ISO без таймзоны
                            published_at = datetime.fromisoformat(published_at_str + "+00:00")
                    else:
                        # Если даты нет, используем текущее время
                        published_at = datetime.now()
                    
                    news_item = NewsItem(
                        title=article.get("title", ""),
                        description=article.get("description", ""),
                        url=article.get("url", ""),
                        published_at=published_at,
                        source=article.get("source", ""),
                        category=article.get("category"),
                        language=article.get("language", language),
                        image_url=article.get("image_url"),
                        uuid=article.get("uuid"),
                        keywords=article.get("keywords"),
                        snippet=article.get("snippet")
                    )
                    news_items.append(news_item)
                except Exception as e:
                    self.logger.warning(f"Failed to parse article: {str(e)}")
                    continue
            
            self.logger.info(f"Fetched {len(news_items)} articles in {execution_time:.2f}s")
            
            return StageResult(
                success=True,
                execution_time=execution_time,
                data={
                    "articles": news_items,
                    "articles_count": len(news_items),
                    "raw_response": response
                }
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Fetch stage exception: {str(e)}"
            self.logger.error(error_msg)
            return StageResult(
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
    
    def _run_deduplication_stage(self, articles: List[NewsItem]) -> StageResult:
        """Выполняет этап дедупликации и ранжирования"""
        start_time = time.time()
        
        try:
            original_count = len(articles)
            self.logger.info(f"Processing {original_count} articles for deduplication")
            
            # Применяем лимит обработки
            max_items = self.faiss_settings.MAX_NEWS_ITEMS_FOR_PROCESSING
            if len(articles) > max_items:
                self.logger.warning(f"Limiting articles to {max_items} for processing")
                articles = articles[:max_items]
            
            # Обрабатываем через LangChain
            processed_articles = self.news_chain.process_news(
                news_items=articles,
                ranking_criteria=self.ranking_criteria,
                fail_on_errors=False
            )
            
            execution_time = time.time() - start_time
            
            # Подсчитываем дубли
            duplicates_count = sum(1 for item in processed_articles if item.is_duplicate)
            deduplicated_count = len(processed_articles) - duplicates_count
            
            self.logger.info(
                f"Deduplication completed: {original_count} → {deduplicated_count} "
                f"({duplicates_count} duplicates) in {execution_time:.2f}s"
            )
            
            return StageResult(
                success=True,
                execution_time=execution_time,
                data={
                    "processed_articles": processed_articles,
                    "original_count": original_count,
                    "deduplicated_count": deduplicated_count,
                    "duplicates_count": duplicates_count
                }
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Deduplication stage exception: {str(e)}"
            self.logger.error(error_msg)
            return StageResult(
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
    
    def _run_export_stage(self, articles: List[NewsItem]) -> StageResult:
        """Выполняет этап экспорта в Google Sheets"""
        start_time = time.time()
        
        try:
            # Экспортируем в Google Sheets
            export_success = self.exporter.export_news(articles, append=True)
            
            execution_time = time.time() - start_time
            
            if export_success:
                # Получаем URL таблицы
                sheet_url = f"https://docs.google.com/spreadsheets/d/{self.exporter.spreadsheet_id}"
                
                self.logger.info(f"Exported {len(articles)} articles in {execution_time:.2f}s")
                
                return StageResult(
                    success=True,
                    execution_time=execution_time,
                    data={
                        "exported_count": len(articles),
                        "sheet_url": sheet_url,
                        "worksheet_name": self.worksheet_name
                    }
                )
            else:
                error_msg = "Export failed - exporter returned False"
                self.logger.error(error_msg)
                return StageResult(
                    success=False,
                    execution_time=execution_time,
                    error_message=error_msg
                )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Export stage exception: {str(e)}"
            self.logger.error(error_msg)
            return StageResult(
                success=False,
                execution_time=execution_time,
                error_message=error_msg
            )
    
    def _create_pipeline_result(self, 
                               success: bool,
                               total_stages: int,
                               completed_stages: int,
                               results: Dict[str, StageResult],
                               errors: List[str],
                               start_time: float) -> PipelineResult:
        """Создает итоговый результат pipeline"""
        total_execution_time = time.time() - start_time
        
        self.logger.info(
            f"Pipeline completed: success={success}, "
            f"stages={completed_stages}/{total_stages}, "
            f"time={total_execution_time:.2f}s"
        )
        
        return PipelineResult(
            success=success,
            total_stages=total_stages,
            completed_stages=completed_stages,
            total_execution_time=total_execution_time,
            results=results,
            errors=errors
        )
    
    def run_all_rubrics(self, limit: int = 5, language: str = "en") -> List[Dict[str, Any]]:
        """
        Запускает pipeline для всех активных рубрик
        
        Args:
            limit: Количество новостей на рубрику
            language: Язык поиска
            
        Returns:
            Список результатов выполнения pipeline для каждой рубрики
        """
        start_time = time.time()
        
        self.logger.info(f"Starting pipeline for all active rubrics with limit={limit}")
        
        # Получаем активные рубрики
        active_rubrics = get_active_rubrics()
        
        if not active_rubrics:
            self.logger.warning("No active rubrics found")
            return []
        
        self.logger.info(f"Found {len(active_rubrics)} active rubrics to process")
        
        results = []
        
        for i, rubric in enumerate(active_rubrics, 1):
            rubric_name = rubric.get("rubric", "Unknown")
            category = rubric.get("category", "")
            query = rubric.get("query", "")
            
            self.logger.info(f"Processing rubric {i}/{len(active_rubrics)}: '{rubric_name}'")
            
            try:
                # Запускаем pipeline для рубрики
                pipeline_result = self.run_pipeline(
                    query=query,
                    categories=[category],
                    limit=limit,
                    language=language
                )
                
                # Добавляем информацию о рубрике к результату
                rubric_result = {
                    "rubric": rubric_name,
                    "category": category,
                    "query": query,
                    "pipeline_result": pipeline_result
                }
                
                results.append(rubric_result)
                
                self.logger.info(
                    f"Rubric '{rubric_name}' completed: "
                    f"success={pipeline_result.success}, "
                    f"stages={pipeline_result.completed_stages}/{pipeline_result.total_stages}"
                )
                
            except Exception as e:
                error_msg = f"Failed to process rubric '{rubric_name}': {str(e)}"
                self.logger.error(error_msg)
                
                # Добавляем результат с ошибкой
                error_result = {
                    "rubric": rubric_name,
                    "category": category,
                    "query": query,
                    "pipeline_result": None,
                    "error": error_msg
                }
                
                results.append(error_result)
                
                # Продолжаем выполнение для остальных рубрик
                continue
        
        total_time = time.time() - start_time
        successful_rubrics = len([r for r in results if r.get("pipeline_result") and r["pipeline_result"].success])
        
        self.logger.info(
            f"All rubrics processing completed: "
            f"{successful_rubrics}/{len(active_rubrics)} successful, "
            f"total time: {total_time:.2f}s"
        )
        
        return results
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Возвращает статус компонентов pipeline"""
        return {
            "provider": self.provider,
            "worksheet_name": self.worksheet_name,
            "settings": {
                "default_language": self.pipeline_settings.DEFAULT_LANGUAGE,
                "default_limit": self.pipeline_settings.DEFAULT_LIMIT,
                "pipeline_timeout": self.pipeline_settings.PIPELINE_TIMEOUT,
                "enable_partial_results": self.pipeline_settings.ENABLE_PARTIAL_RESULTS,
                "faiss_similarity_threshold": self.faiss_settings.FAISS_SIMILARITY_THRESHOLD,
                "max_news_items_for_processing": self.faiss_settings.MAX_NEWS_ITEMS_FOR_PROCESSING
            },
            "components": {
                "fetcher_initialized": self._fetcher is not None,
                "news_chain_initialized": self._news_chain is not None,
                "exporter_initialized": self._exporter is not None
            }
        }


def create_news_pipeline_orchestrator(provider: str = "thenewsapi",
                                     worksheet_name: str = "News",
                                     ranking_criteria: Optional[str] = None) -> NewsPipelineOrchestrator:
    """
    Удобная функция для создания оркестратора pipeline
    
    Args:
        provider: Провайдер новостей
        worksheet_name: Имя листа в Google Sheets
        ranking_criteria: Критерии ранжирования
        
    Returns:
        Экземпляр NewsPipelineOrchestrator
    """
    return NewsPipelineOrchestrator(
        provider=provider,
        worksheet_name=worksheet_name,
        ranking_criteria=ranking_criteria
    ) 