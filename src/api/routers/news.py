# /src/api/routers/news.py

import json
import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, ValidationError

from src.services.news.runner import (
    run_from_config, 
    ProgressTracker, 
    ProcessingConfig, 
    NewsProviderConfig
)
from src.logger import setup_logger


# Настройки API
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

router = APIRouter(prefix="/api/news", tags=["news"])
logger = setup_logger(__name__)


def get_api_key(api_key: str = Security(api_key_header)):
    """Проверка API ключа"""
    expected_key = os.getenv("NEWS_API_KEY", "development_key")
    if api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return api_key


class ConfigUpdateRequest(BaseModel):
    """Модель для обновления конфигурации"""
    providers: Dict[str, NewsProviderConfig]


class TriggerRequest(BaseModel):
    """Модель для запуска обработки"""
    dry_run: bool = False
    config_path: Optional[str] = None


@router.get("/config")
async def get_config(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """
    Получить текущую конфигурацию обработки новостей
    """
    config_path = "data/news_parsing_config.json"
    
    try:
        if not os.path.exists(config_path):
            logger.warning(f"Configuration file not found: {config_path}")
            return {"providers": {}}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        logger.info(f"📖 Configuration loaded from {config_path}")
        return config_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON in configuration file: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error reading configuration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading configuration: {str(e)}"
        )


@router.post("/config")
async def update_config(
    config_request: ConfigUpdateRequest,
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """
    Обновить конфигурацию обработки новостей
    """
    config_path = "data/news_parsing_config.json"
    
    try:
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Конвертируем Pydantic модели в словари
        config_data = {}
        for provider_name, provider_config in config_request.providers.items():
            config_data[provider_name] = provider_config.model_dump(exclude_none=True)
        
        # Валидируем через ProcessingConfig
        ProcessingConfig(providers=config_request.providers)
        
        # Сохраняем конфигурацию
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Configuration saved to {config_path}")
        logger.info(f"📊 Providers configured: {list(config_data.keys())}")
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "providers_count": len(config_data),
            "providers": list(config_data.keys()),
            "saved_at": datetime.now(timezone.utc).isoformat()
        }
        
    except ValidationError as e:
        logger.error(f"Configuration validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Configuration validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error saving configuration: {str(e)}"
        )


@router.get("/status")
async def get_status(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """
    Получить текущий статус обработки новостей
    """
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        progress_tracker = ProgressTracker(redis_url)
        
        progress = progress_tracker.get_progress()
        
        # Дополнительная информация
        status_info = {
            **progress,
            "service_status": "running",
            "redis_connected": True,
            "config_exists": os.path.exists("data/news_parsing_config.json")
        }
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        # Возвращаем базовый статус даже при ошибке Redis
        return {
            "state": "unknown",
            "percent": 0,
            "message": f"Error connecting to Redis: {str(e)}",
            "service_status": "running",
            "redis_connected": False,
            "config_exists": os.path.exists("data/news_parsing_config.json"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.post("/trigger")
async def trigger_processing(
    background_tasks: BackgroundTasks,
    trigger_request: TriggerRequest = TriggerRequest(),
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """
    Запустить обработку новостей в фоновом режиме
    """
    config_path = trigger_request.config_path or "data/news_parsing_config.json"
    
    # Проверяем существование конфигурации
    if not os.path.exists(config_path):
        raise HTTPException(
            status_code=400,
            detail=f"Configuration file not found: {config_path}"
        )
    
    # Проверяем, не запущен ли уже процесс
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        progress_tracker = ProgressTracker(redis_url)
        current_progress = progress_tracker.get_progress()
        
        if current_progress.get("state") == "running":
            raise HTTPException(
                status_code=409,
                detail="Processing is already running"
            )
    except Exception as e:
        logger.warning(f"Could not check current status: {str(e)}")
    
    # Запускаем обработку в фоне
    def run_processing():
        try:
            logger.info("🚀 Starting news processing in background")
            result = run_from_config(
                config_path=config_path,
                dry_run=trigger_request.dry_run,
                redis_url=redis_url
            )
            logger.info(f"✅ Processing completed: {result}")
        except Exception as e:
            logger.error(f"❌ Processing failed: {str(e)}")
    
    background_tasks.add_task(run_processing)
    
    return {
        "success": True,
        "message": "News processing started",
        "config_path": config_path,
        "dry_run": trigger_request.dry_run,
        "started_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/logs")
async def get_logs(
    lines: int = 100,
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """
    Получить последние строки логов
    """
    # Путь к файлу логов (нужно будет настроить в logger)
    log_file_paths = [
        "/app/logs/app.log",
        "/tmp/news_processing.log",
        "logs/app.log"
    ]
    
    log_content = []
    log_file_used = None
    
    # Ищем существующий файл логов
    for log_path in log_file_paths:
        if os.path.exists(log_path):
            log_file_used = log_path
            break
    
    if log_file_used:
        try:
            # Читаем последние N строк
            with open(log_file_used, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                log_content = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
        except Exception as e:
            logger.error(f"Error reading log file {log_file_used}: {str(e)}")
            return {
                "success": False,
                "error": f"Error reading log file: {str(e)}",
                "log_file": log_file_used
            }
    
    return {
        "success": True,
        "lines_requested": lines,
        "lines_returned": len(log_content),
        "log_file": log_file_used,
        "logs": [line.rstrip() for line in log_content],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.delete("/progress")
async def clear_progress(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """
    Очистить прогресс обработки (для сброса состояния)
    """
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        progress_tracker = ProgressTracker(redis_url)
        progress_tracker.clear_progress()
        
        logger.info("🧹 Progress cleared")
        
        return {
            "success": True,
            "message": "Progress cleared successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing progress: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing progress: {str(e)}"
        ) 