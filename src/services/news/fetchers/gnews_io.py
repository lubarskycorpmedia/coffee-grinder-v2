# src/services/news/fetchers/gnews_io.py

import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseFetcher, NewsAPIError
from src.logger import setup_logger


class GNewsIOFetcher(BaseFetcher):
    """Fetcher для GNews API с поддержкой всех эндпоинтов"""
    
    PROVIDER_NAME = "gnews_io"
    
    def __init__(self, provider_settings):
        """
        Инициализация fetcher'а
        
        Args:
            provider_settings: Настройки провайдера GNewsIOSettings
        """
        super().__init__(provider_settings)
        
        # Получаем специфичные настройки для GNews
        self.api_key = provider_settings.api_key
        self.base_url = provider_settings.base_url
        self.page_size = provider_settings.page_size
        
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
        
        # Добавляем apikey к параметрам
        params["apikey"] = self.api_key
        
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
            
            # Проверяем на ошибки API (GNews возвращает ошибки в разных форматах)
            if "error" in data:
                error_msg = data["error"]
                self.logger.error(f"GNews API error: {error_msg}")
                return {"error": NewsAPIError(error_msg, response.status_code, 1)}
            
            # Проверяем статус ответа
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {data}"
                self.logger.error(error_msg)
                return {"error": NewsAPIError(error_msg, response.status_code, 1)}
            
            self.logger.debug(f"Request successful, got {len(data.get('articles', []))} items")
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
            result = self._make_request("search", {"q": "test", "max": 1})
            
            if "error" in result:
                return {
                    "status": "unhealthy",
                    "provider": self.PROVIDER_NAME,
                    "message": f"API error: {result['error']}"
                }
            
            return {
                "status": "healthy",
                "provider": self.PROVIDER_NAME,
                "message": "GNews API is accessible"
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
        categories_path = os.path.join(project_root, 'data', 'gnews_io_categories.json')
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
        languages_path = os.path.join(project_root, 'data', 'gnews_io_languages.json')
        with open(languages_path, 'r') as f:
            languages = json.load(f)
        return languages

    def get_provider_parameters(self) -> Dict[str, Any]:
        """
        Получить параметры провайдера из JSON файла
        
        Returns:
            Dict[str, Any]: Словарь с URL эндпоинта и полями формы
                {
                    "url": "https://gnews.io/api/v4/search",
                    "fields": {
                        "q": "Поисковый запрос",
                        "lang": "Язык"
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
            parameters_path = os.path.join(project_root, 'data', 'gnews_io_parameters.json')
            
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
        
    def get_countries(self) -> List[str]:
        """
        Получить поддерживаемые страны
        
        Returns:
            List[str]: Список 2-буквенных кодов стран
        """
        # Возвращаем основные страны, поддерживаемые GNews
        return [
            "au", "br", "ca", "cn", "eg", "fr", "de", "gr", "hk", "in", "ie", "il",
            "it", "jp", "nl", "no", "pk", "pe", "ph", "pt", "ro", "ru", "sg", "es",
            "se", "ch", "tw", "ua", "gb", "us"
        ]
    
    def _map_category_to_gnews(self, category: Optional[str]) -> Optional[str]:
        """
        Маппинг категории в категорию GNews для top-headlines
        
        Args:
            category: Категория для маппинга
            
        Returns:
            Optional[str]: Категория GNews или None
        """
        if not category:
            return None
            
        # Маппинг категорий в категории GNews
        category_mapping = {
            "general": "general",
            "world": "world",
            "nation": "nation",
            "business": "business",
            "technology": "technology",
            "entertainment": "entertainment",
            "sports": "sports",
            "science": "science",
            "health": "health",
            # Синонимы и альтернативные названия
            "tech": "technology",
            "sport": "sports",
            "finance": "business",
            "politics": "nation",
            "national": "nation",
            "international": "world",
            "global": "world",
            "economy": "business",
            "medical": "health",
            "healthcare": "health"
        }
        
        return category_mapping.get(category.lower())
    
    def fetch_headlines(self, 
                       category: Optional[str] = None,
                       language: Optional[str] = None,
                       country: Optional[str] = None,
                       limit: int = 10) -> Dict[str, Any]:
        """
        Получает топ заголовки по категориям через эндпоинт /top-headlines
        
        Args:
            category: Категория новостей
            language: Язык новостей (опционально)
            country: Страна новостей (опционально)
            limit: Количество новостей (max 100)
            
        Returns:
            Dict с результатами или ошибкой
        """
        params = {
            "max": min(limit, self.page_size)
        }
        
        # Добавляем категорию если указана (только для top-headlines)
        if category:
            mapped_category = self._map_category_to_gnews(category)
            if mapped_category:
                params["category"] = mapped_category
        
        # Добавляем язык если указан
        if language:
            params["lang"] = language
        
        # Добавляем страну если указана
        if country:
            params["country"] = country
            
        return self._make_request("top-headlines", params)
    
    def fetch_top_stories(self, **kwargs) -> Dict[str, Any]:
        """
        Получает топ новости (алиас для fetch_headlines)
        
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            result = self.fetch_headlines(**kwargs)
            return result
        except Exception as e:
            return {"error": NewsAPIError(f"Failed to fetch top stories: {e}")}
    
    def get_sources(self, **kwargs) -> Dict[str, Any]:
        """
        Получает список доступных источников
        
        Note: GNews API не предоставляет отдельный эндпоинт для источников,
        поэтому возвращаем пустой список
        
        Returns:
            Dict с пустым списком источников
        """
        self.logger.warning("GNews API does not provide a sources endpoint")
        return {"sources": []}
    

    
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
            
            # Вызываем _make_request который добавит token
            result = self._make_request(endpoint, params)
            
            # Если есть ошибка, возвращаем как есть
            if "error" in result:
                return result
            
            # Стандартизируем формат каждой статьи
            articles = []
            for article in result.get("articles", []):
                standardized_article = self._standardize_article(article)
                articles.append(standardized_article)
            
            self.logger.info(f"Successfully standardized {len(articles)} articles")
            
            return {
                "articles": articles,
                "meta": {"total": result.get("totalArticles", len(articles))}
            }
            
        except Exception as e:
            error_msg = f"Failed to fetch news: {str(e)}"
            self.logger.error(error_msg)
            return {"error": NewsAPIError(error_msg, None, 1)}
    
    def _standardize_article(self, article: Dict[str, Any], language: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Стандартизация формата статьи GNews под общий формат
        
        Args:
            article: Статья от GNews API
            language: Язык запроса (для заполнения если отсутствует в статье)
            category: Категория запроса (для заполнения если отсутствует в статье)
            
        Returns:
            Dict[str, Any]: Стандартизованная статья
        """
        # Парсим дату публикации
        published_at = None
        if article.get("publishedAt"):
            try:
                # GNews возвращает дату в ISO формате
                published_at = datetime.fromisoformat(
                    article["publishedAt"].replace("Z", "+00:00")
                )
            except ValueError:
                self.logger.warning(f"Failed to parse date: {article.get('publishedAt')}")
        
        # Извлекаем информацию об источнике
        source_info = article.get("source", {})
        source_name = source_info.get("name", "") if isinstance(source_info, dict) else str(source_info)
        source_url = source_info.get("url", "") if isinstance(source_info, dict) else ""
        
        return {
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "content": article.get("content", ""),
            "url": article.get("url", ""),
            "image_url": article.get("image"),
            "published_at": published_at,
            "source": {
                "name": source_name,
                "url": source_url
            },
            "author": None,  # GNews не возвращает автора
            "provider": self.PROVIDER_NAME,
            "language": language,  # GNews не возвращает язык в статьях
            "category": category,  # GNews не возвращает категорию в статьях
            "raw_data": article  # Сохраняем оригинальные данные
        } 