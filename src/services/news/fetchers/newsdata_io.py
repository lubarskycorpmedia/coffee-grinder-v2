# src/services/news/fetchers/newsdata_io.py

from datetime import datetime
from typing import Any, TYPE_CHECKING

from newsdataapi import NewsDataApiClient

from src.logger import setup_logger

from .base import BaseFetcher

if TYPE_CHECKING:
    from src.config import NewsDataIOSettings

logger = setup_logger(__name__)


class NewsDataIOFetcher(BaseFetcher):
    """Fetcher для NewsData.io с полной поддержкой всех эндпоинтов"""

    PROVIDER_NAME = "newsdata"

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

    def fetch_all_news(self, **kwargs: Any) -> dict[str, Any]:
        """
        Получает все новости (для совместимости с базовым классом)

        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            articles = self.search_news(**kwargs)
            return {"articles": articles}
        except Exception as e:
            from .base import NewsAPIError

            return {"error": NewsAPIError(f"Failed to fetch all news: {e}")}

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

    def fetch_news(
        self,
        query: str | None = None,
        category: str | None = None,
        language: str | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Универсальный метод для получения новостей

        Args:
            query: Поисковый запрос
            category: Категория новостей
            language: Язык новостей
            limit: Максимальное количество новостей
            **kwargs: Дополнительные параметры (country, domain, etc.)

        Returns:
            Dict[str, Any]: Результат в стандартном формате с полем "articles"
        """
        try:
            # Подготавливаем параметры для запроса
            params = {"size": min(limit, self.page_size)}

            # Добавляем поисковый запрос если есть
            if query:
                params["q"] = query

            # Добавляем категорию если есть
            if category:
                params["category"] = category

            # Добавляем язык если есть
            if language:
                params["language"] = language

            # Добавляем дополнительные параметры из kwargs
            if "country" in kwargs and kwargs["country"]:
                params["country"] = str(kwargs["country"])
            if "domain" in kwargs and kwargs["domain"]:
                params["domain"] = str(kwargs["domain"])
            if "timeframe" in kwargs and kwargs["timeframe"]:
                params["timeframe"] = str(kwargs["timeframe"])

            # Выполняем запрос через библиотеку
            response = self.client.news_api(**params)

            if response.get("status") != "success":
                logger.error(
                    f"NewsData.io API error: {response.get('message', 'Unknown error')}"
                )
                from .base import NewsAPIError

                return {
                    "error": NewsAPIError(
                        f"NewsData.io API error: {response.get('message', 'Unknown error')}"
                    )
                }

            articles = response.get("results", [])
            standardized_articles = [
                self._standardize_article(article) for article in articles
            ]
            return {"articles": standardized_articles}

        except Exception as e:
            logger.error(f"NewsData.io fetch exception: {e}")
            from .base import NewsAPIError

            return {"error": NewsAPIError(f"NewsData.io fetch exception: {e}")}

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
            if "domain" in kwargs and kwargs["domain"]:
                params["domain"] = str(kwargs["domain"])
            if "category" in kwargs and kwargs["category"]:
                params["category"] = str(kwargs["category"])

            response = self.client.news_api(**params)

            if response.get("status") != "success":
                logger.error(
                    f"NewsData.io search error: {response.get('message', 'Unknown error')}"
                )
                return []

            articles = response.get("results", [])
            return [self._standardize_article(article) for article in articles]

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

            response = self.client.sources_api(**params)

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
            response = self.client.sources_api()

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
        # TODO: АРХИТЕКТУРНАЯ ПРОБЛЕМА - захардкоженные категории
        #
        # ПРОБЛЕМА:
        # Метод возвращает статичный список категорий NewsData.io вместо получения
        # реальных категорий из источников. NewsData.io предоставляет фиксированный
        # набор категорий, но источники могут иметь дополнительные категории.
        #
        # ВАРИАНТЫ РЕШЕНИЯ:
        # 1. Получать категории из sources_api() и извлекать уникальные category
        # 2. Разделить на get_supported_categories() (API категории) и get_available_categories() (из источников)
        # 3. Комбинировать: возвращать API категории + категории из источников
        # 4. Добавить параметр source для выбора: "api" или "sources"
        #
        # ОСОБЕННОСТЬ NewsData.io:
        # В отличие от других API, здесь категории могут быть более гибкими,
        # но для стабильности используем стандартный набор.

        # Возвращаем стандартные категории NewsData.io
        return [
            "business",
            "entertainment",
            "environment",
            "food",
            "health",
            "politics",
            "science",
            "sports",
            "technology",
            "top",
            "tourism",
            "world",
        ]

    def get_languages(self) -> list[str]:
        """
        Получить поддерживаемые языки

        Returns:
            List[str]: Список поддерживаемых языков
        """
        # Возвращаем стандартные языки NewsData.io
        return [
            "en",
            "ar",
            "bn",
            "cs",
            "da",
            "de",
            "el",
            "es",
            "et",
            "fa",
            "fi",
            "fr",
            "he",
            "hi",
            "hr",
            "hu",
            "id",
            "it",
            "ja",
            "ko",
            "lt",
            "lv",
            "ms",
            "nl",
            "no",
            "pl",
            "pt",
            "ro",
            "ru",
            "sk",
            "sl",
            "sv",
            "ta",
            "th",
            "tr",
            "uk",
            "vi",
            "zh",
        ]

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
