# src/services/news/fetchers/newsapi_org.py

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from urllib.parse import urlencode
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

from .base import BaseFetcher, NewsAPIError
from src.logger import setup_logger

logger = setup_logger(__name__)


class NewsAPIFetcher(BaseFetcher):
    """Fetcher для NewsAPI.org с полной поддержкой всех эндпоинтов"""
    
    PROVIDER_NAME = "newsapi_org"
    
    def __init__(self, provider_settings):
        """
        Инициализация fetcher'а
        
        Args:
            provider_settings: Настройки провайдера NewsAPISettings
        """
        super().__init__(provider_settings)
        
        # Сохраняем настройки для совместимости с тестами
        self.settings = provider_settings
        
        # Получаем настройки
        self.api_key = provider_settings.api_key
        self.base_url = provider_settings.base_url
        self.page_size = provider_settings.page_size
        
        # Инициализируем клиент
        self.client = NewsApiClient(api_key=self.api_key)
        
        # Инициализируем логгер
        self.logger = setup_logger(__name__)
    
    def _log_api_request(self, endpoint: str, params: Dict[str, Any]) -> None:
        """Логирует полный URL запроса к NewsAPI с замаскированным API ключом"""
        # Копируем параметры и маскируем API ключ
        masked_params = params.copy()
        masked_params['apiKey'] = 'xxx'
        
        # Формируем полный URL (base_url уже содержит /v2)
        url = f"{self.base_url}/{endpoint}"
        masked_url = f"{url}?{urlencode(masked_params)}"
        
        self.logger.info(f"🌐 API Request: @{masked_url}")
    
    def fetch_headlines(self, **kwargs) -> Dict[str, Any]:
        """
        Получает топ заголовки (для совместимости с базовым классом)
        
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            articles = self.fetch_news(**kwargs)
            return {"articles": articles}
        except Exception as e:
            from .base import NewsAPIError
            return {"error": NewsAPIError(f"Failed to fetch headlines: {e}")}
    
    def fetch_top_stories(self, **kwargs) -> Dict[str, Any]:
        """
        Получает топ новости (для совместимости с базовым классом)
        
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            articles = self.fetch_news(**kwargs)
            return {"articles": articles}
        except Exception as e:
            from .base import NewsAPIError
            return {"error": NewsAPIError(f"Failed to fetch top stories: {e}")}
    
    def fetch_news(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Унифицированный метод для получения новостей (новый интерфейс)
        
        Args:
            url: URL эндпоинта (используется для определения метода API)
            params: Параметры запроса в формате NewsAPI
            
        Returns:
            Dict[str, Any]: Результат в стандартном формате {"articles": [...], "meta": {...}}
        """
        try:
            self.logger.info(f"NewsAPI fetch_news: {len(params)} параметров")
            self.logger.debug(f"NewsAPI параметры: {params}")
            
            # Определяем метод API по URL
            if "top-headlines" in url:
                api_method = "get_top_headlines"
                response = self.client.get_top_headlines(**params)
            elif "everything" in url:
                api_method = "get_everything" 
                response = self.client.get_everything(**params)
            elif "sources" in url:
                api_method = "get_sources"
                response = self.client.get_sources(**params)
                # Для sources возвращаем sources, а не articles
                if response.get('status') == 'ok':
                    sources = response.get('sources', [])
                    standardized_sources = [self._standardize_source(source) for source in sources]
                    meta = {
                        "provider": self.PROVIDER_NAME,
                        "found": len(standardized_sources),
                        "url": url,
                        "params": params,
                        "method": api_method
                    }
                    return {
                        "sources": standardized_sources,
                        "meta": meta
                    }
            else:
                # По умолчанию используем everything
                api_method = "get_everything"
                response = self.client.get_everything(**params)
            
            if response.get('status') != 'ok':
                error_msg = f"NewsAPI error: {response.get('message', 'Unknown error')}"
                self.logger.error(error_msg)
                return {"error": NewsAPIError(error_msg)}
                
            articles = response.get('articles', [])
            standardized_articles = [self._standardize_article(article) for article in articles]
            
            # Добавляем метаинформацию
            meta = {
                "provider": self.PROVIDER_NAME,
                "found": len(standardized_articles),
                "url": url,
                "params": params,
                "method": api_method
            }
            
            self.logger.info(f"NewsAPI fetch_news ({api_method}): получено {len(standardized_articles)} статей")
            
            return {
                "articles": standardized_articles,
                "meta": meta
            }
            
        except NewsAPIException as e:
            error_msg = f"NewsAPI fetch exception: {e}"
            self.logger.error(error_msg)
            return {"error": NewsAPIError(error_msg)}
        except Exception as e:
            error_msg = f"Unexpected error in NewsAPI fetch: {e}"
            self.logger.error(error_msg)
            return {"error": NewsAPIError(error_msg)}
    

    
    def get_sources(self, 
                    language: Optional[str] = None,
                    category: Optional[str] = None,
                    country: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить список доступных источников
        
        Args:
            language: Язык источников (опционально)
            category: Категория источников (опционально)
            country: Страна источников (опционально)
            
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            params = {}
            
            # Добавляем параметры только если они указаны
            if language:
                params['language'] = language
            if category:
                params['category'] = category
            if country:
                params['country'] = country
                
            response = self.client.get_sources(**params)
            
            if response.get('status') != 'ok':
                logger.error(f"NewsAPI sources error: {response.get('message', 'Unknown error')}")
                return {"sources": []}
                
            sources = response.get('sources', [])
            standardized_sources = [self._standardize_source(source) for source in sources]
            return {"sources": standardized_sources}
            
        except NewsAPIException as e:
            logger.error(f"NewsAPI sources exception: {e}")
            from .base import NewsAPIError
            return {"error": NewsAPIError(f"NewsAPI sources exception: {e}")}
        except Exception as e:
            logger.error(f"Unexpected error in NewsAPI get_sources: {e}")
            from .base import NewsAPIError
            return {"error": NewsAPIError(f"Unexpected error in NewsAPI get_sources: {e}")}
    
    def check_health(self) -> Dict[str, Any]:
        """
        Проверка состояния провайдера
        
        Returns:
            Dict[str, Any]: Результат проверки
        """
        try:
            # Делаем минимальный запрос для проверки доступности API
            response = self.client.get_sources()
            
            if response.get('status') == 'ok':
                return {
                    "status": "healthy",
                    "provider": self.PROVIDER_NAME,
                    "message": "NewsAPI is accessible"
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": self.PROVIDER_NAME,
                    "message": f"NewsAPI error: {response.get('message', 'Unknown error')}"
                }
                
        except NewsAPIException as e:
            return {
                "status": "unhealthy",
                "provider": self.PROVIDER_NAME,
                "message": f"NewsAPI exception: {e}"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.PROVIDER_NAME,
                "message": f"Unexpected error: {e}"
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
        categories_path = os.path.join(project_root, 'data', 'newsapi_org_categories.json')
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
        languages_path = os.path.join(project_root, 'data', 'newsapi_org_languages.json')
        with open(languages_path, 'r') as f:
            languages = json.load(f)
        return languages

    def get_provider_parameters(self) -> Dict[str, Any]:
        """
        Получить параметры провайдера из JSON файла
        
        Returns:
            Dict[str, Any]: Словарь с URL эндпоинта и полями формы
                {
                    "url": "https://newsapi.org/v2/everything",
                    "fields": {
                        "q": "Поисковый запрос",
                        "domains": "Домены"
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
            parameters_path = os.path.join(project_root, 'data', 'newsapi_org_parameters.json')
            
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
    
    def _map_rubric_to_category(self, rubric: Optional[str]) -> Optional[str]:
        """
        Маппинг рубрики в категорию NewsAPI
        
        Args:
            rubric: Рубрика для маппинга
            
        Returns:
            Optional[str]: Категория NewsAPI или None
        """
        if not rubric:
            return None
            
        # Маппинг рубрик в категории NewsAPI
        rubric_mapping = {
            "business": "business",
            "entertainment": "entertainment", 
            "general": "general",
            "health": "health",
            "science": "science",
            "sports": "sports",
            "technology": "technology",
            "tech": "technology",
            "sport": "sports",
            "finance": "business",
            "politics": "general",
            "world": "general",
            "national": "general",
            "local": "general"
        }
        
        return rubric_mapping.get(rubric.lower())
    
    def _standardize_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Стандартизация формата статьи NewsAPI под общий формат
        
        Args:
            article: Статья от NewsAPI
            
        Returns:
            Dict[str, Any]: Стандартизованная статья
        """
        # Парсим дату публикации
        published_at = None
        if article.get('publishedAt'):
            try:
                published_at = datetime.fromisoformat(
                    article['publishedAt'].replace('Z', '+00:00')
                )
            except ValueError:
                logger.warning(f"Failed to parse date: {article.get('publishedAt')}")
        
        return {
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'content': article.get('content', ''),
            'url': article.get('url', ''),
            'image_url': article.get('urlToImage'),
            'published_at': published_at,
            'source': {
                'name': article.get('source', {}).get('name', ''),
                'id': article.get('source', {}).get('id', '')
            },
            'author': article.get('author', ''),
            'provider': self.PROVIDER_NAME,
            'language': None,  # NewsAPI не всегда возвращает язык
            'category': None,  # NewsAPI не возвращает категорию в статьях
            'raw_data': article  # Сохраняем оригинальные данные
        }
    
    def _standardize_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Стандартизация формата источника NewsAPI под общий формат
        
        Args:
            source: Источник от NewsAPI
            
        Returns:
            Dict[str, Any]: Стандартизованный источник
        """
        return {
            'id': source.get('id', ''),
            'name': source.get('name', ''),
            'description': source.get('description', ''),
            'url': source.get('url', ''),
            'category': source.get('category', ''),
            'language': source.get('language', ''),
            'country': source.get('country', ''),
            'provider': self.PROVIDER_NAME,
            'raw_data': source  # Сохраняем оригинальные данные
        } 