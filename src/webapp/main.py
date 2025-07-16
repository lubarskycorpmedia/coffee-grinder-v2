# /src/webapp/main.py

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request, Form
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Import the news processing components
from src.services.news.fetcher_fabric import FetcherFactory
from src.services.news.news_processor import NewsProcessor
from src.services.news.exporter import GoogleSheetsExporter
from src.logger import setup_logger

app = FastAPI(title="News Aggregator API", version="1.0.0")
logger = setup_logger(__name__)

# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="src/webapp/static"), name="static")
templates = Jinja2Templates(directory="src/webapp/templates")

# Simple API key auth
API_KEY = os.getenv("API_KEY", "development_key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    """Проверка API ключа"""
    if not API_KEY or api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return True

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Проверка состояния сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": os.getenv("APP_VERSION", "dev"),
        "service": "Coffee Grinder v2"
    }

def process_news(query: str = "technology", limit: int = 50):
    """Обработка новостей в фоновом режиме"""
    try:
        logger.info(f"Starting news processing for query: {query}, limit: {limit}")
        
        # Fetch news
        fetcher = FetcherFactory.create()
        articles = fetcher.fetch(query=query, limit=limit)
        logger.info(f"Fetched {len(articles)} articles")
        
        # Deduplicate
        deduplicator = NewsDeduplicator()
        unique_articles = deduplicator.filter_duplicates(articles)
        logger.info(f"After deduplication: {len(unique_articles)} articles")
        
        # Rank
        ranker = NewsRanker()
        ranked_articles = ranker.rank_articles(unique_articles)
        logger.info(f"Ranked {len(ranked_articles)} articles")
        
        # Export
        exporter = GoogleSheetsExporter()
        success = exporter.export_news(ranked_articles)
        logger.info(f"Export {'successful' if success else 'failed'}")
        
        return {
            "success": True,
            "articles_processed": len(articles),
            "articles_unique": len(unique_articles),
            "articles_exported": len(ranked_articles)
        }
    except Exception as e:
        logger.error(f"Error processing news: {str(e)}")
        return {"success": False, "error": str(e)}

@app.post("/trigger/run")
async def trigger_run(
    background_tasks: BackgroundTasks,
    query: str = "technology",
    limit: int = 50,
    _: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """Запуск обработки новостей в фоновом режиме"""
    # Run in background to avoid timeout
    background_tasks.add_task(process_news, query, limit)
    
    return {
        "status": "processing",
        "query": query,
        "limit": limit,
        "timestamp": datetime.now().isoformat(),
        "message": "News processing started in background"
    }

@app.post("/web/trigger/run")
async def web_trigger_run(
    background_tasks: BackgroundTasks,
    query: str = Form("technology"),
    limit: int = Form(50)
) -> Dict[str, Any]:
    """Запуск обработки новостей через веб-интерфейс (без аутентификации)"""
    # Run in background to avoid timeout
    background_tasks.add_task(process_news, query, limit)
    
    return {
        "status": "processing",
        "query": query,
        "limit": limit,
        "timestamp": datetime.now().isoformat(),
        "message": "News processing started in background"
    }

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница веб-интерфейса"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "version": "1.0.0",
        "current_time": datetime.now().isoformat()
    })

@app.get("/api/info")
async def api_info():
    """Информация об API"""
    return {
        "message": "Coffee Grinder v2 News Aggregator API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "trigger": "/trigger/run",
            "api_info": "/api/info"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 