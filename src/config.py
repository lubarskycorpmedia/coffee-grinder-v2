# src/config.py
import os
from functools import lru_cache
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings


class BaseProviderSettings(BaseModel):
    """Базовые настройки для всех провайдеров новостей"""
    enabled: bool = Field(default=True, description="Включен ли провайдер")
    priority: int = Field(default=1, description="Приоритет провайдера (1 - высший)")
    max_retries: int = Field(default=3, description="Максимальное количество попыток")
    backoff_factor: float = Field(default=2.0, description="Коэффициент backoff для повторных попыток")
    timeout: int = Field(default=30, description="Таймаут запроса в секундах")


class TheNewsAPISettings(BaseProviderSettings):
    """Настройки для TheNewsAPI.com провайдера"""
    api_token: str = Field(..., description="API токен для TheNewsAPI")
    base_url: str = Field(default="https://api.thenewsapi.com/v1", description="Базовый URL API")
    supported_languages: List[str] = Field(
        default=["en", "es", "fr", "de", "it", "pt", "ru", "ar", "zh"], 
        description="Поддерживаемые языки"
    )
    supported_categories: List[str] = Field(
        default=["general", "business", "entertainment", "health", "science", "sports", "technology"],
        description="Поддерживаемые категории"
    )
    default_locale: str = Field(default="us", description="Локаль по умолчанию")
    headlines_per_category: int = Field(default=6, description="Количество заголовков на категорию")


class NewsAPISettings(BaseProviderSettings):
    """Настройки для NewsAPI.org провайдера"""
    api_key: str = Field(..., description="API ключ для NewsAPI.org")
    base_url: str = Field(default="https://newsapi.org/v2", description="Базовый URL API")
    supported_languages: List[str] = Field(
        default=["en", "ar", "de", "es", "fr", "he", "it", "nl", "no", "pt", "ru", "sv", "ud", "zh"],
        description="Поддерживаемые языки"
    )
    supported_categories: List[str] = Field(
        default=["business", "entertainment", "general", "health", "science", "sports", "technology"],
        description="Поддерживаемые категории"
    )
    default_country: str = Field(default="us", description="Страна по умолчанию")
    page_size: int = Field(default=100, description="Размер страницы результатов")


class NewsProvidersSettings(BaseModel):
    """Настройки всех новостных провайдеров"""
    providers: Dict[str, BaseProviderSettings] = Field(
        default_factory=dict,
        description="Словарь провайдеров новостей"
    )
    default_provider: str = Field(
        default="thenewsapi",
        description="Провайдер по умолчанию"
    )
    fallback_providers: List[str] = Field(
        default_factory=list,
        description="Список провайдеров для fallback в порядке приоритета"
    )
    
    def get_provider_settings(self, provider_name: str) -> Optional[BaseProviderSettings]:
        """Получить настройки конкретного провайдера"""
        return self.providers.get(provider_name)
    
    def get_enabled_providers(self) -> Dict[str, BaseProviderSettings]:
        """Получить только включенные провайдеры"""
        return {name: settings for name, settings in self.providers.items() if settings.enabled}
    
    def get_providers_by_priority(self) -> List[tuple[str, BaseProviderSettings]]:
        """Получить провайдеры отсортированные по приоритету"""
        enabled = self.get_enabled_providers()
        return sorted(enabled.items(), key=lambda x: x[1].priority)


class AISettings(BaseModel):
    """Настройки для AI/LLM модулей"""
    OPENAI_API_KEY: str = Field(..., description="API ключ OpenAI")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="Модель OpenAI для обработки")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Модель для эмбеддингов")
    MAX_TOKENS: int = Field(default=1000, description="Максимальное количество токенов")
    TEMPERATURE: float = Field(default=0.7, description="Температура для генерации")


class FAISSSettings(BaseModel):
    """Настройки для FAISS векторной базы данных"""
    FAISS_SIMILARITY_THRESHOLD: float = Field(
        default=0.85, 
        description="Порог схожести для дедупликации новостей (0.0-1.0). "
                   "Чем выше значение, тем строже фильтрация дублей. "
                   "0.85 означает что статьи с схожестью >85% считаются дублями"
    )
    FAISS_INDEX_TYPE: str = Field(
        default="IndexFlatIP", 
        description="Тип FAISS индекса для поиска векторов. "
                   "IndexFlatIP - точный поиск по скалярному произведению (рекомендуется). "
                   "IndexFlatL2 - точный поиск по L2 расстоянию. "
                   "IndexIVFFlat - приближенный поиск для больших объемов"
    )
    FAISS_NORMALIZE_VECTORS: bool = Field(
        default=True,
        description="Нормализовать векторы перед добавлением в FAISS индекс. "
                   "True - рекомендуется для косинусного сходства. "
                   "False - для использования сырых векторов"
    )
    MAX_NEWS_ITEMS_FOR_PROCESSING: int = Field(
        default=100,
        description="Максимальное количество новостей для обработки в одном batch. "
                   "Ограничивает нагрузку на OpenAI API и память"
    )


class PipelineSettings(BaseModel):
    """Настройки для pipeline обработки новостей"""
    DEFAULT_LANGUAGE: str = Field(
        default="en",
        description="Язык по умолчанию для поиска новостей. "
                   "Используется для API запросов к источникам новостей"
    )
    DEFAULT_LIMIT: int = Field(
        default=100,
        description="Количество новостей по умолчанию для получения из API"
    )
    PIPELINE_TIMEOUT: int = Field(
        default=300,
        description="Максимальное время выполнения pipeline в секундах (5 минут)"
    )
    ENABLE_PARTIAL_RESULTS: bool = Field(
        default=True,
        description="Возвращать частичные результаты при ошибках в pipeline. "
                   "True - продолжать выполнение даже при ошибках на отдельных этапах"
    )


