# src/config.py
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import List

def get_env_file() -> str | None:
    """Определяет файл env в зависимости от окружения."""
    if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS"):
        return None
    return ".env"

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # API Keys
    OPENAI_API_KEY: str
    
    # News API Provider Configuration
    NEWS_API_PROVIDER: str = Field(default="thenewsapi")
    THENEWSAPI_API_TOKEN: str
    
    # Google Sheets Configuration
    GOOGLE_GSHEET_ID: str
    GOOGLE_ACCOUNT_EMAIL: str
    GOOGLE_ACCOUNT_KEY: str

    # News Processing Configuration (константы)
    TOPICS: str = "us,left_reaction,ukraine,world,tech,crazy,marasmus,coffee_grounds"
    ASK_NEWS_COUNT: int = 10
    DAYS_BACK: int = 1
    
    # Deduplication and AI Configuration (константы)
    DEDUP_THRESHOLD: float = 0.85
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 2.0
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO")
    
    # LLM Configuration
    LLM_MODEL: str = Field(default="gpt-4o-mini")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    
    # Ranking Configuration
    RANKING_PROMPT_TEMPLATE: str = """
    Оцени важность и актуальность новости по шкале от 1 до 5, где:
    1 - Малозначимая новость
    2 - Локальная значимость  
    3 - Умеренная важность
    4 - Высокая важность
    5 - Критически важная новость
    
    Заголовок: {title}
    Описание: {description}
    Популярность: {popularity}
    
    Верни только число от 1 до 5.
    """

    @property
    def topics_list(self) -> List[str]:
        """Возвращает список тем как массив строк."""
        return [topic.strip() for topic in self.TOPICS.split(",")]

@lru_cache()
def get_settings() -> Settings:
    return Settings()