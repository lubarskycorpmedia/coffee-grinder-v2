# src/services/news/fetchers/__init__.py

# Автоматический импорт всех fetcher'ов для их регистрации через метакласс
from .base import BaseFetcher, NewsAPIError, FetcherRegistry
from .thenewsapi_com import TheNewsAPIFetcher
from .newsapi_org import NewsAPIFetcher

__all__ = [
    'BaseFetcher',
    'NewsAPIError', 
    'FetcherRegistry',
    'TheNewsAPIFetcher',
    'NewsAPIFetcher'
] 