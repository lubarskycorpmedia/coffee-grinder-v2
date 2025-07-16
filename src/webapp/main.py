# /src/webapp/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
from typing import Dict, Any

from src.api.routers.news import router as news_router
from src.logger import setup_logger

app = FastAPI(
    title="Coffee Grinder v2 API", 
    version="2.0.0",
    description="AI-powered news processing system API"
)

logger = setup_logger(__name__)

# CORS middleware для React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005", "http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(news_router)

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Проверка состояния сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": os.getenv("APP_VERSION", "2.0.0"),
        "service": "Coffee Grinder v2",
        "mode": "API-only (React frontend on port 3005)"
    }

@app.get("/")
async def root() -> Dict[str, Any]:
    """Корневой эндпоинт с информацией о сервисе"""
    return {
        "message": "Coffee Grinder v2 API",
        "description": "AI-powered news processing system",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "frontend": "React app running on port 3005"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 