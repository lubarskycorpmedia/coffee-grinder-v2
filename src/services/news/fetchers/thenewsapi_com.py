# src/services/news/fetchers/thenewsapi_com.py

import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseFetcher, NewsAPIError
from src.logger import setup_logger


class TheNewsAPIFetcher(BaseFetcher):
    """Fetcher для thenewsapi.com с поддержкой всех эндпоинтов"""
    
    PROVIDER_NAME = "thenewsapi"
    
    def __init__(self, provider_settings):
        """
        Инициализация fetcher'а
        
        Args:
            provider_settings: Настройки провайдера TheNewsAPISettings
        """
        super().__init__(provider_settings)
        
        # Получаем специфичные настройки для TheNewsAPI
        self.api_token = provider_settings.api_token
        self.base_url = provider_settings.base_url
        self.headlines_per_category = provider_settings.headlines_per_category
        
        # Инициализируем сессию и логгер лениво
        self._session = None
        self._logger = None
    
    @property
    def session(self):
        """Ленивая инициализация HTTP сессии"""
        if self._session is None:
            self._session = requests.Session()
            
            # Настройка retry стратегии
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
            
            # Настройка заголовков
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_token}",
                "User-Agent": "CoffeeGrinder/1.0"
            })
        
        return self._session
    
    @property
    def logger(self):
        """Ленивая инициализация логгера"""
        if self._logger is None:
            self._logger = setup_logger(__name__)
        return self._logger
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполняет HTTP запрос к API используя общую логику ретраев из базового класса
        
        Args:
            endpoint: Эндпоинт API
            params: Параметры запроса
            
        Returns:
            Dict с результатом или ошибкой
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Используем общий метод из базового класса
        result = self._make_request_with_retries(
            session=self.session,
            url=url,
            params=params,
            timeout=30
        )
        
        # Если есть ошибка, возвращаем как есть
        if "error" in result:
            return result
        
        # Если успешно, обрабатываем ответ
        response = result["response"]
        
        try:
            data = response.json()
            
            # Проверяем на ошибки API
            if "error" in data:
                error_msg = data["error"]
                self.logger.error(f"API error: {error_msg}")
                return {"error": NewsAPIError(error_msg, response.status_code, 1)}
            
            self.logger.debug(f"Request successful, got {len(data.get('data', []))} items")
            return data
            
        except Exception as e:
            error_msg = f"Failed to parse JSON response: {str(e)}"
            self.logger.error(error_msg)
            return {"error": NewsAPIError(error_msg, response.status_code, 1)}
    
    def _add_random_delay(self):
        """Добавляет случайную задержку для предотвращения rate limiting"""
        delay = random.uniform(0.1, 0.5)
        time.sleep(delay)
    
    def check_health(self) -> Dict[str, Any]:
        """
        Проверка состояния провайдера
        
        Returns:
            Dict[str, Any]: Результат проверки
        """
        try:
            # Делаем минимальный запрос для проверки доступности API
            result = self._make_request("news/sources", {})
            
            if "error" in result:
                return {
                    "status": "unhealthy",
                    "provider": self.PROVIDER_NAME,
                    "message": f"API error: {result['error']}"
                }
            
            return {
                "status": "healthy",
                "provider": self.PROVIDER_NAME,
                "message": "TheNewsAPI is accessible"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.PROVIDER_NAME,
                "message": f"Health check failed: {str(e)}"
            }
    
    def get_categories(self) -> List[str]:
        """
        Получить поддерживаемые категории
        
        Returns:
            List[str]: Список поддерживаемых категорий
        """
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        categories_path = os.path.join(project_root, 'data', 'thenewsapi_com_categories.json')
        with open(categories_path, 'r') as f:
            categories = json.load(f)
        return categories
    
    def get_languages(self) -> List[str]:
        """
        Получить поддерживаемые языки
        
        Returns:
            List[str]: Список поддерживаемых языков
        """
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        languages_path = os.path.join(project_root, 'data', 'thenewsapi_com_languages.json')
        with open(languages_path, 'r') as f:
            languages = json.load(f)
        return languages
        
    def fetch_headlines(self, 
                       locale: Optional[str] = None,
                       language: Optional[str] = None,
                       domains: Optional[str] = None,
                       exclude_domains: Optional[str] = None,
                       source_ids: Optional[str] = None,
                       exclude_source_ids: Optional[str] = None,
                       published_on: Optional[str] = None,
                       headlines_per_category: Optional[int] = None,
                       include_similar: bool = True) -> Dict[str, Any]:
        """
        Получает заголовки новостей по категориям
        
        Args:
            locale: Коды стран через запятую (опционально)
            language: Коды языков через запятую (опционально)
            domains: Домены для включения
            exclude_domains: Домены для исключения
            source_ids: ID источников для включения
            exclude_source_ids: ID источников для исключения
            published_on: Дата публикации (YYYY-MM-DD)
            headlines_per_category: Количество заголовков на категорию (max 10)
            include_similar: Включать похожие статьи
            
        Returns:
            Dict с результатами или ошибкой
        """
        params = {
            "headlines_per_category": min(headlines_per_category or self.headlines_per_category, 10),
            "include_similar": str(include_similar).lower()
        }
        
        # Добавляем параметры только если они указаны
        if locale:
            params["locale"] = locale
        if language:
            params["language"] = language
        if domains:
            params["domains"] = domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains
        if source_ids:
            params["source_ids"] = source_ids
        if exclude_source_ids:
            params["exclude_source_ids"] = exclude_source_ids
        if published_on:
            params["published_on"] = published_on
            
        return self._make_request("news/headlines", params)
    
    def fetch_all_news(self,
                      search: Optional[str] = None,
                      locale: Optional[str] = None,
                      language: Optional[str] = None,
                      domains: Optional[str] = None,
                      exclude_domains: Optional[str] = None,
                      source_ids: Optional[str] = None,
                      exclude_source_ids: Optional[str] = None,
                      categories: Optional[str] = None,
                      exclude_categories: Optional[str] = None,
                      published_after: Optional[str] = None,
                      published_before: Optional[str] = None,
                      published_on: Optional[str] = None,
                      sort: str = "published_at",
                      sort_order: str = "desc",
                      limit: int = 100,
                      page: int = 1) -> Dict[str, Any]:
        """
        Поиск по всем новостям
        
        Args:
            search: Поисковый запрос с поддержкой операторов (+, -, |, скобки)
            locale: Коды стран через запятую (опционально)
            language: Коды языков через запятую (опционально)
            domains: Домены для включения
            exclude_domains: Домены для исключения
            source_ids: ID источников для включения
            exclude_source_ids: ID источников для исключения
            categories: Категории для включения
            exclude_categories: Категории для исключения
            published_after: Дата начала (YYYY-MM-DD)
            published_before: Дата окончания (YYYY-MM-DD)
            published_on: Конкретная дата (YYYY-MM-DD)
            sort: Сортировка (published_at, relevance_score)
            sort_order: Порядок сортировки (asc, desc)
            limit: Количество результатов (max 100)
            page: Номер страницы
            
        Returns:
            Dict с результатами или ошибкой
        """
        params = {
            "sort": sort,
            "sort_order": sort_order,
            "limit": min(limit, 100),
            "page": page
        }
        
        # Добавляем параметры только если они указаны
        if search:
            params["search"] = search
        if locale:
            params["locale"] = locale
        if language:
            params["language"] = language
        if domains:
            params["domains"] = domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains
        if source_ids:
            params["source_ids"] = source_ids
        if exclude_source_ids:
            params["exclude_source_ids"] = exclude_source_ids
        if categories:
            params["categories"] = categories
        if exclude_categories:
            params["exclude_categories"] = exclude_categories
        if published_after:
            params["published_after"] = published_after
        if published_before:
            params["published_before"] = published_before
        if published_on:
            params["published_on"] = published_on
            
        return self._make_request("news/all", params)
    
    def fetch_top_stories(self,
                         locale: Optional[str] = None,
                         language: Optional[str] = None,
                         domains: Optional[str] = None,
                         exclude_domains: Optional[str] = None,
                         source_ids: Optional[str] = None,
                         exclude_source_ids: Optional[str] = None,
                         categories: Optional[str] = None,
                         exclude_categories: Optional[str] = None,
                         published_after: Optional[str] = None,
                         published_before: Optional[str] = None,
                         published_on: Optional[str] = None,
                         limit: int = 100,
                         page: int = 1) -> Dict[str, Any]:
        """
        Получает топ новости
        
        Args:
            locale: Коды стран через запятую (опционально)
            language: Коды языков через запятую (опционально)
            domains: Домены для включения
            exclude_domains: Домены для исключения
            source_ids: ID источников для включения
            exclude_source_ids: ID источников для исключения
            categories: Категории для включения
            exclude_categories: Категории для исключения
            published_after: Дата начала (YYYY-MM-DD)
            published_before: Дата окончания (YYYY-MM-DD)
            published_on: Конкретная дата (YYYY-MM-DD)
            limit: Количество результатов (max 100)
            page: Номер страницы
            
        Returns:
            Dict с результатами или ошибкой
        """
        params = {
            "limit": min(limit, 100),
            "page": page
        }
        
        # Добавляем параметры только если они указаны
        if locale:
            params["locale"] = locale
        if language:
            params["language"] = language
        if domains:
            params["domains"] = domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains
        if source_ids:
            params["source_ids"] = source_ids
        if exclude_source_ids:
            params["exclude_source_ids"] = exclude_source_ids
        if categories:
            params["categories"] = categories
        if exclude_categories:
            params["exclude_categories"] = exclude_categories
        if published_after:
            params["published_after"] = published_after
        if published_before:
            params["published_before"] = published_before
        if published_on:
            params["published_on"] = published_on
            
        return self._make_request("news/top", params)
    
    def get_sources(self,
                   locale: Optional[str] = None,
                   language: Optional[str] = None,
                   categories: Optional[str] = None) -> Dict[str, Any]:
        """
        Получает список доступных источников
        
        Args:
            locale: Коды стран через запятую (опционально)
            language: Коды языков через запятую (опционально)
            categories: Категории для фильтрации
            
        Returns:
            Dict с результатами или ошибкой
        """
        params = {}
        
        # Добавляем параметры только если они указаны
        if locale:
            params["locale"] = locale
        if language:
            params["language"] = language
        if categories:
            params["categories"] = categories
            
        return self._make_request("news/sources", params)
    
    def search_news(self, 
                    query: str,
                    language: Optional[str] = None,
                    limit: int = 50,
                    **kwargs) -> List[Dict[str, Any]]:
        """
        Поиск новостей по запросу
        
        Args:
            query: Поисковый запрос
            language: Язык новостей (опционально)
            limit: Максимальное количество новостей
            **kwargs: Дополнительные параметры
            
        Returns:
            List[Dict[str, Any]]: Список новостей в стандартизованном формате
        """
        params = {
            "search": query,
            "limit": min(limit, 100),
            "sort": "relevance_score",
            "sort_order": "desc"
        }
        
        # Добавляем язык только если он указан
        if language:
            params["language"] = language
        
        # Добавляем дополнительные параметры
        params.update(kwargs)
        
        result = self.fetch_all_news(**params)
        
        if "error" in result:
            return []
        
        # Стандартизируем формат каждой статьи
        articles = []
        for article in result.get("data", []):
            standardized_article = {
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "published_at": article.get("published_at", ""),
                "source": article.get("source", ""),
                "category": article.get("categories", [None])[0] if article.get("categories") else None,
                "language": article.get("language", language),
                "uuid": article.get("uuid", ""),
                "image_url": article.get("image_url", ""),
                "keywords": article.get("keywords", ""),
                "snippet": article.get("snippet", ""),
                "relevance_score": article.get("relevance_score")
            }
            articles.append(standardized_article)
        
        return articles
    
    def fetch_news(self, 
                   query: Optional[str] = None,
                   category: Optional[str] = None,
                   language: Optional[str] = None,
                   limit: int = 50,
                   **kwargs) -> Dict[str, Any]:
        """
        Универсальный метод для получения новостей
        Адаптер между NewsProcessor и fetch_all_news
        
        Args:
            query: Поисковый запрос
            category: Категория новостей (будет преобразована в categories)
            language: Язык новостей (опционально)
            limit: Максимальное количество новостей
            **kwargs: Дополнительные параметры для fetch_all_news
            
        Returns:
            Dict в стандартном формате с полем 'articles'
        """
        try:
            # Подготавливаем параметры для fetch_all_news
            params = {
                "limit": min(limit, 100),
                "sort": "relevance_score",
                "sort_order": "desc"
            }
            
            # Добавляем язык только если он явно указан
            if language:
                params["language"] = language
            
            # Добавляем поисковый запрос если есть
            if query:
                params["search"] = query
            
            # Добавляем категорию если есть
            if category:
                params["categories"] = category
            
            # Добавляем дополнительные параметры из kwargs
            params.update(kwargs)
            
            self.logger.debug(f"Calling fetch_all_news with params: {params}")
            
            # Вызываем fetch_all_news
            result = self.fetch_all_news(**params)
            
            # Если есть ошибка, возвращаем как есть
            if "error" in result:
                return result
            
            # Преобразуем формат ответа: "data" -> "articles"
            raw_articles = result.get("data", [])
            
            # Стандартизируем формат каждой статьи
            articles = []
            for article in raw_articles:
                standardized_article = {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("published_at", ""),
                    "source": article.get("source", ""),
                    "category": self._extract_category(article, category),
                    "language": article.get("language", language),
                    # Дополнительные поля из API
                    "uuid": article.get("uuid", ""),
                    "image_url": article.get("image_url", ""),
                    "keywords": article.get("keywords", ""),
                    "snippet": article.get("snippet", ""),
                    "relevance_score": article.get("relevance_score"),
                    "categories": article.get("categories", [])
                }
                articles.append(standardized_article)
            
            self.logger.info(f"Successfully standardized {len(articles)} articles")
            
            meta = {
                "total": len(articles),
                "limit": limit
            }
            if language:
                meta["language"] = language
            
            return {
                "articles": articles,
                "meta": result.get("meta", meta)
            }
            
        except Exception as e:
            error_msg = f"Failed to fetch news: {str(e)}"
            self.logger.error(error_msg)
            error = NewsAPIError(error_msg, None, 1)
            return {"error": error}
    
    def _extract_category(self, article: Dict[str, Any], requested_category: Optional[str]) -> Optional[str]:
        """
        Извлекает категорию из статьи
        
        Args:
            article: Статья от API
            requested_category: Запрошенная категория
            
        Returns:
            Optional[str]: Категория статьи
        """
        # Сначала пытаемся взять из categories массива
        categories = article.get("categories", [])
        if categories:
            return categories[0]
        
        # Если нет категорий в статье, возвращаем запрошенную
        return requested_category 