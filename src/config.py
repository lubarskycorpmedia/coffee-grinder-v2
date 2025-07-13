# src/config.py
import os
from functools import lru_cache
from typing import Optional, Dict, List, Union
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # Убираем все дефолтные значения для языков и категорий
    headlines_per_category: int = Field(default=6, description="Количество заголовков на категорию")


class NewsAPISettings(BaseProviderSettings):
    """Настройки для NewsAPI.org провайдера"""
    api_key: str = Field(..., description="API ключ для NewsAPI.org")
    base_url: str = Field(default="https://newsapi.org/v2", description="Базовый URL API")
    # Убираем все дефолтные значения для языков, стран и категорий
    page_size: int = Field(default=100, description="Размер страницы результатов")


class NewsDataIOSettings(BaseProviderSettings):
    """Настройки для NewsData.io провайдера"""
    api_key: str = Field(..., description="API ключ для NewsData.io")
    base_url: str = Field(default="https://newsdata.io/api/1", description="Базовый URL API")
    # Убираем все дефолтные значения для языков, стран и категорий
    page_size: int = Field(default=10, description="Размер страницы результатов")


class MediaStackSettings(BaseProviderSettings):
    """Настройки для MediaStack провайдера"""
    access_key: str = Field(..., description="Access key для MediaStack API")
    base_url: str = Field(default="https://api.mediastack.com/v1", description="Базовый URL API")
    page_size: int = Field(default=25, description="Размер страницы результатов")


