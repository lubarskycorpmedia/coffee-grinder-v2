# src/config.py
import os
from functools import lru_cache
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings


class NewsSettings(BaseModel):
    """Настройки для модуля новостей"""
    NEWS_API_PROVIDER: str = Field(default="thenewsapi", description="Провайдер новостей")
    THENEWSAPI_API_TOKEN: str = Field(..., description="API токен для TheNewsAPI")
    MAX_RETRIES: int = Field(default=3, description="Максимальное количество попыток")
    BACKOFF_FACTOR: float = Field(default=0.5, description="Коэффициент backoff для повторных попыток")


class AISettings(BaseModel):
    """Настройки для AI/LLM модулей"""
    OPENAI_API_KEY: str = Field(..., description="API ключ OpenAI")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="Модель OpenAI для обработки")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Модель для эмбеддингов")
    MAX_TOKENS: int = Field(default=1000, description="Максимальное количество токенов")
    TEMPERATURE: float = Field(default=0.7, description="Температура для генерации")


class GoogleSettings(BaseModel):
    """Настройки для Google сервисов"""
    GOOGLE_GSHEET_ID: str = Field(..., description="ID Google Sheets документа")
    GOOGLE_ACCOUNT_EMAIL: str = Field(..., description="Email Google аккаунта")
    GOOGLE_ACCOUNT_KEY: str = Field(..., description="Ключ Google аккаунта")


class Settings(BaseSettings):
    """Общие настройки приложения"""
    
    # Настройки новостей
    NEWS_API_PROVIDER: str = Field(default="thenewsapi", description="Провайдер новостей")
    THENEWSAPI_API_TOKEN: str = Field(..., description="API токен для TheNewsAPI")
    MAX_RETRIES: int = Field(default=3, description="Максимальное количество попыток")
    BACKOFF_FACTOR: float = Field(default=0.5, description="Коэффициент backoff для повторных попыток")
    
    # Настройки AI
    OPENAI_API_KEY: str = Field(..., description="API ключ OpenAI")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="Модель OpenAI для обработки")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", description="Модель для эмбеддингов")
    MAX_TOKENS: int = Field(default=1000, description="Максимальное количество токенов")
    TEMPERATURE: float = Field(default=0.7, description="Температура для генерации")
    
    # Настройки Google
    GOOGLE_GSHEET_ID: str = Field(..., description="ID Google Sheets документа")
    GOOGLE_ACCOUNT_EMAIL: str = Field(..., description="Email Google аккаунта")
    GOOGLE_ACCOUNT_KEY: str = Field(..., description="Ключ Google аккаунта")
    
    # Общие настройки
    LOG_LEVEL: str = Field(default="INFO", description="Уровень логирования")
    DEBUG: bool = Field(default=False, description="Режим отладки")
    
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
def get_news_settings() -> NewsSettings:
    """Получить настройки для модуля новостей"""
    try:
        # Пытаемся получить из общих настроек
        settings = get_settings()
        return NewsSettings(
            NEWS_API_PROVIDER=settings.NEWS_API_PROVIDER,
            THENEWSAPI_API_TOKEN=settings.THENEWSAPI_API_TOKEN,
            MAX_RETRIES=settings.MAX_RETRIES,
            BACKOFF_FACTOR=settings.BACKOFF_FACTOR,
        )
    except Exception:
        # Если не удается получить общие настройки, пытаемся получить только нужные
        return NewsSettings(
            NEWS_API_PROVIDER=os.getenv("NEWS_API_PROVIDER", "thenewsapi"),
            THENEWSAPI_API_TOKEN=os.getenv("THENEWSAPI_API_TOKEN"),
            MAX_RETRIES=int(os.getenv("MAX_RETRIES", "3")),
            BACKOFF_FACTOR=float(os.getenv("BACKOFF_FACTOR", "0.5")),
        )


@lru_cache()
def get_ai_settings() -> AISettings:
    """Получить настройки для AI модулей"""
    try:
        # Пытаемся получить из общих настроек
        settings = get_settings()
        return AISettings(
            OPENAI_API_KEY=settings.OPENAI_API_KEY,
            OPENAI_MODEL=settings.OPENAI_MODEL,
            OPENAI_EMBEDDING_MODEL=settings.OPENAI_EMBEDDING_MODEL,
            MAX_TOKENS=settings.MAX_TOKENS,
            TEMPERATURE=settings.TEMPERATURE,
        )
    except Exception:
        # Если не удается получить общие настройки, пытаемся получить только нужные
        return AISettings(
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY"),
            OPENAI_MODEL=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            OPENAI_EMBEDDING_MODEL=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            MAX_TOKENS=int(os.getenv("MAX_TOKENS", "1000")),
            TEMPERATURE=float(os.getenv("TEMPERATURE", "0.7")),
        )


@lru_cache()
def get_google_settings() -> GoogleSettings:
    """Получить настройки для Google сервисов"""
    try:
        # Пытаемся получить из общих настроек
        settings = get_settings()
        return GoogleSettings(
            GOOGLE_GSHEET_ID=settings.GOOGLE_GSHEET_ID,
            GOOGLE_ACCOUNT_EMAIL=settings.GOOGLE_ACCOUNT_EMAIL,
            GOOGLE_ACCOUNT_KEY=settings.GOOGLE_ACCOUNT_KEY,
        )
    except Exception:
        # Если не удается получить общие настройки, пытаемся получить только нужные
        return GoogleSettings(
            GOOGLE_GSHEET_ID=os.getenv("GOOGLE_GSHEET_ID"),
            GOOGLE_ACCOUNT_EMAIL=os.getenv("GOOGLE_ACCOUNT_EMAIL"),
            GOOGLE_ACCOUNT_KEY=os.getenv("GOOGLE_ACCOUNT_KEY"),
        )


def get_log_level() -> str:
    """Получить уровень логирования"""
    return os.getenv("LOG_LEVEL", "INFO")


def is_debug_mode() -> bool:
    """Проверить включен ли режим отладки"""
    return os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")