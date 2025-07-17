"""
Главный оркестратор для полного pipeline обработки новостей
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.config import get_pipeline_settings, get_faiss_settings
from src.logger import setup_logger
from src.services.news.fetcher_fabric import create_news_fetcher_from_config
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
                 worksheet_name: str = "News",
                 ranking_criteria: Optional[str] = None):
        """
        Инициализация оркестратора
        
        Args:
            worksheet_name: Имя листа в Google Sheets
            ranking_criteria: Критерии ранжирования для LLM
        """
        self.worksheet_name = worksheet_name
        self.ranking_criteria = ranking_criteria or self._get_default_ranking_criteria()
        
        # Загружаем настройки
        self.pipeline_settings = get_pipeline_settings()
        self.faiss_settings = get_faiss_settings()
        
        # Инициализируем логгер
        self.logger = setup_logger(__name__)
        
        # Компоненты pipeline (создаются лениво)
        self._news_chain = None
        self._exporter = None
        
        self.logger.info("NewsPipelineOrchestrator initialized for multi-provider processing")
    
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
    
    def run_pipeline(self, config_requests: List[Dict[str, Any]]) -> PipelineResult:
        """
        Запускает полный pipeline обработки новостей для всех запросов
        
        Args:
            config_requests: Список запросов в формате [{"provider": "name", "url": "...", "config": {...}}]
            
        Returns:
            PipelineResult с детальными результатами выполнения
        """
        start_time = time.time()
        
        self.logger.info(f"Starting pipeline for {len(config_requests)} requests")
        
        # Инициализируем результат
        results = {
            "fetcher": StageResult(success=False, execution_time=0.0),
            "deduplication": StageResult(success=False, execution_time=0.0),
            "export": StageResult(success=False, execution_time=0.0)
        }
        errors = []
        completed_stages = 0
        
        try:
            # ЭТАП 1: Получение новостей от всех провайдеров
            self.logger.info("Stage 1: Fetching news from all providers")
            stage_result = self._run_fetch_stage(config_requests)
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
                    if not self.pipeline_settings.ENABLE_PARTIAL_RESULTS:
                        return self._create_pipeline_result(False, 3, completed_stages, results, errors, start_time)
                    else:
                        errors.append(f"Export stage failed: {stage_result.error_message}")
                else:
                    completed_stages += 1
        
        except Exception as e:
            errors.append(f"Pipeline exception: {str(e)}")
            self.logger.error(f"Pipeline failed with exception: {str(e)}")
        
        # Определяем успешность выполнения
        success = completed_stages >= 3 and len(errors) == 0
        
        return self._create_pipeline_result(success, 3, completed_stages, results, errors, start_time)
    
    def _run_fetch_stage(self, config_requests: List[Dict[str, Any]]) -> StageResult:
        """Выполняет этап получения новостей для всех провайдеров"""
        start_time = time.time()
        
        all_articles = []
        successful_requests = 0
        failed_requests = 0
        warnings = []
        
        for i, req in enumerate(config_requests):
            provider_name = req.get("provider")
            provider_url = req.get("url")
            provider_config = req.get("config", {})
            
            if not provider_name:
                error_msg = "Provider name not specified in config_requests"
                self.logger.error(error_msg)
                failed_requests += 1
                warnings.append(f"Request {i+1}: {error_msg}")
                continue
            
            if not provider_url:
                error_msg = f"Provider URL not specified for {provider_name}"
                self.logger.error(error_msg)
                failed_requests += 1
                warnings.append(f"Request {i+1}: {error_msg}")
                continue
            
            self.logger.info(f"Processing request {i+1}/{len(config_requests)} for provider {provider_name}")
            self.logger.info(f"URL: {provider_url}")
            self.logger.info(f"Config: {provider_config}")
            
            try:
                fetcher = create_news_fetcher_from_config(provider_name)
                
                # Получаем новости через fetcher с новым интерфейсом
                response = fetcher.fetch_news(url=provider_url, params=provider_config)
                
                # Проверяем на наличие ошибки
                if "error" in response:
                    error_msg = str(response.get("error", "Unknown fetch error"))
                    self.logger.warning(f"Request {i+1} failed for provider {provider_name}: {error_msg}")
                    failed_requests += 1
                    warnings.append(f"Request {i+1} ({provider_name}): {error_msg}")
                    continue
                
                # Получаем статьи
                articles = response.get("articles", [])
                
                if not articles:
                    warning_msg = f"No articles found for provider {provider_name}"
                    self.logger.warning(f"Request {i+1}: {warning_msg}")
                    warnings.append(f"Request {i+1} ({provider_name}): {warning_msg}")
                    # НЕ считаем это фатальной ошибкой - продолжаем обработку
                    continue
                
                # Преобразуем в NewsItem объекты
                news_items = []
                for article in articles:
                    try:
                        # Парсим дату публикации
                        published_at_raw = article.get("published_at", "")
                        if published_at_raw:
                            # Проверяем тип данных
                            if isinstance(published_at_raw, datetime):
                                # Уже datetime объект
                                published_at = published_at_raw
                            elif isinstance(published_at_raw, str):
                                # Строка - парсим
                                if published_at_raw.endswith("Z"):
                                    published_at = datetime.fromisoformat(published_at_raw.replace("Z", "+00:00"))
                                elif "+" in published_at_raw or published_at_raw.endswith("00:00"):
                                    published_at = datetime.fromisoformat(published_at_raw)
                                else:
                                    # Пытаемся парсить как ISO без таймзоны
                                    published_at = datetime.fromisoformat(published_at_raw + "+00:00")
                            else:
                                # Неизвестный тип - используем текущее время
                                published_at = datetime.now()
                        else:
                            # Если даты нет, используем текущее время
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
                            language=article.get("language"),
                            image_url=article.get("image_url"),
                            uuid=article.get("uuid"),
                            keywords=article.get("keywords"),
                            snippet=article.get("snippet")
                        )
                        news_items.append(news_item)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse article for provider {provider_name}: {str(e)}")
                        continue
                
                articles_count = len(news_items)
                self.logger.info(f"Request {i+1}: Successfully processed {articles_count} articles from {provider_name}")
                all_articles.extend(news_items)
                successful_requests += 1
                
            except Exception as e:
                error_msg = f"Fetch stage exception for provider {provider_name}: {str(e)}"
                self.logger.error(error_msg)
                failed_requests += 1
                warnings.append(f"Request {i+1} ({provider_name}): {error_msg}")
                continue
        
        execution_time = time.time() - start_time
        
        # Определяем успешность: успешен если хотя бы один запрос прошел ИЛИ есть статьи
        is_successful = successful_requests > 0 or len(all_articles) > 0
        
        self.logger.info(f"Fetch stage summary: {successful_requests} successful, {failed_requests} failed, {len(all_articles)} total articles")
        if warnings:
            self.logger.info(f"Warnings: {len(warnings)} issues encountered")
        
        if is_successful:
            return StageResult(
                success=True,
                execution_time=execution_time,
                data={
                    "articles": all_articles,
                    "articles_count": len(all_articles),
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "warnings": warnings,
                    "raw_response": {"articles": all_articles}
                }
            )
        else:
            # Все запросы завершились ошибкой
            error_msg = f"All {len(config_requests)} requests failed. Warnings: {'; '.join(warnings)}"
            self.logger.error(error_msg)
            return StageResult(
                success=False,
                execution_time=execution_time,
                error_message=error_msg,
                data={
                    "articles": [],
                    "articles_count": 0,
                    "successful_requests": 0,
                    "failed_requests": failed_requests,
                    "warnings": warnings
                }
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
    
    def run_all_rubrics(self, limit: int = 5, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Запускает pipeline для всех активных рубрик
        
        Args:
            limit: Количество новостей на рубрику
            language: Язык поиска (опционально)
            
        Returns:
            Список результатов выполнения pipeline для каждой рубрики
        """
        start_time = time.time()
        
        self.logger.info(f"Starting pipeline for all active rubrics with limit={limit}, language={language}")
        
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
                    config_requests=[{
                        "provider": "thenewsapi_com", # Assuming a default provider for rubrics
                        "url": "https://api.thenewsapi.com/v1/news/all", # Default URL for rubrics
                        "config": {
                            "query": query,
                            "categories": category,
                            "limit": limit,
                            "language": language
                        }
                    }]
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
            "worksheet_name": self.worksheet_name,
            "settings": {
                "default_limit": self.pipeline_settings.DEFAULT_LIMIT,
                "pipeline_timeout": self.pipeline_settings.PIPELINE_TIMEOUT,
                "enable_partial_results": self.pipeline_settings.ENABLE_PARTIAL_RESULTS,
                "faiss_similarity_threshold": self.faiss_settings.FAISS_SIMILARITY_THRESHOLD,
                "max_news_items_for_processing": self.faiss_settings.MAX_NEWS_ITEMS_FOR_PROCESSING
            },
            "components": {
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
        worksheet_name=worksheet_name,
        ranking_criteria=ranking_criteria
    ) 