class NewsProvidersSettings(BaseModel):
    """Настройки всех новостных провайдеров"""
    providers: Dict[str, Union[TheNewsAPISettings, NewsAPISettings, NewsDataIOSettings, MediaStackSettings]] = Field(
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
    
    def get_provider_settings(self, provider_name: str) -> Optional[Union[TheNewsAPISettings, NewsAPISettings, NewsDataIOSettings, MediaStackSettings]]:
        """Получить настройки конкретного провайдера"""
        return self.providers.get(provider_name)
    
    def get_enabled_providers(self) -> Dict[str, Union[TheNewsAPISettings, NewsAPISettings, NewsDataIOSettings, MediaStackSettings]]:
        """Получить только включенные провайдеры"""
        return {name: settings for name, settings in self.providers.items() if settings.enabled}
    
    def get_providers_by_priority(self) -> List[tuple[str, Union[TheNewsAPISettings, NewsAPISettings, NewsDataIOSettings, MediaStackSettings]]]:
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
    # Убираем дефолтный язык - пусть будет None
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
    THENEWSAPI_API_TOKEN: Optional[str] = Field(default=None, description="API токен для TheNewsAPI")
    NEWSAPI_API_KEY: Optional[str] = Field(default=None, description="API ключ для NewsAPI.org")
    NEWSDATA_API_KEY: Optional[str] = Field(default=None, description="API ключ для NewsData.io")
    MEDIASTACK_API_KEY: Optional[str] = Field(default=None, description="Access key для MediaStack API")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="API ключ OpenAI")
    GOOGLE_SHEET_ID: Optional[str] = Field(default=None, description="ID Google Sheets документа")
    GOOGLE_SERVICE_ACCOUNT_PATH: Optional[str] = Field(default=None, description="Путь к файлу с Google service account JSON")
    GOOGLE_ACCOUNT_EMAIL: Optional[str] = Field(default=None, description="Email Google аккаунта")
    GOOGLE_ACCOUNT_KEY: Optional[str] = Field(default=None, description="Ключ Google аккаунта")
    
    model_config = SettingsConfigDict(
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
        providers: Dict[str, Union[TheNewsAPISettings, NewsAPISettings, NewsDataIOSettings, MediaStackSettings]] = {}
        
        # TheNewsAPI провайдер
        if settings.THENEWSAPI_API_TOKEN:
            providers["thenewsapi"] = TheNewsAPISettings(
                api_token=settings.THENEWSAPI_API_TOKEN,
                priority=1,
                enabled=True
            )
        
        # NewsAPI провайдер
        if settings.NEWSAPI_API_KEY:
            providers["newsapi"] = NewsAPISettings(
                api_key=settings.NEWSAPI_API_KEY,
                priority=2,
                enabled=True
            )
        
        # NewsData.io провайдер
        if settings.NEWSDATA_API_KEY:
            providers["newsdata"] = NewsDataIOSettings(
                api_key=settings.NEWSDATA_API_KEY,
                priority=3,
                enabled=True
            )
        
        # MediaStack провайдер
        if settings.MEDIASTACK_API_KEY:
            providers["mediastack"] = MediaStackSettings(
                access_key=settings.MEDIASTACK_API_KEY,
                priority=4,
                enabled=True
            )
        
        return NewsProvidersSettings(
            providers=providers,
            default_provider="thenewsapi" if "thenewsapi" in providers else (
                "newsapi" if "newsapi" in providers else (
                    "newsdata" if "newsdata" in providers else (
                        "mediastack" if "mediastack" in providers else "thenewsapi"
                    )
                )
            ),
            fallback_providers=list(providers.keys())
        )
    except Exception as e:
        # Fallback конфигурация с переменными окружения
        fallback_providers: Dict[str, Union[TheNewsAPISettings, NewsAPISettings, NewsDataIOSettings, MediaStackSettings]] = {}
        
        thenewsapi_token = os.getenv("THENEWSAPI_API_TOKEN")
        if thenewsapi_token:
            fallback_providers["thenewsapi"] = TheNewsAPISettings(
                api_token=thenewsapi_token,
                priority=1,
                enabled=True
            )
        
        newsapi_key = os.getenv("NEWSAPI_API_KEY")
        if newsapi_key:
            fallback_providers["newsapi"] = NewsAPISettings(
                api_key=newsapi_key,
                priority=2,
                enabled=True
            )
        
        newsdata_key = os.getenv("NEWSDATA_API_KEY")
        if newsdata_key:
            fallback_providers["newsdata"] = NewsDataIOSettings(
                api_key=newsdata_key,
                priority=3,
                enabled=True
            )
        
        mediastack_key = os.getenv("MEDIASTACK_API_KEY")
        if mediastack_key:
            fallback_providers["mediastack"] = MediaStackSettings(
                access_key=mediastack_key,
                priority=4,
                enabled=True
            )
        
        return NewsProvidersSettings(
            providers=fallback_providers,
            default_provider="thenewsapi" if "thenewsapi" in fallback_providers else "newsapi",
            fallback_providers=list(fallback_providers.keys())
        )


@lru_cache()
def get_ai_settings() -> AISettings:
    """Получить настройки для AI модулей"""
    try:
        # Получаем секретные данные из Settings, остальное берем из дефолтов класса
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        return AISettings(
            OPENAI_API_KEY=settings.OPENAI_API_KEY,
            # Остальные параметры используют дефолтные значения из класса AISettings
        )
    except Exception:
        # Если не удается получить общие настройки, пытаемся получить только нужные
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY is required")
        return AISettings(
            OPENAI_API_KEY=openai_key,
        )


@lru_cache()
def get_google_settings() -> GoogleSettings:
    """Получить настройки для Google сервисов"""
    try:
        # Получаем секретные данные из Settings
        settings = get_settings()
        if not all([settings.GOOGLE_SHEET_ID, settings.GOOGLE_SERVICE_ACCOUNT_PATH, 
                   settings.GOOGLE_ACCOUNT_EMAIL, settings.GOOGLE_ACCOUNT_KEY]):
            raise ValueError("All Google settings are required")
        
        # Гарантируем, что все значения не None после проверки
        assert settings.GOOGLE_SHEET_ID is not None
        assert settings.GOOGLE_SERVICE_ACCOUNT_PATH is not None
        assert settings.GOOGLE_ACCOUNT_EMAIL is not None
        assert settings.GOOGLE_ACCOUNT_KEY is not None
        
        return GoogleSettings(
            GOOGLE_SHEET_ID=settings.GOOGLE_SHEET_ID,
            GOOGLE_SERVICE_ACCOUNT_PATH=settings.GOOGLE_SERVICE_ACCOUNT_PATH,
            GOOGLE_ACCOUNT_EMAIL=settings.GOOGLE_ACCOUNT_EMAIL,
            GOOGLE_ACCOUNT_KEY=settings.GOOGLE_ACCOUNT_KEY,
        )
    except Exception:
        # Если не удается получить общие настройки, пытаемся получить только нужные
        google_settings = [
            os.getenv("GOOGLE_SHEET_ID"),
            os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH"),
            os.getenv("GOOGLE_ACCOUNT_EMAIL"),
            os.getenv("GOOGLE_ACCOUNT_KEY")
        ]
        if not all(google_settings):
            raise ValueError("All Google settings are required")
        
        # Гарантируем, что все значения не None после проверки
        assert all(google_settings)
        
        return GoogleSettings(
            GOOGLE_SHEET_ID=google_settings[0],  # type: ignore
            GOOGLE_SERVICE_ACCOUNT_PATH=google_settings[1],  # type: ignore
            GOOGLE_ACCOUNT_EMAIL=google_settings[2],  # type: ignore
            GOOGLE_ACCOUNT_KEY=google_settings[3],  # type: ignore
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