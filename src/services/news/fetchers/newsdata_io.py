# src/services/news/fetchers/newsdata_io.py

from datetime import datetime
from typing import Any, TYPE_CHECKING, Dict
import requests
from urllib.parse import urlencode

from newsdataapi import NewsDataApiClient

from src.logger import setup_logger

from .base import BaseFetcher

if TYPE_CHECKING:
    from src.config import NewsDataIOSettings

logger = setup_logger(__name__)


class NewsDataIOFetcher(BaseFetcher):
    """Fetcher для NewsData.io с полной поддержкой всех эндпоинтов"""

    PROVIDER_NAME = "newsdata_io"

    def __init__(self, provider_settings: 'NewsDataIOSettings') -> None:
        """
        Инициализация fetcher'а

        Args:
            provider_settings: Настройки провайдера NewsDataIOSettings
        """
        super().__init__(provider_settings)

        # Сохраняем настройки для совместимости с тестами
        self.settings = provider_settings

        # Получаем настройки
        self.api_key = provider_settings.api_key
        self.base_url = provider_settings.base_url
        self.page_size = provider_settings.page_size

        # Инициализируем клиент
        self.client = NewsDataApiClient(apikey=self.api_key)

        # Инициализируем логгер
        self.logger = setup_logger(__name__)

    def check_source_by_domain(self, domain: str) -> str:
        """
        Проверяет существование источника по домену через API sources
        
        Args:
            domain: Домен для проверки (например, 'washingtonpost.com')
        
        Returns:
            'да' - если источник найден и активен
            'нет' - если источник не найден или неактивен
            'ошибка_XXX' - если произошла ошибка API
        """
        try:
            # Нормализуем домен
            normalized_domain = self._normalize_domain(domain)
            if not normalized_domain:
                logger.warning(f"Невалидный домен: {domain}")
                return "нет"
            
            # Делаем прямой HTTP запрос к API sources с параметром domainurl
            
            url = "https://newsdata.io/api/1/sources"
            params = {
                'apikey': self.settings.api_key,
                'domainurl': normalized_domain
            }
            
            logger.info(f"Проверяем источник по домену {normalized_domain} в NewsData.io")
            
            # Логируем полный URL с замаскированным API ключом
            masked_params = params.copy()
            masked_params['apikey'] = 'xxx'
            masked_url = f"{url}?{urlencode(masked_params)}"
            logger.info(f"🌐 API Request: @{masked_url}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'success':
                logger.error(f"API вернул неуспешный статус: {data}")
                return "ошибка_api"
            
            results = data.get('results', [])
            
            if not results:
                logger.info(f"Источник с доменом {normalized_domain} не найден в NewsData.io")
                return "нет"
            
            # Проверяем, что найденный источник действительно соответствует запрошенному домену
            for source in results:
                source_url = source.get('url', '')
                source_domain = self._normalize_domain(source_url)
                
                if source_domain == normalized_domain:
                    logger.info(f"Источник {source.get('name')} найден для домена {normalized_domain}")
                    return "да"
            
            logger.info(f"Найденные источники не соответствуют домену {normalized_domain}")
            return "нет"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка HTTP запроса при проверке источника {domain}: {e}")
            return f"ошибка_http"
        except Exception as e:
            logger.error(f"Неожиданная ошибка при проверке источника {domain}: {e}")
            return f"ошибка_неизвестная"
    
    def _normalize_domain(self, domain: str) -> str:
        """
        Нормализует домен для использования в API
        
        Args:
            domain: Исходный домен
            
        Returns:
            str: Нормализованный домен
        """
        if not domain:
            return ""
        
        # Убираем протокол
        domain = domain.replace("https://", "").replace("http://", "")
        
        # Убираем www
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Убираем путь и параметры
        if "/" in domain:
            domain = domain.split("/")[0]
        
        # Убираем порт
        if ":" in domain:
            domain = domain.split(":")[0]
        
        return domain.strip().lower()

    def _call_with_timeout(self, func, *args, **kwargs):
        """
        Вызывает функцию - упрощенная версия без signal
        Библиотека newsdataapi сама имеет встроенные таймауты
        """
        # Убираем signal.SIGALRM так как он не работает в FastAPI/uvicorn потоках
        # Библиотека newsdataapi сама имеет встроенные таймауты
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Преобразуем любые таймауты библиотеки в наш TimeoutError
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                raise TimeoutError(f"Request timed out: {str(e)}")
            raise

    def fetch_headlines(self, **kwargs: Any) -> dict[str, Any]:
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

    def fetch_top_stories(self, **kwargs: Any) -> dict[str, Any]:
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
            url: URL эндпоинта (игнорируется, используется библиотека-клиент)
            params: Параметры запроса в формате NewsData.io
            
        Returns:
            Dict[str, Any]: Результат в стандартном формате {"articles": [...], "meta": {...}}
        """
        try:
            self.logger.info(f"NewsData.io fetch_news: {len(params)} параметров")
            self.logger.debug(f"NewsData.io параметры: {params}")
            
            # Преобразуем типы параметров для библиотеки NewsData.io
            converted_params = self._convert_param_types(params)
            self.logger.debug(f"NewsData.io конвертированные параметры: {converted_params}")
            
            # Выполняем запрос через библиотеку с таймаутом - распаковываем params напрямую
            response = self._call_with_timeout(self.client.news_api, **converted_params)

            if response.get("status") != "success":
                error_msg = f"NewsData.io API error: {response.get('message', 'Unknown error')}"
                self.logger.error(error_msg)
                from .base import NewsAPIError
                return {"error": NewsAPIError(error_msg)}

            articles = response.get("results", [])
            standardized_articles = [
                self._standardize_article(article) for article in articles
            ]
            
            # Добавляем метаинформацию
            meta = {
                "provider": self.PROVIDER_NAME,
                "found": len(standardized_articles),
                "url": url,
                "params": converted_params
            }
            
            self.logger.info(f"NewsData.io fetch_news: получено {len(standardized_articles)} статей")
            
            return {
                "articles": standardized_articles,
                "meta": meta
            }

        except TimeoutError as e:
            error_msg = f"NewsData.io fetch timeout: {e}"
            self.logger.error(error_msg)
            from .base import NewsAPIError
            return {"error": NewsAPIError(error_msg)}
        except Exception as e:
            error_msg = f"NewsData.io fetch exception: {e}"
            self.logger.error(error_msg)
            from .base import NewsAPIError
            return {"error": NewsAPIError(error_msg)}

    def _convert_param_types(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует типы параметров для библиотеки NewsData.io
        
        Основано на сигнатуре NewsDataApiClient.news_api():
        - int: size, max_result, timeframe
        - bool: full_content, image, video, scroll, removeduplicate
        """
        converted_params = params.copy()
        
        # Параметры, которые должны быть int
        int_params = {'size', 'max_result'}
        
        # Параметры, которые должны быть bool  
        bool_params = {'full_content', 'image', 'video', 'scroll', 'removeduplicate'}
        
        # Специальный параметр timeframe (может быть int или str)
        timeframe_param = 'timeframe'
        
        for param_name, param_value in params.items():
            try:
                if param_name in int_params:
                    # Преобразуем в int
                    if isinstance(param_value, str) and param_value.isdigit():
                        converted_params[param_name] = int(param_value)
                        self.logger.debug(f"Converted {param_name}: '{param_value}' → {converted_params[param_name]} (int)")
                    elif isinstance(param_value, (int, float)):
                        converted_params[param_name] = int(param_value)
                
                elif param_name in bool_params:
                    # Преобразуем в bool
                    if isinstance(param_value, str):
                        if param_value.lower() in ('true', '1', 'yes', 'on'):
                            converted_params[param_name] = True
                        elif param_value.lower() in ('false', '0', 'no', 'off'):
                            converted_params[param_name] = False
                        else:
                            self.logger.warning(f"Cannot convert {param_name}='{param_value}' to bool, keeping original")
                        self.logger.debug(f"Converted {param_name}: '{param_value}' → {converted_params[param_name]} (bool)")
                    elif isinstance(param_value, (int, float)):
                        converted_params[param_name] = bool(param_value)
                        self.logger.debug(f"Converted {param_name}: {param_value} → {converted_params[param_name]} (bool)")
                
                elif param_name == timeframe_param:
                    # timeframe может быть int или str, пробуем int если возможно
                    if isinstance(param_value, str) and param_value.isdigit():
                        converted_params[param_name] = int(param_value)
                        self.logger.debug(f"Converted {param_name}: '{param_value}' → {converted_params[param_name]} (int)")
                    # Иначе оставляем как есть (может быть строкой типа "1h", "7d")
                        
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Failed to convert parameter {param_name}='{param_value}': {e}")
                # Оставляем оригинальное значение при ошибке
        
        self.logger.debug(f"Original params: {params}")
        self.logger.debug(f"Converted params: {converted_params}")
        
        return converted_params

    def search_news(
        self,
        query: str,
        language: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Поиск новостей через API

        Args:
            query: Поисковый запрос (обязательный)
            language: Язык новостей (опционально)
            from_date: Дата начала поиска
            to_date: Дата окончания поиска
            limit: Максимальное количество новостей
            **kwargs: Дополнительные параметры (country, domain, etc.)

        Returns:
            List[Dict[str, Any]]: Список стандартизированных статей
        """
        try:
            # Подготавливаем параметры для поиска
            params = {"q": query, "size": min(limit, self.page_size)}

            # Добавляем язык только если он указан
            if language:
                params["language"] = language

            # Добавляем даты если указаны
            if from_date:
                params["from_date"] = from_date.strftime("%Y-%m-%d")
            if to_date:
                params["to_date"] = to_date.strftime("%Y-%m-%d")

            # Добавляем дополнительные параметры
            if "country" in kwargs and kwargs["country"]:
                params["country"] = str(kwargs["country"])
            
            # Обработка доменов: определяем тип (domain vs domainurl)
            domain_value = kwargs.get("domain") or kwargs.get("domains")
            if domain_value:
                domain_str = str(domain_value)
                # Если содержит точки, то это URL домены (domainurl)
                if "." in domain_str:
                    params["domainurl"] = domain_str
                else:
                    # Иначе это имена доменов (domain)
                    params["domain"] = domain_str
            
            if "category" in kwargs and kwargs["category"]:
                params["category"] = str(kwargs["category"])

            response = self._call_with_timeout(self.client.news_api, **params)

            if response.get("status") != "success":
                logger.error(
                    f"NewsData.io search error: {response.get('message', 'Unknown error')}"
                )
                return []

            articles = response.get("results", [])
            return [self._standardize_article(article) for article in articles]

        except TimeoutError as e:
            logger.error(f"NewsData.io search timeout: {e}")
            return []
        except Exception as e:
            logger.error(f"NewsData.io search exception: {e}")
            return []

    def get_sources(self, **kwargs: Any) -> dict[str, Any]:
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
            # Извлекаем параметры из kwargs
            language = kwargs.get("language")
            category = kwargs.get("category")
            country = kwargs.get("country")
            
            params = {}

            # Добавляем параметры только если они указаны
            if language:
                params["language"] = language
            if category:
                params["category"] = category
            if country:
                params["country"] = country
            
            # Примечание: sources_api не поддерживает фильтрацию по доменам
            # в базовых планах NewsData.io, поэтому параметры domain/domains игнорируются

            response = self._call_with_timeout(self.client.sources_api, **params)

            if response.get("status") != "success":
                logger.error(
                    f"NewsData.io sources error: {response.get('message', 'Unknown error')}"
                )
                return {"sources": []}

            sources = response.get("results", [])
            standardized_sources = [
                self._standardize_source(source) for source in sources
            ]
            return {"sources": standardized_sources}

        except TimeoutError as e:
            logger.error(f"NewsData.io sources timeout: {e}")
            from .base import NewsAPIError

            return {"error": NewsAPIError(f"NewsData.io sources timeout: {e}")}
        except Exception as e:
            logger.error(f"NewsData.io sources exception: {e}")
            from .base import NewsAPIError

            return {"error": NewsAPIError(f"NewsData.io sources exception: {e}")}

    def check_health(self) -> dict[str, Any]:
        """
        Проверка состояния провайдера

        Returns:
            Dict[str, Any]: Результат проверки
        """
        try:
            # Делаем минимальный запрос для проверки доступности API
            response = self._call_with_timeout(self.client.sources_api)

            if response.get("status") == "success":
                return {
                    "status": "healthy",
                    "provider": self.PROVIDER_NAME,
                    "message": "NewsData.io is accessible",
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": self.PROVIDER_NAME,
                    "message": f"NewsData.io error: {response.get('message', 'Unknown error')}",
                }

        except TimeoutError as e:
            return {
                "status": "unhealthy",
                "provider": self.PROVIDER_NAME,
                "message": f"NewsData.io timeout: {e}",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.PROVIDER_NAME,
                "message": f"Unexpected error: {e}",
            }

    def get_categories(self) -> list[str]:
        """
        Получить поддерживаемые категории

        Returns:
            List[str]: Список поддерживаемых категорий
        """
        import os
        import json
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        categories_path = os.path.join(project_root, 'data', 'newsdata_io_categories.json')
        with open(categories_path, 'r') as f:
            categories = json.load(f)
        return categories
        # return [
        #             "business",
        #             "crime",
        #             "domestic",
        #             "education",
        #             "entertainment",
        #             "environment",
        #             "food",
        #             "health",
        #             "lifestyle",
        #             "politics",
        #             "science",
        #             "sports",
        #             "technology",
        #             "top",
        #             "tourism",
        #             "world",
        #             "other"
        #         ]

    def get_languages(self) -> list[str]:
        """
        Получить поддерживаемые языки

        Returns:
            List[str]: Список поддерживаемых языков
        """
        # Возвращаем стандартные языки NewsData.io
        import os
        import json
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        languages_path = os.path.join(project_root, 'data', 'newsdata_io_languages.json')
        with open(languages_path, 'r') as f:
            languages = json.load(f)
        return languages

    def get_provider_parameters(self) -> dict[str, Any]:
        """
        Получить параметры провайдера из JSON файла
        
        Returns:
            Dict[str, Any]: Словарь с URL эндпоинта и полями формы
                {
                    "url": "https://newsdata.io/api/1/latest",
                    "fields": {
                        "q": "Поисковый запрос",
                        "category": "Категория"
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
            parameters_path = os.path.join(project_root, 'data', 'newsdata_io_parameters.json')
            
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

    def _standardize_article(self, article: dict[str, Any]) -> dict[str, Any]:
        """
        Стандартизация формата статьи NewsData.io под общий формат

        Args:
            article: Статья от NewsData.io

        Returns:
            Dict[str, Any]: Стандартизованная статья
        """
        # Парсим дату публикации
        published_at = None
        if article.get("pubDate"):
            try:
                published_at = datetime.fromisoformat(
                    article["pubDate"].replace("Z", "+00:00")
                )
            except ValueError:
                logger.warning(f"Failed to parse date: {article.get('pubDate')}")

        return {
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "content": article.get("content", ""),
            "url": article.get("link", ""),
            "image_url": article.get("image_url"),
            "published_at": published_at,
            "source": {
                "name": article.get("source_id", ""),
                "id": article.get("source_id", ""),
            },
            "author": article.get("creator", [None])[0]
            if article.get("creator")
            else None,
            "provider": self.PROVIDER_NAME,
            "language": article.get("language"),
            "category": article.get("category", [None])[0]
            if article.get("category")
            else None,
            "country": article.get("country", [None])[0]
            if article.get("country")
            else None,
            "sentiment": article.get("sentiment"),
            "duplicate": article.get("duplicate", False),
            "raw_data": article,  # Сохраняем оригинальные данные
        }

    def _standardize_source(self, source: dict[str, Any]) -> dict[str, Any]:
        """
        Стандартизация формата источника NewsData.io под общий формат

        Args:
            source: Источник от NewsData.io

        Returns:
            Dict[str, Any]: Стандартизованный источник
        """
        return {
            "id": source.get("id", ""),
            "name": source.get("name", ""),
            "description": source.get("description", ""),
            "url": source.get("url", ""),
            "category": source.get("category", [None])[0]
            if source.get("category")
            else None,
            "language": source.get("language", [None])[0]
            if source.get("language")
            else None,
            "country": source.get("country", [None])[0]
            if source.get("country")
            else None,
            "provider": self.PROVIDER_NAME,
            "raw_data": source,  # Сохраняем оригинальные данные
        }
