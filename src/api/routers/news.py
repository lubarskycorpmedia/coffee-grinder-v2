# /src/api/routers/news.py

import json
import os
import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, ValidationError

from src.services.news.runner import (
    run_news_parsing_from_config, 
    ProgressTracker
)
from src.services.news.fetcher_fabric import FetcherFactory
from src.utils.input_validator import validate_api_input
from src.logger import setup_logger
from src.services.news.fetcher_fabric import FetcherFactory


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


class TriggerRequest(BaseModel):
    """Модель для запуска обработки"""
    test_without_export: bool = False
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
            return {"requests": []}
        
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
    config_data: Dict[str, Any],
    api_key: str = Depends(get_api_key)
) -> Dict[str, Any]:
    """
    Обновить конфигурацию обработки новостей
    """
    config_path = "data/news_parsing_config.json"
    
    try:
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        logger.info(f"🔍 Получены данные от фронтенда: {config_data}")
        logger.info(f"📊 Тип полученных данных: {type(config_data)}")
        
        # Извлекаем массив requests из обёртки
        requests_list = config_data.get("requests", [])
        logger.info(f"📋 Количество запросов: {len(requests_list)}")
        
        # Нормализуем данные: undefined, null, NaN -> ""
        normalized_requests = []
        for i, request in enumerate(requests_list):
            provider_name = request.get("provider", "")
            provider_config = request.get("config", {})
            
            # Нормализуем конфигурацию провайдера
            normalized_config = {}
            for key, value in provider_config.items():
                # Приводим undefined, null, NaN к пустой строке
                if value is None:
                    normalized_value = ""
                elif isinstance(value, float) and (str(value).lower() in ("nan", "none") or value != value):  # NaN check
                    normalized_value = ""
                else:
                    normalized_value = str(value) if value is not None else ""
                
                normalized_config[key] = normalized_value
            
            normalized_requests.append({
                "provider": provider_name,
                "config": normalized_config
            })
            
            logger.info(f"🏢 Запрос {i+1} для {provider_name}: {len(normalized_config)} полей - {list(normalized_config.keys())}")
        
        # Валидируем входящие данные на безопасность (БЕЗ фильтрации пустых полей)
        try:
            validated_data = validate_api_input(normalized_requests)
            logger.info(f"✅ Данные прошли валидацию безопасности: количество валидных запросов {len(validated_data)}")
        except Exception as validation_error:
            logger.error(f"❌ Ошибка валидации безопасности: {str(validation_error)}")
            raise HTTPException(
                status_code=400,
                detail=f"Security validation failed: {str(validation_error)}"
            )
        
        # ФИЛЬТРАЦИЯ ПУСТЫХ ПОЛЕЙ - ТОЛЬКО ЗДЕСЬ, ПЕРЕД ЗАПИСЬЮ В ФАЙЛ
        final_requests = []
        for i, request in enumerate(validated_data):
            provider_name = request["provider"]
            provider_config = request["config"]
            
            logger.info(f"🔧 Обрабатываем запрос {i+1} для {provider_name}: {provider_config}")
            
            # Фильтруем только пустые поля
            filtered_config = {}
            for key, value in provider_config.items():
                # Исключаем только пустые строки
                if isinstance(value, str) and value.strip() == "":
                    continue
                filtered_config[key] = value
            
            logger.info(f"🧹 Отфильтрованная конфигурация для запроса {i+1} ({provider_name}): {filtered_config}")
            
            # Упорядочиваем поля согласно исходному порядку в JSON файлах параметров
            ordered_config = get_ordered_config(provider_name, filtered_config)
            logger.info(f"📋 Упорядоченная конфигурация для запроса {i+1} ({provider_name}): {list(ordered_config.keys())}")
            
            # Сохраняем запрос даже если конфигурация пустая (по требованию)
            final_requests.append({
                "provider": provider_name,
                "config": ordered_config
            })
        
        logger.info(f"💾 Сохраняем финальную конфигурацию: {len(final_requests)} запросов")
        
        # Сохраняем конфигурацию в едином формате с обёрткой
        config_to_save = {"requests": final_requests}
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, ensure_ascii=False, indent=2, sort_keys=False)
        
        logger.info(f"💾 Configuration saved to {config_path}")
        
        # Подсчитываем статистику провайдеров
        provider_counts = {}
        for request in final_requests:
            provider = request["provider"]
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        logger.info(f"📊 Запросы по провайдерам: {provider_counts}")
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "requests_count": len(final_requests),
            "provider_counts": provider_counts,
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
    # ЗАМЕР ВРЕМЕНИ НАЧИНАЕТСЯ СРАЗУ ПРИ ПОЛУЧЕНИИ ЗАПРОСА
    start_time = time.time()
    
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
            result = run_news_parsing_from_config(
                config_path=config_path,
                test_without_export=trigger_request.test_without_export,
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
        "test_without_export": trigger_request.test_without_export,
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


@router.get("/available_parameter_values")
async def get_available_parameter_values() -> Dict[str, Any]:
    """
    Получить параметры (категории и языки) для всех включенных провайдеров
    """
    try:
        # Получаем список включенных провайдеров
        enabled_providers = FetcherFactory.get_enabled_providers()
        
        parameters = {}
        
        for provider_name in enabled_providers:
            try:
                # Создаем экземпляр fetcher'а для провайдера
                fetcher = FetcherFactory.create_fetcher_from_config(provider_name)
                
                # Получаем категории и языки
                categories = fetcher.get_categories()
                languages = fetcher.get_languages()
                
                parameters[provider_name] = {
                    "categories": categories,
                    "languages": languages
                }
                
                logger.debug(f"✅ Parameters loaded for provider: {provider_name}")
                
            except Exception as provider_error:
                error_message = f"Failed to load parameters for {provider_name}: {str(provider_error)}"
                logger.warning(error_message)
                
                # Устанавливаем пустые списки для провайдера с ошибкой
                parameters[provider_name] = {
                    "categories": [],
                    "languages": []
                }
        
        logger.info(f"📋 Parameters loaded for {len(enabled_providers)} providers")
        
        return parameters
        
    except Exception as e:
        logger.error(f"Error loading parameters: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading parameters: {str(e)}"
        )


@router.get("/provider_parameters")
async def get_provider_parameters() -> Dict[str, Any]:
    """
    Получить параметры форм для всех включенных провайдеров из их JSON файлов
    
    Returns:
        Словарь в формате:
        {
            "thenewsapi_com": {
                "url": "https://api.thenewsapi.com/v1/news/top",
                "fields": {
                    "search": "Поисковый запрос",
                    "categories": "Категории"
                }
            }
        }
    """
    try:
        # Получаем список включенных провайдеров
        enabled_providers = FetcherFactory.get_enabled_providers()
        
        parameters = {}
        
        for provider_name in enabled_providers:
            try:
                # Создаем экземпляр fetcher'а для провайдера
                fetcher = FetcherFactory.create_fetcher_from_config(provider_name)
                
                # Получаем параметры из JSON файла (теперь это Dict с url и fields)
                provider_parameters = fetcher.get_provider_parameters()
                
                parameters[provider_name] = provider_parameters
                
                fields_count = len(provider_parameters.get('fields', {}))
                logger.debug(f"✅ Provider parameters loaded for: {provider_name} ({fields_count} fields, URL: {provider_parameters.get('url', 'N/A')})")
                
            except Exception as provider_error:
                error_message = f"Failed to load provider parameters for {provider_name}: {str(provider_error)}"
                logger.warning(error_message)
                
                # Устанавливаем пустую структуру для провайдера с ошибкой
                parameters[provider_name] = {
                    "url": "",
                    "fields": {}
                }
        
        logger.info(f"📋 Provider parameters loaded for {len(enabled_providers)} providers")
        
        return parameters
        
    except Exception as e:
        logger.error(f"Error loading provider parameters: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading provider parameters: {str(e)}"
        ) 


@router.post("/test-validator")
async def test_validator(
    data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Тестовый эндпоинт для проверки валидатора
    """
    try:
        logger.info(f"🔍 Тест валидатора - входные данные: {data}")
        validated = validate_api_input(data)
        logger.info(f"✅ Тест валидатора - валидированные данные: {validated}")
        
        return {
            "success": True,
            "original": data,
            "validated": validated
        }
    except Exception as e:
        logger.error(f"❌ Тест валидатора - ошибка: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "original": data
        } 


def get_ordered_config(provider_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Упорядочить поля конфигурации согласно исходному порядку в JSON файлах параметров
    
    Args:
        provider_name: Имя провайдера
        config: Конфигурация для упорядочивания
        
    Returns:
        Упорядоченная конфигурация с сохранением исходного порядка полей
    """
    try:
        # Получаем порядок полей из JSON файла параметров провайдера
        fetcher = FetcherFactory.create_fetcher_from_config(provider_name)
        provider_params = fetcher.get_provider_parameters()
        field_order = list(provider_params.get("fields", {}).keys())
        
        # Создаем упорядоченную конфигурацию
        ordered_config = {}
        
        # Сначала добавляем поля в порядке из JSON файла
        for field_name in field_order:
            if field_name in config:
                ordered_config[field_name] = config[field_name]
        
        # Затем добавляем любые дополнительные поля
        for field_name, value in config.items():
            if field_name not in ordered_config:
                ordered_config[field_name] = value
        
        logger.debug(f"📋 Упорядочены поля для {provider_name}: {list(ordered_config.keys())}")
        return ordered_config
        
    except Exception as e:
        logger.warning(f"⚠️ Не удалось упорядочить поля для {provider_name}: {str(e)}")
        # Возвращаем исходную конфигурацию если не удалось упорядочить
        return config 