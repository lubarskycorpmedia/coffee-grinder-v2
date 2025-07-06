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
    
    def __init__(self, api_token: str, max_retries: int = 3, backoff_factor: float = 2.0):
        """
        Инициализация fetcher'а
        
        Args:
            api_token: API токен для thenewsapi.com
            max_retries: Максимальное количество попыток при ошибках
            backoff_factor: Коэффициент для экспоненциального backoff
        """
        self.api_token = api_token
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.base_url = "https://api.thenewsapi.com/v1"
        self._session = None
        self._logger = None
    
    @property
    def session(self):
        """Ленивое создание сессии"""
        if self._session is None:
            self._session = self._create_session()
        return self._session
    
    @property
    def logger(self):
        """Ленивое создание логгера"""
        if self._logger is None:
            self._logger = setup_logger(__name__)
        return self._logger
    
    def _create_session(self) -> requests.Session:
        """Создает сессию с настройками retry"""
        session = requests.Session()
        
        # Отключаем автоматический retry - делаем вручную
        retry_strategy = Retry(
            total=0,
            backoff_factor=0,
            status_forcelist=[]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _exponential_backoff(self, attempt: int) -> float:
        """Вычисляет время задержки для экспоненциального backoff"""
        base_delay = 1.0  # Базовая задержка в секундах
        max_delay = 60.0  # Максимальная задержка
        
        delay = base_delay * (self.backoff_factor ** attempt) + random.uniform(0, 1)
        return min(delay, max_delay)
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет HTTP запрос с retry логикой"""
        url = f"{self.base_url}/{endpoint}"
        
        # Добавляем API токен в параметры
        params["api_token"] = self.api_token
        
        headers = {
            "User-Agent": "coffee-grinder-news-service/1.0",
            "Accept": "application/json"
        }
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Making request to {url}, attempt {attempt + 1}/{self.max_retries}")
                
                response = self.session.get(url, params=params, headers=headers, timeout=30)
                
                # Проверяем статус код
                if response.status_code == 200:
                    data = response.json()
                    
                    # Проверяем наличие ошибки в ответе
                    if "error" in data:
                        error_info = data["error"]
                        error_msg = error_info.get("message", "Unknown API error")
                        self.logger.error(f"API error: {error_msg}")
                        last_error = NewsAPIError(error_msg, response.status_code, attempt + 1)
                        return {"error": last_error}
                    
                    # Успешный ответ
                    total_results = len(data.get("data", []))
                    self.logger.info(f"Successfully fetched {total_results} items")
                    return data
                    
                elif response.status_code == 429:
                    # Rate limit exceeded
                    self.logger.warning(f"Rate limit exceeded (429), attempt {attempt + 1}/{self.max_retries}")
                    last_error = NewsAPIError("Rate limit exceeded", 429, attempt + 1)
                    
                    # Если это не последняя попытка, ждем
                    if attempt < self.max_retries - 1:
                        delay = self._exponential_backoff(attempt)
                        self.logger.info(f"Waiting {delay:.2f} seconds before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        # Последняя попытка - возвращаем ошибку
                        self.logger.error(f"Rate limit exceeded after {self.max_retries} attempts")
                        return {"error": last_error}
                
                else:
                    # Другие HTTP ошибки
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg = error_data["error"].get("message", f"HTTP {response.status_code}")
                        else:
                            error_msg = f"HTTP {response.status_code}: {response.text}"
                    except:
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                    
                    self.logger.error(error_msg)
                    last_error = NewsAPIError(error_msg, response.status_code, attempt + 1)
                    
                    # Для серверных ошибок (5xx) пытаемся повторить
                    if 500 <= response.status_code < 600 and attempt < self.max_retries - 1:
                        delay = self._exponential_backoff(attempt)
                        self.logger.info(f"Server error, waiting {delay:.2f} seconds before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        return {"error": last_error}
                        
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed: {str(e)}"
                self.logger.error(error_msg)
                last_error = NewsAPIError(error_msg, None, attempt + 1)
                
                # Для сетевых ошибок пытаемся повторить
                if attempt < self.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    self.logger.info(f"Network error, waiting {delay:.2f} seconds before retry...")
                    time.sleep(delay)
                    continue
                else:
                    return {"error": last_error}
        
        # Если дошли сюда, значит все попытки исчерпаны
        return {"error": last_error}
    
    def fetch_headlines(self, 
                       locale: Optional[str] = "us",
                       language: Optional[str] = "en",
                       domains: Optional[str] = None,
                       exclude_domains: Optional[str] = None,
                       source_ids: Optional[str] = None,
                       exclude_source_ids: Optional[str] = None,
                       published_on: Optional[str] = None,
                       headlines_per_category: int = 6,
                       include_similar: bool = True) -> Dict[str, Any]:
        """
        Получает заголовки новостей по категориям
        
        Args:
            locale: Коды стран через запятую (us, ca, etc.)
            language: Коды языков через запятую (en, es, etc.)
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
            "headlines_per_category": min(headlines_per_category, 10),
            "include_similar": str(include_similar).lower()
        }
        
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
            locale: Коды стран через запятую
            language: Коды языков через запятую
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
                         locale: Optional[str] = "us",
                         language: Optional[str] = "en",
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
            locale: Коды стран через запятую
            language: Коды языков через запятую
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
            locale: Коды стран через запятую
            language: Коды языков через запятую
            categories: Категории для фильтрации
            
        Returns:
            Dict с результатами или ошибкой
        """
        params = {}
        
        if locale:
            params["locale"] = locale
        if language:
            params["language"] = language
        if categories:
            params["categories"] = categories
            
        return self._make_request("news/sources", params)
    
    def fetch_recent_tech_news(self, days_back: int = 1) -> Dict[str, Any]:
        """
        Получает последние технологические новости за указанное количество дней
        
        Args:
            days_back: Количество дней назад
            
        Returns:
            Dict с результатами или ошибкой
        """
        published_after = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        return self.fetch_all_news(
            search="technology + (AI | artificial intelligence | machine learning | startup)",
            language="en",
            categories="tech,business",
            published_after=published_after,
            sort="relevance_score",
            sort_order="desc",
            limit=100
        )
    
    def fetch_news(self, 
                   query: Optional[str] = None,
                   category: Optional[str] = None,
                   language: str = "en",
                   limit: int = 50,
                   **kwargs) -> Dict[str, Any]:
        """
        Универсальный метод для получения новостей
        Адаптер между NewsProcessor и fetch_all_news
        
        Args:
            query: Поисковый запрос
            category: Категория новостей (будет преобразована в categories)
            language: Язык новостей (по умолчанию русский)
            limit: Максимальное количество новостей
            **kwargs: Дополнительные параметры для fetch_all_news
            
        Returns:
            Dict в стандартном формате с полем 'articles'
        """
        try:
            # Вчерашняя дата для published_after
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Подготавливаем параметры для fetch_all_news с фиксированными значениями
            params = {
                "language": language,
                "limit": min(limit, 100),
                "sort": "relevance_score",
                "sort_order": "desc",
                "categories": "general,politics,tech,business",
                "published_after": yesterday
            }
            
            # Добавляем поисковый запрос если есть
            if query:
                params["search"] = query
            
            # Добавляем категорию если есть (перезапишет categories по умолчанию)
            if category:
                params["categories"] = category
            
            # Добавляем дополнительные параметры (могут перезаписать defaults)
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
                    "language": article.get("language", language)
                }
                articles.append(standardized_article)
            
            self.logger.info(f"Successfully standardized {len(articles)} articles")
            
            return {
                "articles": articles,
                "meta": result.get("meta", {
                    "total": len(articles),
                    "limit": limit,
                    "language": language
                })
            }
            
        except Exception as e:
            error_msg = f"Failed to fetch news: {str(e)}"
            self.logger.error(error_msg)
            error = NewsAPIError(error_msg, None, 1)
            return {"error": error}
    
    def _extract_category(self, article: Dict[str, Any], requested_category: Optional[str]) -> str:
        """
        Извлекает категорию из статьи
        
        Args:
            article: Статья из API
            requested_category: Запрошенная категория
            
        Returns:
            Строка с категорией
        """
        # TheNewsAPI возвращает categories как массив
        api_categories = article.get("categories", [])
        
        if api_categories and isinstance(api_categories, list):
            # Берем первую категорию из API
            return api_categories[0]
        elif requested_category:
            # Используем запрошенную категорию
            return requested_category
        else:
            # По умолчанию
            return "general" 