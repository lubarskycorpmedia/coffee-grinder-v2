# src/services/news/fetchers/newsapi_org.py

from typing import Dict, Any
from .base import BaseFetcher, NewsAPIError


class NewsAPIFetcher(BaseFetcher):
    """Fetcher для newsapi.org - заглушка для будущей реализации"""
    
    def __init__(self):
        # TODO: Реализовать при необходимости
        pass
    
    def fetch_headlines(self, **kwargs) -> Dict[str, Any]:
        """Получает заголовки новостей - не реализовано"""
        return {"error": NewsAPIError("NewsAPI.org fetcher not implemented yet")}
    
    def fetch_all_news(self, **kwargs) -> Dict[str, Any]:
        """Получает все новости по поиску - не реализовано"""
        return {"error": NewsAPIError("NewsAPI.org fetcher not implemented yet")}
    
    def fetch_top_stories(self, **kwargs) -> Dict[str, Any]:
        """Получает топ новости - не реализовано"""
        return {"error": NewsAPIError("NewsAPI.org fetcher not implemented yet")}
    
    def get_sources(self, **kwargs) -> Dict[str, Any]:
        """Получает список доступных источников - не реализовано"""
        return {"error": NewsAPIError("NewsAPI.org fetcher not implemented yet")} 