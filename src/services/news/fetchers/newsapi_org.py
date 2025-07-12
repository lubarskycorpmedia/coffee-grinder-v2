# src/services/news/fetchers/newsapi_org.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

from .base import BaseFetcher

logger = logging.getLogger(__name__)


class NewsAPIFetcher(BaseFetcher):
    """Провайдер для получения новостей с NewsAPI.org"""
    
    PROVIDER_NAME = "newsapi"
    
    def __init__(self, provider_settings):
        super().__init__(provider_settings)
        self.client = NewsApiClient(api_key=provider_settings.api_key)
        self.settings = provider_settings
        
    def fetch_headlines(self, **kwargs) -> Dict[str, Any]:
        """
        Получает заголовки новостей (для совместимости с базовым классом)
        
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            articles = self.fetch_news(**kwargs)
            return {"articles": articles}
        except Exception as e:
            from .base import NewsAPIError
            return {"error": NewsAPIError(f"Failed to fetch headlines: {e}")}
    
    def fetch_all_news(self, **kwargs) -> Dict[str, Any]:
        """
        Получает все новости по поиску (для совместимости с базовым классом)
        
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            query = kwargs.get('query', kwargs.get('q', ''))
            if not query:
                return {"articles": []}
            
            articles = self.search_news(query, **kwargs)
            return {"articles": articles}
        except Exception as e:
            from .base import NewsAPIError
            return {"error": NewsAPIError(f"Failed to fetch all news: {e}")}
    
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
    
    def fetch_news(self, 
                   query: Optional[str] = None,
                   category: Optional[str] = None,
                   language: str = "en",
                   limit: int = 50,
                   **kwargs) -> Dict[str, Any]:
        """
        Универсальный метод для получения новостей
        
        Args:
            query: Поисковый запрос
            category: Категория новостей
            language: Язык новостей
            limit: Максимальное количество новостей
            **kwargs: Дополнительные параметры (domains, sources, etc.)
            
        Returns:
            Dict[str, Any]: Результат в стандартном формате с полем "articles"
        """
        try:
            # Если есть параметр domains, используем search_news (эндпоинт /v2/everything)
            if 'domains' in kwargs:
                articles = self.search_news(
                    query=query or "news",
                    language=language,
                    limit=limit,
                    **kwargs
                )
                return {"articles": articles}
            
            # Иначе используем топ заголовки (эндпоинт /v2/top-headlines)
            # Маппинг category в категорию NewsAPI
            api_category = self._map_rubric_to_category(category)
            
            # Получаем топ заголовки
            response = self.client.get_top_headlines(
                category=api_category,
                language=language if language in self.settings.supported_languages else "en",
                country=self.settings.default_country,
                page_size=min(limit, self.settings.page_size)
            )
            
            if response.get('status') != 'ok':
                logger.error(f"NewsAPI error: {response.get('message', 'Unknown error')}")
                from .base import NewsAPIError
                return {"error": NewsAPIError(f"NewsAPI error: {response.get('message', 'Unknown error')}")}
                
            articles = response.get('articles', [])
            standardized_articles = [self._standardize_article(article) for article in articles]
            return {"articles": standardized_articles}
            
        except NewsAPIException as e:
            logger.error(f"NewsAPI exception: {e}")
            from .base import NewsAPIError
            return {"error": NewsAPIError(f"NewsAPI exception: {e}")}
        except Exception as e:
            logger.error(f"Unexpected error in NewsAPI fetcher: {e}")
            from .base import NewsAPIError
            return {"error": NewsAPIError(f"Unexpected error in NewsAPI fetcher: {e}")}
    
    def search_news(self, 
                    query: str,
                    language: str = "en",
                    limit: int = 100,
                    from_date: Optional[datetime] = None,
                    to_date: Optional[datetime] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """
        Поиск новостей по запросу
        
        Args:
            query: Поисковый запрос
            language: Язык новостей
            limit: Максимальное количество новостей
            from_date: Дата начала поиска
            to_date: Дата окончания поиска
            **kwargs: Дополнительные параметры
            
        Returns:
            List[Dict[str, Any]]: Список новостей в стандартизованном формате
        """
        try:
            # Подготавливаем параметры для поиска
            params = {
                'q': query,
                'language': language if language in self.settings.supported_languages else "en",
                'page_size': min(limit, self.settings.page_size),
                'sort_by': kwargs.get('sort_by', 'publishedAt')
            }
            
            # Добавляем даты если указаны
            if from_date:
                params['from_param'] = from_date.strftime('%Y-%m-%d')
            if to_date:
                params['to'] = to_date.strftime('%Y-%m-%d')
                
            # Добавляем источники если указаны
            if 'sources' in kwargs:
                params['sources'] = kwargs['sources']
            
            # Добавляем домены если указаны
            if 'domains' in kwargs:
                params['domains'] = kwargs['domains']
            
            response = self.client.get_everything(**params)
            
            if response.get('status') != 'ok':
                logger.error(f"NewsAPI search error: {response.get('message', 'Unknown error')}")
                return []
                
            articles = response.get('articles', [])
            return [self._standardize_article(article) for article in articles]
            
        except NewsAPIException as e:
            logger.error(f"NewsAPI search exception: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in NewsAPI search: {e}")
            return []
    
    def get_sources(self, 
                    language: str = "en",
                    category: Optional[str] = None,
                    country: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить список доступных источников
        
        Args:
            language: Язык источников
            category: Категория источников
            country: Страна источников
            
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            params = {}
            
            if language in self.settings.supported_languages:
                params['language'] = language
            if category and category in self.settings.supported_categories:
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
    
    def get_categories(self) -> List[str]:
        """
        Получить список поддерживаемых категорий
        
        Returns:
            List[str]: Список категорий
        """
        return self.settings.supported_categories.copy()
    
    def get_languages(self) -> List[str]:
        """
        Получить список поддерживаемых языков
        
        Returns:
            List[str]: Список языков
        """
        return self.settings.supported_languages.copy()
    
    def check_health(self) -> Dict[str, Any]:
        """
        Проверить состояние провайдера
        
        Returns:
            Dict[str, Any]: Статус провайдера
        """
        try:
            # Делаем простой запрос для проверки работоспособности
            response = self.client.get_sources()
            
            if response.get('status') == 'ok':
                return {
                    'status': 'healthy',
                    'provider': self.PROVIDER_NAME,
                    'message': 'NewsAPI is accessible'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'provider': self.PROVIDER_NAME,
                    'message': f"NewsAPI error: {response.get('message', 'Unknown error')}"
                }
                
        except NewsAPIException as e:
            return {
                'status': 'unhealthy',
                'provider': self.PROVIDER_NAME,
                'message': f"NewsAPI exception: {e}"
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'provider': self.PROVIDER_NAME,
                'message': f"Unexpected error: {e}"
            }
    
    def _map_rubric_to_category(self, rubric: Optional[str]) -> Optional[str]:
        """
        Маппинг рубрики в категорию NewsAPI
        
        Args:
            rubric: Рубрика из нашей системы
            
        Returns:
            Optional[str]: Категория NewsAPI или None
        """
        if not rubric:
            return None
            
        # Маппинг наших рубрик в категории NewsAPI
        rubric_mapping = {
            'business': 'business',
            'entertainment': 'entertainment', 
            'general': 'general',
            'health': 'health',
            'science': 'science',
            'sports': 'sports',
            'technology': 'technology'
        }
        
        # Пытаемся найти прямое соответствие
        if rubric.lower() in rubric_mapping:
            return rubric_mapping[rubric.lower()]
            
        # Если прямого соответствия нет, возвращаем general
        return 'general'
    
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
            'language': 'en',  # NewsAPI не всегда возвращает язык
            'category': None,  # NewsAPI не возвращает категорию в статьях
            'raw_data': article  # Сохраняем оригинальные данные
        }
    
    def _standardize_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Стандартизация формата источника NewsAPI
        
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
            'provider': self.PROVIDER_NAME
        } 