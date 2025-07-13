# src/services/news/fetchers/__init__.py

# Автоматический импорт всех fetcher'ов для их регистрации через метакласс
from .base import BaseFetcher, NewsAPIError, FetcherRegistry
from .thenewsapi_com import TheNewsAPIFetcher
from .newsapi_org import NewsAPIFetcher
from .newsdata_io import NewsDataIOFetcher
from .mediastack_com import MediaStackFetcher

__all__ = [
    'BaseFetcher',
    'NewsAPIError', 
    'FetcherRegistry',
    'TheNewsAPIFetcher',
    'NewsAPIFetcher',
    'NewsDataIOFetcher',
    'MediaStackFetcher'
] 