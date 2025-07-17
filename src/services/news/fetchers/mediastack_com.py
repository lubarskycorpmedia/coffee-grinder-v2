# src/services/news/fetchers/mediastack_com.py

import time
import random
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import BaseFetcher, NewsAPIError
from src.logger import setup_logger


class MediaStackFetcher(BaseFetcher):
    """Fetcher для MediaStack API с поддержкой всех эндпоинтов"""
    
    PROVIDER_NAME = "mediastack_com"
    
    def __init__(self, provider_settings):
        """
        Инициализация fetcher'а
        
        Args:
            provider_settings: Настройки провайдера MediaStackSettings
        """
        super().__init__(provider_settings)
        
        # Получаем специфичные настройки для MediaStack
        self.access_key = provider_settings.access_key
        self.base_url = provider_settings.base_url
        self.page_size = provider_settings.page_size
        
        # Путь к файлу маппинга доменов на источники (перенесён в data/)
        # Путь от src/services/news/fetchers/mediastack_com.py до корня проекта: ../../../../
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        self.sources_mapping_file = os.path.join(project_root, "data", "mediastack_com_sources.json")
        
        # Путь к файлу с источниками новостей
        self.news_sources_file = os.path.join(project_root, "data", "news_sources.json")
        
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
    
    def check_source_by_domain(self, domain: str) -> str:
        """
        Публичный метод для проверки существования источника по домену
        
        Args:
            domain: Домен для проверки (может быть URL или доменом)
            
        Returns:
            str: "да" если источник найден, "нет" если не найден, или код ошибки
        """
        try:
            # Нормализуем домен через единый метод
            normalized_domain = self._extract_domain_from_url(domain)
            if not normalized_domain:
                self.logger.warning(f"Failed to normalize domain: {domain}")
                return "нет"
            
            # Загружаем текущий маппинг
            mapping = self._load_sources_mapping()
            
            # Проверяем, есть ли домен уже в маппинге
            if normalized_domain in mapping:
                source_id = mapping[normalized_domain]
                self.logger.debug(f"Found in JSON: {normalized_domain} -> {source_id}")
                if source_id == "unavailable":
                    return "нет"
                else:
                    return "да"
            
            # Загружаем источники новостей только если домен не найден в маппинге
            news_sources = self._load_news_sources()
            search_term = None
            
            # Проверяем, есть ли домен в news_sources.json
            if normalized_domain in news_sources:
                source_names = news_sources[normalized_domain]
                if source_names and len(source_names) > 0:
                    search_term = source_names[0]  # Берём первое значение из массива
                    self.logger.info(f"Found domain '{normalized_domain}' in news_sources.json, using search term: '{search_term}'")
            
            if search_term:
                # Ищем по названию источника из news_sources.json
                self.logger.info(f"Searching for source name: {search_term}")
                search_result = self._make_request("sources", {"search": search_term, "limit": 100})
                
                self.logger.info(f"Search API response for '{search_term}': {search_result}")
                
                if "error" not in search_result:
                    sources = search_result.get("data", [])
                    self.logger.info(f"Found {len(sources)} sources for '{search_term}'")
                    
                    # Логируем первые несколько источников для анализа
                    for i, source in enumerate(sources[:3]):
                        self.logger.info(f"Source {i+1}: code={source.get('code')}, id={source.get('id')}, name={source.get('name')}, url={source.get('url')}")
                    
                    # Ищем совпадение по домену в URL источников
                    for source in sources:
                        source_url = source.get("url", "")
                        if source_url:
                            source_domain = self._extract_domain_from_url(source_url)
                            
                            self.logger.debug(f"Comparing '{normalized_domain}' with source domain '{source_domain}' from URL '{source_url}'")
                            
                            if source_domain and source_domain.lower() == normalized_domain.lower():
                                source_id = source.get("code") or source.get("id", "")
                                if source_id:
                                    self.logger.info(f"Found exact domain match: {normalized_domain} -> {source_id}")
                                    mapping[normalized_domain] = source_id
                                    self._save_sources_mapping(mapping)
                                    return "да"
                else:
                    self.logger.warning(f"Search API returned error for '{search_term}': {search_result}")
            
            # Если источник не найден, возвращаем "нет" без записи в JSON
            self.logger.info(f"Source not found for domain {normalized_domain}")
            return "нет"
            
        except Exception as e:
            self.logger.error(f"Error checking source for domain {domain}: {e}")
            return f"ошибка: {str(e)}"

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
        
        # Добавляем access_key к параметрам
        params["access_key"] = self.access_key
        
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
            
            # RAW SERVER RESPONSE LOGGING
            # print("RAW SERVER RESPONSE:")
            # print(response.text)
            
            # Проверяем на ошибки API
            if "error" in data:
                error_info = data["error"]
                error_msg = error_info.get("message", "Unknown API error")
                error_code = error_info.get("code", "unknown_error")
                
                self.logger.error(f"MediaStack API error [{error_code}]: {error_msg}")
                return {"error": NewsAPIError(f"[{error_code}] {error_msg}", response.status_code, 1)}
            
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
    
    def _load_sources_mapping(self) -> Dict[str, str]:
        """
        Загружает маппинг доменов на источники из JSON файла
        
        Returns:
            Dict[str, str]: Словарь {домен: источник}
        """
        try:
            if os.path.exists(self.sources_mapping_file):
                with open(self.sources_mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Sources mapping file not found: {self.sources_mapping_file}")
                return {}
        except (json.JSONDecodeError, IOError) as e:
            error_msg = f"Failed to load sources mapping from {self.sources_mapping_file}: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _save_sources_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Сохраняет маппинг доменов на источники в JSON файл
        
        Args:
            mapping: Словарь {домен: источник} для сохранения
        """
        try:
            with open(self.sources_mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Sources mapping saved to {self.sources_mapping_file}")
        except IOError as e:
            error_msg = f"Failed to save sources mapping to {self.sources_mapping_file}: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _load_news_sources(self) -> Dict[str, List[str]]:
        """
        Загружает файл news_sources.json с источниками новостей
        
        Returns:
            Dict[str, List[str]]: Словарь {домен: [список названий источников]}
        """
        try:
            if os.path.exists(self.news_sources_file):
                with open(self.news_sources_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"News sources file not found: {self.news_sources_file}")
                return {}
        except (json.JSONDecodeError, IOError) as e:
            error_msg = f"Failed to load news sources from {self.news_sources_file}: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _search_source_by_domain(self, domain: str) -> str:
        """
        Ищет источник MediaStack по домену через API, записывает в JSON и возвращает результат
        
        Args:
            domain: Домен для поиска
            
        Returns:
            str: ID источника или "unavailable"
        """
        try:
            # Нормализуем домен через единый метод
            normalized_domain = self._extract_domain_from_url(domain)
            if not normalized_domain:
                self.logger.warning(f"Failed to normalize domain: {domain}")
                return "unavailable"
            
            # Загружаем текущий маппинг и источники новостей
            mapping = self._load_sources_mapping()
            news_sources = self._load_news_sources()
            
            search_term = None
            
            # Проверяем, есть ли домен в news_sources.json
            if normalized_domain in news_sources:
                source_names = news_sources[normalized_domain]
                if source_names and len(source_names) > 0:
                    search_term = source_names[0]  # Берём первое значение из массива
                    self.logger.info(f"Found domain '{normalized_domain}' in news_sources.json, using search term: '{search_term}'")
            
            if search_term:
                # Ищем по названию источника из news_sources.json
                self.logger.info(f"Searching for source name: {search_term}")
                search_result = self._make_request("sources", {"search": search_term, "limit": 100})
                
                self.logger.info(f"Search API response for '{search_term}': {search_result}")
                
                if "error" not in search_result:
                    sources = search_result.get("data", [])
                    self.logger.info(f"Found {len(sources)} sources for '{search_term}'")
                    
                    # Логируем первые несколько источников для анализа
                    for i, source in enumerate(sources[:3]):
                        self.logger.info(f"Source {i+1}: code={source.get('code')}, id={source.get('id')}, name={source.get('name')}, url={source.get('url')}")
                    
                    # Ищем совпадение по домену в URL источников
                    for source in sources:
                        source_url = source.get("url", "")
                        if source_url:
                            source_domain = self._extract_domain_from_url(source_url)
                            
                            self.logger.debug(f"Comparing '{normalized_domain}' with source domain '{source_domain}' from URL '{source_url}'")
                            
                            if source_domain and source_domain.lower() == normalized_domain.lower():
                                source_id = source.get("code") or source.get("id", "")
                                if source_id:
                                    self.logger.info(f"Found exact domain match: {normalized_domain} -> {source_id}")
                                    mapping[normalized_domain] = source_id
                                    self._save_sources_mapping(mapping)
                                    return source_id
                else:
                    self.logger.warning(f"Search API returned error for '{search_term}': {search_result}")
            
            # Если домен не найден в news_sources.json или не найдено совпадение в первой сотне
            # применяем _extract_root_domain
            self.logger.info(f"Domain {normalized_domain} not found via search or not in news_sources.json, trying root domain")
            root_domain = self._extract_root_domain(normalized_domain)
            
            # Проверяем, удалось ли извлечь root domain
            if not root_domain:
                self.logger.warning(f"Failed to extract root domain for {normalized_domain}, marking as unavailable")
                mapping[normalized_domain] = "unavailable"
                self._save_sources_mapping(mapping)
                return "unavailable"
            
            # Записываем root domain в маппинг (без повторного запроса к серверу)
            self.logger.info(f"Recording root domain result: {normalized_domain} -> {root_domain}")
            mapping[normalized_domain] = root_domain
            self._save_sources_mapping(mapping)
            return root_domain
            
        except Exception as e:
            self.logger.error(f"Error searching source for domain {domain}: {e}")
            # Записываем "unavailable" в JSON даже при ошибке
            try:
                normalized_domain = self._extract_domain_from_url(domain)
                if normalized_domain:
                    mapping = self._load_sources_mapping()
                    mapping[normalized_domain] = "unavailable"
                    self._save_sources_mapping(mapping)
            except:
                pass  # Игнорируем ошибки записи при исключениях
            return "unavailable"
    

    
    def _extract_root_domain(self, domain: str) -> Optional[str]:
        """
        Преобразует домен: заменяет точки на запятые и удаляет 'news' если это не домен 1-го уровня.
        
        Args:
            domain: Уже нормализованный домен (например, 'sub.domain.com')
            
        Returns:
            Преобразованный домен (например, 'sub,domain') или None если невозможно извлечь
        """
        if not domain:
            return None
        
        # Убираем расширение (.com, .org, .net и т.д.)
        if "." in domain:
            domain_without_extension = domain.rsplit(".", 1)[0]
        else:
            return domain
        
        # Разбиваем на части
        parts = domain_without_extension.split(".")
        
        # Удаляем 'news' если это не единственная часть (не домен 1-го уровня)
        if len(parts) > 1 and "news" in parts:
            parts = [part for part in parts if part != "news"]
        
        # Если после удаления 'news' ничего не осталось, возвращаем None
        if not parts:
            return None
        
        # Заменяем точки на запятые
        return ",".join(parts)

    def _extract_domain_from_url(self, url: str) -> Optional[str]:
        """
        Извлекает и нормализует домен из URL или доменной строки
        
        Обрабатывает все возможные варианты:
        - https://www.sub.domain.com/path -> sub.domain.com
        - WWW.DOMAIN.COM -> domain.com  
        - sub.domain.com -> sub.domain.com
        - domain.com/path -> domain.com
        
        Args:
            url: URL или домен для обработки
            
        Returns:
            Optional[str]: Нормализованный домен или None
        """
        try:
            from urllib.parse import urlparse
            
            # Очищаем входную строку
            cleaned_url = url.strip().lower()
            
            # Если это не URL, добавляем схему для корректного парсинга
            if not cleaned_url.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
                cleaned_url = f'https://{cleaned_url}'
            
            # Парсим URL
            parsed = urlparse(cleaned_url)
            domain = parsed.netloc
            
            if not domain:
                return None
            
            # Убираем все www. префиксы (включая множественные)
            while domain.startswith('www.'):
                domain = domain[4:]
            
            # Убираем порты если есть
            if ':' in domain:
                domain = domain.split(':')[0]
            
            return domain if domain else None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract domain from '{url}': {e}")
            return None
    
    def _convert_domains_to_sources(self, domains: str) -> str:
        """
        Конвертирует параметр domains в sources для MediaStack API
        
        TODO: В будущем можно добавить поддержку exclude синтаксиса MediaStack ("-cnn")
        для исключения источников, но сейчас это не реализовано.
        
        Args:
            domains: Строка с доменами через запятую (например, "cnn.com,bbc.com")
            
        Returns:
            str: Строка с источниками через запятую (например, "cnn,bbc,unavailable")
            Возвращает строго то, что найдено/получено, без фильтрации
        """
        if not domains:
            return ""
        
        domain_list = [d.strip() for d in domains.split(",") if d.strip()]
        source_list = []
        
        # Загружаем маппинг один раз
        mapping = self._load_sources_mapping()
        
        for domain in domain_list:
            # Нормализуем домен через единый метод
            normalized_domain = self._extract_domain_from_url(domain)
            if not normalized_domain:
                self.logger.warning(f"Failed to normalize domain: {domain}, skipping")
                continue
            
            # Проверяем JSON
            if normalized_domain in mapping:
                source_id = mapping[normalized_domain]
                self.logger.debug(f"Found in JSON: {normalized_domain} -> {source_id}")
            else:
                # Вызываем поиск, который сам запишет в JSON
                self.logger.info(f"Domain {normalized_domain} not in JSON, searching via API...")
                source_id = self._search_source_by_domain(normalized_domain)
            
            # Добавляем все значения как есть, без фильтрации
            source_list.append(source_id)
        
        result = ",".join(source_list)
        self.logger.debug(f"Converted domains '{domains}' to sources '{result}'")
        return result
    
    def check_health(self) -> Dict[str, Any]:
        """
        Проверка состояния провайдера
        
        Returns:
            Dict[str, Any]: Результат проверки
        """
        try:
            # Делаем минимальный запрос для проверки доступности API
            result = self._make_request("sources", {"limit": 1})
            
            if "error" in result:
                return {
                    "status": "unhealthy",
                    "provider": self.PROVIDER_NAME,
                    "message": f"API error: {result['error']}"
                }
            
            return {
                "status": "healthy",
                "provider": self.PROVIDER_NAME,
                "message": "MediaStack API is accessible"
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
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        categories_path = os.path.join(project_root, 'data', 'mediastack_com_categories.json')
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
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        languages_path = os.path.join(project_root, 'data', 'mediastack_com_languages.json')
        with open(languages_path, 'r') as f:
            languages = json.load(f)
        return languages

    def get_provider_parameters(self) -> Dict[str, Any]:
        """
        Получить параметры провайдера из JSON файла
        
        Returns:
            Dict[str, Any]: Словарь с URL эндпоинта и полями формы
                {
                    "url": "https://api.mediastack.com/v1/news",
                    "fields": {
                        "sources": "Источники",
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
            parameters_path = os.path.join(project_root, 'data', 'mediastack_com_parameters.json')
            
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
        
    def fetch_news(self,
                   query: Optional[str] = None,
                   category: Optional[str] = None,
                   language: Optional[str] = None,
                   limit: int = 50,
                   **kwargs) -> Dict[str, Any]:
        """
        Универсальный метод для получения новостей (Live News)
        
        Args:
            query: Поисковый запрос (keywords)
            category: Категория новостей (categories)
            language: Язык новостей (languages)
            limit: Максимальное количество новостей
            **kwargs: Дополнительные параметры для MediaStack API
            
        Returns:
            Dict в стандартном формате с полем 'articles'
        """
        try:
            # Подготавливаем параметры для запроса
            params = {
                "limit": min(limit, 100),  # MediaStack max limit is 100
                "sort": kwargs.get("sort", "published_desc")
            }
            
            # Добавляем поисковый запрос если есть
            if query:
                params["keywords"] = query
            
            # Добавляем категорию если есть
            if category:
                params["categories"] = category
            
            # Добавляем язык если есть
            if language:
                params["languages"] = language
            
            # Добавляем дополнительные параметры из kwargs
            for key, value in kwargs.items():
                if key not in ["sort"] and value is not None:
                    # Маппинг параметров
                    if key == "sources":
                        params["sources"] = str(value)
                    elif key == "domains":
                        # Конвертируем домены в источники MediaStack
                        sources = self._convert_domains_to_sources(str(value))
                        if sources:
                            params["sources"] = sources
                        # Не передаем domains в API, так как MediaStack его не поддерживает
                    elif key == "countries":
                        params["countries"] = str(value)
                    elif key == "date":
                        params["date"] = str(value)
                    elif key == "offset":
                        params["offset"] = int(value)
                    else:
                        params[key] = value
            
            self.logger.debug(f"Calling MediaStack news API with params: {params}")
            
            # Вызываем API
            result = self._make_request("news", params)
            
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
                    "category": article.get("category", category),
                    "language": article.get("language", language),
                    # Дополнительные поля из API
                    "author": article.get("author", ""),
                    "image_url": article.get("image", ""),
                    "country": article.get("country", ""),
                    "raw_data": article  # Сохраняем оригинальные данные
                }
                articles.append(standardized_article)
            
            self.logger.info(f"Successfully standardized {len(articles)} articles")
            
            meta = {
                "total": result.get("pagination", {}).get("total", len(articles)),
                "limit": limit,
                "offset": result.get("pagination", {}).get("offset", 0),
                "count": result.get("pagination", {}).get("count", len(articles))
            }
            
            return {
                "articles": articles,
                "meta": meta,
                "pagination": result.get("pagination", {})
            }
            
        except Exception as e:
            error_msg = f"Failed to fetch news: {str(e)}"
            self.logger.error(error_msg)
            error = NewsAPIError(error_msg, None, 1)
            return {"error": error}
    
    def fetch_headlines(self, **kwargs) -> Dict[str, Any]:
        """
        Получает заголовки новостей (алиас для fetch_news)
        
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            result = self.fetch_news(**kwargs)
            return result
        except Exception as e:
            return {"error": NewsAPIError(f"Failed to fetch headlines: {e}")}
    
    def fetch_all_news(self, **kwargs) -> Dict[str, Any]:
        """
        Получает все новости (алиас для fetch_news)
        
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            result = self.fetch_news(**kwargs)
            return result
        except Exception as e:
            return {"error": NewsAPIError(f"Failed to fetch all news: {e}")}
    
    def fetch_top_stories(self, **kwargs) -> Dict[str, Any]:
        """
        Получает топ новости (алиас для fetch_news)
        
        Returns:
            Dict[str, Any]: Результат в формате базового класса
        """
        try:
            result = self.fetch_news(**kwargs)
            return result
        except Exception as e:
            return {"error": NewsAPIError(f"Failed to fetch top stories: {e}")}
    
    def fetch_historical_news(self,
                             date: str,
                             sources: Optional[str] = None,
                             categories: Optional[str] = None,
                             countries: Optional[str] = None,
                             languages: Optional[str] = None,
                             keywords: Optional[str] = None,
                             sort: str = "published_desc",
                             limit: int = 25,
                             offset: int = 0) -> Dict[str, Any]:
        """
        Получает исторические новости (Historical News)
        
        Args:
            date: Дата в формате YYYY-MM-DD или диапазон YYYY-MM-DD,YYYY-MM-DD
            sources: Источники для включения/исключения (cnn,-bbc)
            categories: Категории для включения/исключения (business,-sports)
            countries: Страны для включения/исключения (us,-gb)
            languages: Языки для включения/исключения (en,-de)
            keywords: Ключевые слова для поиска/исключения (virus,-corona)
            sort: Сортировка (published_desc, published_asc, popularity)
            limit: Количество результатов (max 100)
            offset: Смещение для пагинации
            
        Returns:
            Dict с результатами или ошибкой
        """
        params = {
            "date": date,
            "sort": sort,
            "limit": min(limit, 100),
            "offset": offset
        }
        
        # Добавляем параметры только если они указаны
        if sources:
            params["sources"] = sources
        if categories:
            params["categories"] = categories
        if countries:
            params["countries"] = countries
        if languages:
            params["languages"] = languages
        if keywords:
            params["keywords"] = keywords
        
        return self._make_request("news", params)
    
    def get_sources(self,
                   search: Optional[str] = None,
                   countries: Optional[str] = None,
                   languages: Optional[str] = None,
                   categories: Optional[str] = None,
                   limit: int = 25,
                   offset: int = 0) -> Dict[str, Any]:
        """
        Получает список доступных источников новостей
        
        Args:
            search: Поисковый запрос по источникам
            countries: Страны для фильтрации
            languages: Языки для фильтрации
            categories: Категории для фильтрации
            limit: Количество результатов (max 100)
            offset: Смещение для пагинации
            
        Returns:
            Dict с результатами или ошибкой
        """
        params = {
            "limit": min(limit, 100),
            "offset": offset
        }
        
        # Добавляем параметры только если они указаны
        if search:
            params["search"] = search
        if countries:
            params["countries"] = countries
        if languages:
            params["languages"] = languages
        if categories:
            params["categories"] = categories
        
        result = self._make_request("sources", params)
        
        # Если есть ошибка, возвращаем как есть
        if "error" in result:
            return result
        
        # Стандартизируем формат источников
        raw_sources = result.get("data", [])
        standardized_sources = []
        
        for source in raw_sources:
            standardized_source = {
                "id": source.get("id", ""),
                "name": source.get("name", ""),
                "category": source.get("category", ""),
                "country": source.get("country", ""),
                "language": source.get("language", ""),
                "url": source.get("url", ""),
                "provider": self.PROVIDER_NAME,
                "raw_data": source  # Сохраняем оригинальные данные
            }
            standardized_sources.append(standardized_source)
        
        return {
            "sources": standardized_sources,
            "pagination": result.get("pagination", {})
        }
    
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
        # Используем fetch_news для поиска
        result = self.fetch_news(
            query=query,
            language=language,
            limit=limit,
            **kwargs
        )
        
        if "error" in result:
            return []
        
        return result.get("articles", [])
    
    def get_supported_countries(self) -> List[str]:
        """
        Получить поддерживаемые страны
        
        Returns:
            List[str]: Список 2-буквенных кодов стран
        """
        # Возвращаем наиболее распространенные страны, поддерживаемые MediaStack
        # Полный список можно получить через get_sources() и извлечь уникальные country
        return [
            "us", "gb", "ca", "au", "de", "fr", "es", "it", "nl", "be", "ch", "at",
            "se", "no", "dk", "fi", "pl", "cz", "hu", "pt", "gr", "ie", "ru", "ua",
            "cn", "jp", "kr", "in", "sg", "hk", "my", "th", "id", "ph", "vn", "tw",
            "br", "mx", "ar", "co", "pe", "cl", "ve", "za", "ng", "eg", "ma", "ke",
            "il", "tr", "ae", "sa", "qa", "kw", "om", "bh", "jo", "lb", "pk", "bd"
        ]
    
    def _extract_category(self, article: Dict[str, Any], requested_category: Optional[str]) -> Optional[str]:
        """
        Извлекает категорию из статьи
        
        Args:
            article: Статья от API
            requested_category: Запрошенная категория
            
        Returns:
            Optional[str]: Категория статьи
        """
        # MediaStack возвращает категорию прямо в поле category
        return article.get("category", requested_category) 