class GoogleSettings(BaseModel):
    """Настройки для Google сервисов"""
    GOOGLE_SHEET_ID: str = Field(..., description="ID Google Sheets документа")
    GOOGLE_SERVICE_ACCOUNT_PATH: str = Field(..., description="Путь к файлу с Google service account JSON")
    GOOGLE_ACCOUNT_EMAIL: str = Field(..., description="Email Google аккаунта")
    GOOGLE_ACCOUNT_KEY: str = Field(..., description="Ключ Google аккаунта")


class Settings(BaseSettings):
    """Общие настройки приложения - только секретные переменные из .env"""
    
    # Секретные токены и ключи (только эти берутся из .env)
    THENEWSAPI_API_TOKEN: str = Field(..., description="API токен для TheNewsAPI")
    NEWSAPI_API_KEY: str = Field(..., description="API ключ для NewsAPI.org")
    OPENAI_API_KEY: str = Field(..., description="API ключ OpenAI")
    GOOGLE_SHEET_ID: str = Field(..., description="ID Google Sheets документа")
    GOOGLE_SERVICE_ACCOUNT_PATH: str = Field(..., description="Путь к файлу с Google service account JSON")
    GOOGLE_ACCOUNT_EMAIL: str = Field(..., description="Email Google аккаунта")
    GOOGLE_ACCOUNT_KEY: str = Field(..., description="Ключ Google аккаунта")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Игнорируем лишние поля из окружения
    )


@lru_cache()
def get_settings() -> Settings:
    """Получить все настройки приложения"""
    return Settings()


@lru_cache()
def get_news_providers_settings() -> NewsProvidersSettings:
    """Получить настройки всех новостных провайдеров"""
    try:
        # Получаем секретные данные из Settings
        settings = get_settings()
        
        # Создаем настройки провайдеров
        providers = {}
        
        # TheNewsAPI провайдер
        providers["thenewsapi"] = TheNewsAPISettings(
            api_token=settings.THENEWSAPI_API_TOKEN,
            priority=1,
            enabled=True
        )
        
        # NewsAPI провайдер
        providers["newsapi"] = NewsAPISettings(
            api_key=settings.NEWSAPI_API_KEY,
            priority=2,
            enabled=True
        )
        
        return NewsProvidersSettings(
            providers=providers,
            default_provider="thenewsapi",
            fallback_providers=["newsapi"]
        )
    except Exception as e:
        # Fallback конфигурация с переменными окружения
        providers = {}
        
        thenewsapi_token = os.getenv("THENEWSAPI_API_TOKEN")
        if thenewsapi_token:
            providers["thenewsapi"] = TheNewsAPISettings(
                api_token=thenewsapi_token,
                priority=1,
                enabled=True
            )
        
        newsapi_key = os.getenv("NEWSAPI_API_KEY")
        if newsapi_key:
            providers["newsapi"] = NewsAPISettings(
                api_key=newsapi_key,
                priority=2,
                enabled=True
            )
        
        return NewsProvidersSettings(
            providers=providers,
            default_provider="thenewsapi" if "thenewsapi" in providers else "newsapi",
            fallback_providers=list(providers.keys())
        )


@lru_cache()
def get_ai_settings() -> AISettings:
    """Получить настройки для AI модулей"""
    try:
        # Получаем секретные данные из Settings, остальное берем из дефолтов класса
        settings = get_settings()
        return AISettings(
            OPENAI_API_KEY=settings.OPENAI_API_KEY,
            # Остальные параметры используют дефолтные значения из класса AISettings
        )
    except Exception:
        # Если не удается получить общие настройки, пытаемся получить только нужные
        return AISettings(
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
        )


@lru_cache()
def get_google_settings() -> GoogleSettings:
    """Получить настройки для Google сервисов"""
    try:
        # Получаем секретные данные из Settings
        settings = get_settings()
        return GoogleSettings(
            GOOGLE_SHEET_ID=settings.GOOGLE_SHEET_ID,
            GOOGLE_SERVICE_ACCOUNT_PATH=settings.GOOGLE_SERVICE_ACCOUNT_PATH,
            GOOGLE_ACCOUNT_EMAIL=settings.GOOGLE_ACCOUNT_EMAIL,
            GOOGLE_ACCOUNT_KEY=settings.GOOGLE_ACCOUNT_KEY,
        )
    except Exception:
        # Если не удается получить общие настройки, пытаемся получить только нужные
        return GoogleSettings(
            GOOGLE_SHEET_ID=os.getenv("GOOGLE_SHEET_ID"),
            GOOGLE_SERVICE_ACCOUNT_PATH=os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH"),
            GOOGLE_ACCOUNT_EMAIL=os.getenv("GOOGLE_ACCOUNT_EMAIL"),
            GOOGLE_ACCOUNT_KEY=os.getenv("GOOGLE_ACCOUNT_KEY"),
        )


@lru_cache()
def get_faiss_settings() -> FAISSSettings:
    """Получить настройки для FAISS векторной базы данных"""
    # Все настройки используют дефолтные значения из класса FAISSSettings
    return FAISSSettings()


@lru_cache()
def get_pipeline_settings() -> PipelineSettings:
    """Получить настройки для pipeline обработки новостей"""
    # Все настройки используют дефолтные значения из класса PipelineSettings
    return PipelineSettings()


def get_log_level() -> str:
    """Получить уровень логирования"""
    return "INFO"  # Дефолтное значение без переменной окружения


def is_debug_mode() -> bool:
    """Проверить включен ли режим отладки"""
    return False  # Дефолтное значение без переменной окружения