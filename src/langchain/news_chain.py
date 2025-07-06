# /src/langchain/news_chain.py
# News LLM chain 

import json
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
        self.relevance_score: float = 0.0
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
        return f"{self.title}\n{self.description}"
    
    def get_content_for_ranking(self) -> str:
        """Получает текст для ранжирования"""
        return f"Title: {self.title}\nDescription: {self.description}\nSource: {self.source}\nCategory: {self.category or 'Unknown'}"


class NewsProcessingChain:
    """LangChain цепочка для обработки новостей"""
    
    def __init__(self, 
                 openai_client: Optional[OpenAIClient] = None,
                 embedding_model: str = "text-embedding-3-small",
                 llm_model: str = "gpt-4o-mini",
                 similarity_threshold: float = 0.85,
                 max_news_items: int = 50):
        """
        Инициализация цепочки обработки новостей
        
        Args:
            openai_client: Клиент OpenAI (если None, создается новый)
            embedding_model: Модель для создания embeddings
            llm_model: Модель для LLM операций
            similarity_threshold: Порог схожести для дедупликации
            max_news_items: Максимальное количество новостей для обработки
        """
        self.openai_client = openai_client or OpenAIClient()
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.similarity_threshold = similarity_threshold
        self.max_news_items = max_news_items
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
        """Настройка LangChain компонентов"""
        try:
            settings = get_ai_settings()
            api_key = settings.OPENAI_API_KEY
        except Exception:
            api_key = None
        
        # Embeddings
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=api_key
        )
        
        # LLM для ранжирования
        self.llm = ChatOpenAI(
            model=self.llm_model,
            temperature=0.1,
            openai_api_key=api_key
        )
        
        # Промпт для ранжирования новостей
        self.ranking_prompt = PromptTemplate(
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
        self.ranking_chain = (
            RunnablePassthrough()
            | self.ranking_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def create_embeddings(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Создает embeddings для новостей
        
        Args:
            news_items: Список новостей
            
        Returns:
            Список новостей с embeddings
        """
        self.logger.info(f"Creating embeddings for {len(news_items)} news items")
        
        # Получаем тексты для embedding
        texts = [item.get_content_for_embedding() for item in news_items]
        
        try:
            # Создаем embeddings через LangChain
            embeddings = self.embeddings.embed_documents(texts)
            
            # Присваиваем embeddings новостям
            for item, embedding in zip(news_items, embeddings):
                item.embedding = np.array(embedding, dtype=np.float32)
            
            self.logger.info(f"Successfully created embeddings for {len(news_items)} items")
            return news_items
            
        except Exception as e:
            self.logger.error(f"Failed to create embeddings: {str(e)}")
            raise
    
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
        Ранжирование новостей по важности
        
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
        
        try:
            # Вызываем LLM для ранжирования
            result = self.ranking_chain.invoke({
                "news_items": news_text,
                "criteria": criteria
            })
            
            # Парсим результат
            rankings_data = json.loads(result.strip())
            url_to_score = {item["url"]: item["score"] for item in rankings_data["rankings"]}
            
            # Присваиваем оценки
            for item in news_items:
                item.relevance_score = url_to_score.get(item.url, 5.0)  # Дефолтная оценка
            
            # Сортируем по убыванию оценки
            ranked_items = sorted(news_items, key=lambda x: x.relevance_score, reverse=True)
            
            self.logger.info(f"Successfully ranked {len(ranked_items)} news items")
            return ranked_items
            
        except Exception as e:
            self.logger.error(f"Failed to rank news: {str(e)}")
            # Возвращаем исходный список с дефолтными оценками
            for item in news_items:
                item.relevance_score = 5.0
            return news_items
    
    def process_news(self, 
                    news_items: List[NewsItem], 
                    ranking_criteria: str = None) -> List[NewsItem]:
        """
        Полная обработка новостей: embeddings -> дедупликация -> ранжирование
        
        Args:
            news_items: Список новостей
            ranking_criteria: Критерии ранжирования
            
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
        
        # Шаг 1: Создание embeddings
        news_items = self.create_embeddings(news_items)
        
        # Шаг 2: Дедупликация
        unique_items = self.deduplicate_news(news_items)
        
        # Шаг 3: Ранжирование
        ranked_items = self.rank_news(unique_items, ranking_criteria)
        
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