# /src/langchain/news_chain.py
# News LLM chain 

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
import faiss

from src.openai_client import OpenAIClient
from src.config import get_ai_settings
from src.logger import setup_logger


class LLMProcessingError(Exception):
    """Базовое исключение для ошибок обработки LLM"""
    pass


class EmbeddingError(LLMProcessingError):
    """Ошибка создания embeddings"""
    pass


class RankingError(LLMProcessingError):
    """Ошибка ранжирования новостей"""
    pass


class RateLimitError(LLMProcessingError):
    """Ошибка превышения лимита запросов"""
    pass


class NewsItem:
    """Структура для новостной статьи"""
    
    def __init__(self, 
                 title: str, 
                 description: str, 
                 url: str, 
                 published_at: datetime,
                 source: str,
                 category: Optional[str] = None,
                 language: Optional[str] = None):
        self.title = title
        self.description = description
        self.url = url
        self.published_at = published_at
        self.source = source
        self.category = category
        self.language = language
        self.embedding: Optional[np.ndarray] = None
        self.similarity_score: float = 0.0
        self.relevance_score: float = 5.0
        self.is_duplicate: bool = False
        self.duplicate_of: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь для JSON"""
        return {
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "source": self.source,
            "category": self.category,
            "language": self.language,
            "similarity_score": self.similarity_score,
            "relevance_score": self.relevance_score,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of
        }
    
    def get_content_for_embedding(self) -> str:
        """Получает текст для создания embedding"""
        parts = [self.title, self.description]
        if self.category:
            parts.append(self.category)
        return " ".join(parts)
    
    def get_content_for_ranking(self) -> str:
        """Получает текст для ранжирования"""
        if self.category:
            return f"Заголовок: {self.title}\nОписание: {self.description}\nИсточник: {self.source}\nКатегория: {self.category}"
        else:
            return f"Заголовок: {self.title}\nОписание: {self.description}\nИсточник: {self.source}"


class NewsProcessingChain:
    """LangChain цепочка для обработки новостей"""
    
    def __init__(self, 
                 openai_client: Optional[OpenAIClient] = None,
                 embedding_model: str = "text-embedding-3-small",
                 llm_model: str = "gpt-4o-mini",
                 similarity_threshold: float = 0.85,
                 max_news_items: int = 50,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Инициализация цепочки обработки новостей
        
        Args:
            openai_client: Клиент OpenAI (если None, создается новый)
            embedding_model: Модель для создания embeddings
            llm_model: Модель для LLM операций
            similarity_threshold: Порог схожести для дедупликации
            max_news_items: Максимальное количество новостей для обработки
            max_retries: Максимальное количество повторных попыток при ошибках
            retry_delay: Задержка между повторными попытками (секунды)
        """
        self.openai_client = openai_client or OpenAIClient()
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.similarity_threshold = similarity_threshold
        self.max_news_items = max_news_items
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._logger = None
        
        # Инициализируем LangChain компоненты
        self._setup_langchain_components()
        
        # FAISS индекс для поиска дублей
        self.faiss_index: Optional[faiss.IndexFlatIP] = None
        self.indexed_news: List[NewsItem] = []
    
    @property
    def logger(self):
        """Ленивое создание логгера"""
        if self._logger is None:
            self._logger = setup_logger(__name__)
        return self._logger
    
    def _setup_langchain_components(self):
        """Настройка компонентов LangChain"""
        # Получаем настройки AI
        settings = get_ai_settings()
        api_key = settings.OPENAI_API_KEY
        
        # Embeddings для семантического поиска
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=api_key
        )
        
        # Создаем цепочку для ранжирования
        self.ranking_chain = self._create_ranking_chain(api_key)
    
    def _create_ranking_chain(self, api_key: str):
        """Создание цепочки для ранжирования новостей"""
        # LLM для ранжирования
        llm = ChatOpenAI(
            model=self.llm_model,
            temperature=0.1,
            openai_api_key=api_key
        )
        
        # Промпт для ранжирования новостей
        ranking_prompt = PromptTemplate(
            input_variables=["news_items", "criteria"],
            template="""
Ты - эксперт по анализу новостей. Проанализируй следующие новости и оцени их по критериям важности и актуальности.

Критерии оценки:
{criteria}

Новости для анализа:
{news_items}

Для каждой новости дай оценку от 1 до 10, где:
- 1-3: Низкая важность (локальные события, слухи, неподтвержденная информация)
- 4-6: Средняя важность (региональные события, отраслевые новости)
- 7-8: Высокая важность (национальные события, значимые экономические новости)
- 9-10: Критическая важность (глобальные события, кризисы, прорывные технологии)

Отвечай ТОЛЬКО в формате JSON:
{{
    "rankings": [
        {{"url": "URL_новости", "score": число_от_1_до_10, "reasoning": "краткое_обоснование"}},
        ...
    ]
}}
"""
        )
        
        # Цепочка для ранжирования
        return (
            RunnablePassthrough()
            | ranking_prompt
            | llm
            | StrOutputParser()
        )
    
    def _retry_with_backoff(self, func, *args, max_retries: int = None, **kwargs):
        """
        Выполняет функцию с повторными попытками и экспоненциальной задержкой
        
        Args:
            func: Функция для выполнения
            *args: Позиционные аргументы функции
            max_retries: Максимальное количество попыток (если None, использует self.max_retries)
            **kwargs: Именованные аргументы функции
            
        Returns:
            Результат выполнения функции
            
        Raises:
            LLMProcessingError: Если все попытки исчерпаны
        """
        retries = max_retries or self.max_retries
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Проверяем тип ошибки
                error_message = str(e).lower()
                
                if "rate limit" in error_message or "429" in error_message:
                    if attempt < retries:
                        delay = self.retry_delay * (2 ** attempt)  # Экспоненциальная задержка
                        self.logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{retries + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        raise RateLimitError(f"Rate limit exceeded after {retries + 1} attempts: {str(e)}")
                
                elif "timeout" in error_message or "connection" in error_message:
                    if attempt < retries:
                        delay = self.retry_delay * (attempt + 1)  # Линейная задержка для сетевых ошибок
                        self.logger.warning(f"Network error, retrying in {delay}s (attempt {attempt + 1}/{retries + 1}): {str(e)}")
                        time.sleep(delay)
                        continue
                    else:
                        raise LLMProcessingError(f"Network error after {retries + 1} attempts: {str(e)}")
                
                elif "authentication" in error_message or "unauthorized" in error_message:
                    # Не повторяем попытки при ошибках аутентификации
                    raise LLMProcessingError(f"Authentication error: {str(e)}")
                
                else:
                    # Для других ошибок делаем ограниченные повторы
                    if attempt < min(2, retries):  # Максимум 2 попытки для неизвестных ошибок
                        delay = self.retry_delay
                        self.logger.warning(f"Unknown error, retrying in {delay}s (attempt {attempt + 1}/{retries + 1}): {str(e)}")
                        time.sleep(delay)
                        continue
                    else:
                        raise LLMProcessingError(f"Unknown error after {attempt + 1} attempts: {str(e)}")
        
        # Если дошли сюда, значит все попытки исчерпаны
        raise LLMProcessingError(f"All retry attempts failed. Last error: {str(last_exception)}")

    def create_embeddings(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Создает embeddings для новостей с обработкой ошибок и повторными попытками
        
        Args:
            news_items: Список новостей
            
        Returns:
            Список новостей с embeddings
            
        Raises:
            EmbeddingError: При критических ошибках создания embeddings
        """
        self.logger.info(f"Creating embeddings for {len(news_items)} news items")
        
        if not news_items:
            return news_items
        
        # Получаем тексты для embedding
        texts = [item.get_content_for_embedding() for item in news_items]
        
        def _create_embeddings_batch():
            """Внутренняя функция для создания embeddings"""
            return self.embeddings.embed_documents(texts)
        
        try:
            # Создаем embeddings через LangChain с повторными попытками
            embeddings = self._retry_with_backoff(_create_embeddings_batch)
            
            # Присваиваем embeddings новостям
            for item, embedding in zip(news_items, embeddings):
                item.embedding = np.array(embedding, dtype=np.float32)
            
            self.logger.info(f"Successfully created embeddings for {len(news_items)} items")
            return news_items
            
        except Exception as e:
            error_msg = f"Failed to create embeddings after all retry attempts: {str(e)}"
            self.logger.error(error_msg)
            raise EmbeddingError(error_msg) from e
    
    def deduplicate_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Дедупликация новостей на основе семантического сходства
        
        Args:
            news_items: Список новостей с embeddings
            
        Returns:
            Список уникальных новостей
        """
        self.logger.info(f"Deduplicating {len(news_items)} news items")
        
        if not news_items:
            return news_items
        
        # Проверяем что у всех новостей есть embeddings
        items_with_embeddings = [item for item in news_items if item.embedding is not None]
        if len(items_with_embeddings) != len(news_items):
            self.logger.warning(f"Some items missing embeddings: {len(news_items) - len(items_with_embeddings)}")
        
        if not items_with_embeddings:
            return news_items
        
        # Создаем FAISS индекс для быстрого поиска
        dimension = len(items_with_embeddings[0].embedding)
        index = faiss.IndexFlatIP(dimension)  # Inner Product для косинусного сходства
        
        # Нормализуем embeddings для косинусного сходства
        embeddings_matrix = np.array([item.embedding for item in items_with_embeddings])
        faiss.normalize_L2(embeddings_matrix)
        
        # Добавляем в индекс
        index.add(embeddings_matrix)
        
        # Находим дубли
        duplicates = set()
        for i, item in enumerate(items_with_embeddings):
            if i in duplicates:
                continue
            
            # Ищем похожие новости
            query_vector = embeddings_matrix[i:i+1]
            similarities, indices = index.search(query_vector, len(items_with_embeddings))
            
            # Находим дубли по порогу схожести
            for sim, idx in zip(similarities[0], indices[0]):
                if idx != i and sim >= self.similarity_threshold:
                    # Отмечаем как дубль более позднюю новость
                    if items_with_embeddings[idx].published_at > items_with_embeddings[i].published_at:
                        duplicates.add(idx)
                        items_with_embeddings[idx].is_duplicate = True
                        items_with_embeddings[idx].duplicate_of = items_with_embeddings[i].url
                        items_with_embeddings[idx].similarity_score = float(sim)
                    else:
                        duplicates.add(i)
                        items_with_embeddings[i].is_duplicate = True
                        items_with_embeddings[i].duplicate_of = items_with_embeddings[idx].url
                        items_with_embeddings[i].similarity_score = float(sim)
                        break
        
        # Возвращаем только уникальные новости
        unique_items = [item for i, item in enumerate(items_with_embeddings) if i not in duplicates]
        
        self.logger.info(f"Found {len(duplicates)} duplicates, {len(unique_items)} unique items remain")
        return unique_items
    
    def rank_news(self, news_items: List[NewsItem], criteria: str = None) -> List[NewsItem]:
        """
        Ранжирование новостей по важности с улучшенной обработкой ошибок
        
        Args:
            news_items: Список новостей
            criteria: Критерии ранжирования
            
        Returns:
            Список ранжированных новостей
        """
        self.logger.info(f"Ranking {len(news_items)} news items")
        
        if not news_items:
            return news_items
        
        # Дефолтные критерии
        if criteria is None:
            criteria = """
            1. Глобальная важность и влияние на мировую экономику
            2. Актуальность и новизна информации
            3. Достоверность источника
            4. Потенциальное влияние на технологические рынки
            5. Социальная значимость
            """
        
        # Подготавливаем данные для ранжирования
        news_for_ranking = []
        for i, item in enumerate(news_items):
            news_for_ranking.append(f"{i+1}. {item.get_content_for_ranking()}\nURL: {item.url}\n")
        
        news_text = "\n".join(news_for_ranking)
        
        def _rank_news_batch():
            """Внутренняя функция для ранжирования"""
            return self.ranking_chain.invoke({
                "news_items": news_text,
                "criteria": criteria
            })
        
        try:
            # Вызываем LLM для ранжирования с повторными попытками
            result = self._retry_with_backoff(_rank_news_batch)
            
            # Обрабатываем результат
            ranked_items = self._process_ranking_result(result, news_items)
            
            self.logger.info(f"Successfully ranked {len(ranked_items)} news items")
            return ranked_items
            
        except Exception as e:
            self.logger.error(f"Failed to rank news: {str(e)}")
            # Возвращаем исходный список с дефолтными оценками
            for item in news_items:
                item.relevance_score = 5.0
            return news_items
    
    def _process_ranking_result(self, result: str, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Обрабатывает результат ранжирования LLM
        
        Args:
            result: Результат от LLM
            news_items: Список новостей для ранжирования
            
        Returns:
            Список ранжированных новостей
            
        Raises:
            RankingError: При ошибках парсинга результата
        """
        try:
            # Очищаем результат от возможных префиксов/суффиксов
            result_text = result.strip()
            if "```json" in result_text:
                # Извлекаем JSON из markdown блока
                start = result_text.find("```json") + 7
                end = result_text.find("```", start)
                result_text = result_text[start:end].strip()
            elif "```" in result_text:
                # Извлекаем JSON из обычного блока кода
                start = result_text.find("```") + 3
                end = result_text.find("```", start)
                result_text = result_text[start:end].strip()
            
            # Ищем JSON объект в тексте
            if result_text.startswith("{") and result_text.endswith("}"):
                json_text = result_text
            else:
                # Пытаемся найти JSON объект в тексте
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    raise ValueError("No JSON object found in response")
            
            # Парсим результат
            rankings_data = json.loads(json_text)
            
            # Проверяем структуру данных
            if "rankings" not in rankings_data:
                raise ValueError("Missing 'rankings' key in response")
            
            if not isinstance(rankings_data["rankings"], list):
                raise ValueError("'rankings' should be a list")
            
            # Создаем словарь URL -> оценка
            url_to_score = {}
            for ranking in rankings_data["rankings"]:
                if not isinstance(ranking, dict):
                    continue
                if "url" not in ranking or "score" not in ranking:
                    continue
                
                url = ranking["url"]
                score = ranking["score"]
                
                # Валидируем оценку
                try:
                    score = float(score)
                    if not (1.0 <= score <= 10.0):
                        self.logger.warning(f"Score {score} for {url} is out of range [1-10], clamping")
                        score = max(1.0, min(10.0, score))
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid score for {url}: {score}, using default")
                    score = 5.0
                
                url_to_score[url] = score
            
            # Присваиваем оценки
            for item in news_items:
                item.relevance_score = url_to_score.get(item.url, 5.0)  # Дефолтная оценка
            
            # Сортируем по убыванию оценки
            ranked_items = sorted(news_items, key=lambda x: x.relevance_score, reverse=True)
            
            return ranked_items
            
        except json.JSONDecodeError as e:
            raise RankingError(f"Failed to parse JSON response: {str(e)}")
        except Exception as e:
            raise RankingError(f"Failed to process ranking result: {str(e)}")

    def process_news(self, 
                    news_items: List[NewsItem], 
                    ranking_criteria: str = None,
                    fail_on_errors: bool = False) -> List[NewsItem]:
        """
        Полная обработка новостей: embeddings -> дедупликация -> ранжирование
        
        Args:
            news_items: Список новостей
            ranking_criteria: Критерии ранжирования
            fail_on_errors: Если True, прерывает обработку при ошибках, иначе продолжает с частичными результатами
            
        Returns:
            Список обработанных и ранжированных новостей
        """
        self.logger.info(f"Processing {len(news_items)} news items")
        
        if not news_items:
            return news_items
        
        # Ограничиваем количество для обработки
        if len(news_items) > self.max_news_items:
            self.logger.warning(f"Too many items ({len(news_items)}), processing only {self.max_news_items}")
            news_items = news_items[:self.max_news_items]
        
        processed_items = news_items.copy()
        
        try:
            # Шаг 1: Создание embeddings
            processed_items = self.create_embeddings(processed_items)
        except EmbeddingError as e:
            if fail_on_errors:
                raise
            self.logger.error(f"Embeddings failed, skipping deduplication: {str(e)}")
            # Продолжаем без дедупликации
        
        try:
            # Шаг 2: Дедупликация (только если есть embeddings)
            if processed_items and processed_items[0].embedding is not None:
                unique_items = self.deduplicate_news(processed_items)
            else:
                unique_items = processed_items
        except Exception as e:
            if fail_on_errors:
                raise LLMProcessingError(f"Deduplication failed: {str(e)}")
            self.logger.error(f"Deduplication failed, using all items: {str(e)}")
            unique_items = processed_items
        
        try:
            # Шаг 3: Ранжирование
            ranked_items = self.rank_news(unique_items, ranking_criteria)
        except RankingError as e:
            if fail_on_errors:
                raise
            self.logger.error(f"Ranking failed, using default scores: {str(e)}")
            # Устанавливаем дефолтные оценки
            for item in unique_items:
                item.relevance_score = 5.0
            ranked_items = unique_items
        
        self.logger.info(f"Processing complete: {len(ranked_items)} final items")
        return ranked_items


def create_news_processing_chain(openai_client: Optional[OpenAIClient] = None,
                               **kwargs) -> NewsProcessingChain:
    """
    Удобная функция для создания цепочки обработки новостей
    
    Args:
        openai_client: Клиент OpenAI
        **kwargs: Дополнительные параметры для NewsProcessingChain
        
    Returns:
        Экземпляр NewsProcessingChain
    """
    return NewsProcessingChain(openai_client=openai_client, **kwargs) 