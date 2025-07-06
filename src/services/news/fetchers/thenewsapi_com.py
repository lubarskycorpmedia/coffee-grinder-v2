# src/services/news/fetchers/thenewsapi_com.py

import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseFetcher, NewsAPIError
from ....config import get_settings
from ....logger import setup_logger


class TheNewsAPIFetcher(BaseFetcher):
    """Fetcher для thenewsapi.com с поддержкой всех эндпоинтов"""
    
    def __init__(self):
        self._settings = None
        self._logger = None
        self.base_url = "https://api.thenewsapi.com/v1"
        self._session = None
    
    @property
    def settings(self):
        """Ленивое создание настроек"""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings
    
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
        
        delay = base_delay * (self.settings.BACKOFF_FACTOR ** attempt) + random.uniform(0, 1)
        return min(delay, max_delay)
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет HTTP запрос с retry логикой"""
        url = f"{self.base_url}/{endpoint}"
        
        # Добавляем API токен в параметры
        params["api_token"] = self.settings.THENEWSAPI_API_TOKEN
        
        headers = {
            "User-Agent": "coffee-grinder-news-service/1.0",
            "Accept": "application/json"
        }
        
        last_error = None
        
        for attempt in range(self.settings.MAX_RETRIES):
            try:
                # Маскируем API токен для логирования
                safe_params = params.copy()
                if 'api_token' in safe_params:
                    token = safe_params['api_token']
                    safe_params['api_token'] = f"{token[:8]}...{token[-4:]}" if len(token) > 12 else "***"
                
                # Логируем полный URL запроса
                query_string = "&".join([f"{k}={v}" for k, v in safe_params.items()])
                full_url = f"{url}?{query_string}"
                
                self.logger.info(f"🌐 GET {full_url}")
                self.logger.info(f"📤 Attempt {attempt + 1}/{self.settings.MAX_RETRIES}")
                
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                
                # Логируем детали ответа
                self.logger.info(f"📥 Response: {response.status_code} {response.reason}")
                self.logger.info(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
                self.logger.info(f"📊 Content-Length: {response.headers.get('content-length', 'N/A')} bytes")
                
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
                    self.logger.warning(f"Rate limit exceeded (429), attempt {attempt + 1}/{self.settings.MAX_RETRIES}")
                    last_error = NewsAPIError("Rate limit exceeded", 429, attempt + 1)
                    
                    # Если это не последняя попытка, ждем
                    if attempt < self.settings.MAX_RETRIES - 1:
                        delay = self._exponential_backoff(attempt)
                        self.logger.info(f"Waiting {delay:.2f} seconds before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        # Последняя попытка - возвращаем ошибку
                        self.logger.error(f"Rate limit exceeded after {self.settings.MAX_RETRIES} attempts")
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
                    if 500 <= response.status_code < 600 and attempt < self.settings.MAX_RETRIES - 1:
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
                if attempt < self.settings.MAX_RETRIES - 1:
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