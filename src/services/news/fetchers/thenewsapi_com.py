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
    
    PROVIDER_NAME = "thenewsapi_com"
    
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
        import json
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
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
        import json
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        languages_path = os.path.join(project_root, 'data', 'thenewsapi_com_languages.json')
        with open(languages_path, 'r') as f:
            languages = json.load(f)
        return languages

    def get_provider_parameters(self) -> Dict[str, Any]:
        """
        Получить параметры провайдера из JSON файла
        
        Returns:
            Dict[str, Any]: Словарь с URL эндпоинта и полями формы
                {
                    "url": "https://api.thenewsapi.com/v1/news/top",
                    "fields": {
                        "search": "Поисковый запрос",
                        "categories": "Категории"
                    }
                }
            
        Raises:
            Exception: При ошибке чтения или парсинга JSON файла
        """
        import os
        import json
        
        try:
            # Путь к JSON файлу параметров
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            parameters_path = os.path.join(project_root, 'data', 'thenewsapi_com_parameters.json')
            
            # Читаем JSON файл
            with open(parameters_path, 'r', encoding='utf-8') as f:
                parameters_data = json.load(f)
            
            # Ищем первый эндпоинт с "use": "true"
            endpoints = parameters_data.get('endpoints', {})
            first_active_endpoint = None
            
            for endpoint_name, endpoint_data in endpoints.items():
                if endpoint_data.get('use') == 'true':
                    first_active_endpoint = endpoint_data
                    break
            
            if not first_active_endpoint:
                raise Exception("No active endpoint found with 'use': 'true'")
            
            # Получаем URL эндпоинта
            endpoint_url = first_active_endpoint.get('url', '')
            
            # Извлекаем параметры с "use": "true"
            parameters = first_active_endpoint.get('parameters', {})
            active_fields = {}
            
            for param_name, param_data in parameters.items():
                if param_data.get('use') == 'true':
                    # Используем label, если пустое - то ключ параметра
                    label = param_data.get('label', '').strip()
                    if not label:
                        label = param_name
                    active_fields[param_name] = label
            
            return {
                "url": endpoint_url,
                "fields": active_fields
            }
            
        except FileNotFoundError as e:
            raise Exception(f"Parameters file not found: {parameters_path}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in parameters file: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Error reading provider parameters: {str(e)}") from e
        
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
    

    
    def fetch_news(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Универсальный метод для получения новостей по URL и параметрам
        
        Args:
            url: Полный URL эндпоинта API
            params: Параметры запроса из config
            
        Returns:
            Dict в стандартном формате с полем 'articles'
        """
        try:
            # Извлекаем endpoint из URL (убираем base_url)
            endpoint = url.replace(self.base_url + "/", "")
            
            self.logger.debug(f"Making request to endpoint: {endpoint} with params: {params}")
            
            # Вызываем _make_request который добавит api_token
            result = self._make_request(endpoint, params)
            
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
                    "category": article.get("categories", [None])[0] if article.get("categories") else None,
                    "language": article.get("language", ""),
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
            
            return {
                "articles": articles,
                "meta": result.get("meta", {"total": len(articles)})
            }
            
        except Exception as e:
            error_msg = f"Failed to fetch news: {str(e)}"
            self.logger.error(error_msg)
            return {"error": NewsAPIError(error_msg, None, 1)}
    
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