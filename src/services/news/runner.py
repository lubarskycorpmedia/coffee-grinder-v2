# /src/services/news/runner.py

import json
import fcntl
import time
import os
import asyncio
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path

import redis
from pydantic import BaseModel, ValidationError

from src.config import get_news_providers_settings, get_ai_settings, get_google_settings
from src.logger import setup_logger
from src.services.news.pipeline import NewsPipelineOrchestrator


class NewsProviderConfig(BaseModel):
    """Схема конфигурации для провайдера новостей"""
    query: Optional[str] = None
    category: Optional[str] = None
    published_at: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    language: Optional[str] = "en"
    limit: Optional[int] = 50
    country: Optional[str] = None
    timeframe: Optional[str] = None


class ProcessingConfig(BaseModel):
    """Полная конфигурация обработки новостей"""
    providers: Dict[str, NewsProviderConfig]
    
    @classmethod
    def from_json_file(cls, file_path: str) -> "ProcessingConfig":
        """Загрузить конфигурацию из JSON файла"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Конвертируем корневые ключи в providers
        providers = {}
        for provider_name, config_data in data.items():
            providers[provider_name] = NewsProviderConfig(**config_data)
        
        return cls(providers=providers)


class ProgressTracker:
    """Отслеживание прогресса в Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.key = "news_processing_progress"
        
    def update_progress(self, 
                       state: str,
                       percent: int = 0,
                       current_provider: Optional[str] = None,
                       message: str = "",
                       processed_providers: Optional[list] = None):
        """Обновить прогресс в Redis"""
        progress_data = {
            "state": state,  # idle|running|completed|error
            "percent": percent,
            "current_provider": current_provider or "",
            "processed_providers": json.dumps(processed_providers or []),
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        if state == "running" and "start_time" not in self.get_progress():
            progress_data["start_time"] = datetime.now(timezone.utc).isoformat()
        
        self.redis_client.hset(self.key, mapping=progress_data)
        
    def get_progress(self) -> Dict[str, Any]:
        """Получить текущий прогресс"""
        data = self.redis_client.hgetall(self.key)
        if not data:
            return {
                "state": "idle",
                "percent": 0,
                "current_provider": "",
                "processed_providers": [],
                "message": "Готов к запуску",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Конвертируем processed_providers обратно в список
        if "processed_providers" in data:
            try:
                data["processed_providers"] = json.loads(data["processed_providers"])
            except (json.JSONDecodeError, TypeError):
                data["processed_providers"] = []
        
        return data
    
    def clear_progress(self):
        """Очистить прогресс"""
        self.redis_client.delete(self.key)


@contextmanager
def file_lock(lock_file: str, timeout: int = 300):
    """
    Контекстный менеджер для файловой блокировки
    
    Args:
        lock_file: Путь к файлу блокировки
        timeout: Таймаут в секундах
    """
    lock_path = Path(lock_file)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    
    start_time = time.time()
    
    while True:
        try:
            with open(lock_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                f.write(f"PID: {os.getpid()}\nStarted: {datetime.now(timezone.utc).isoformat()}\n")
                f.flush()
                
                try:
                    yield
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                break
                
        except IOError:
            if time.time() - start_time > timeout:
                raise RuntimeError(f"Could not acquire lock within {timeout} seconds. Process may be already running.")
            time.sleep(1)


def run_from_config(
    config_path: str = "data/news_parsing_config.json",
    progress_callback: Optional[Callable] = None,
    dry_run: bool = False,
    redis_url: str = "redis://localhost:6379"
) -> Dict[str, Any]:
    """
    Унифицированная точка входа для запуска обработки новостей
    
    Args:
        config_path: Путь к JSON файлу конфигурации
        progress_callback: Функция для отслеживания прогресса (опционально)
        dry_run: Режим проверки без экспорта
        redis_url: URL Redis для tracking прогресса
        
    Returns:
        Словарь с результатами обработки
    """
    logger = setup_logger(__name__)
    progress_tracker = ProgressTracker(redis_url)
    lock_file = "/tmp/news_processing.lock"
    
    try:
        with file_lock(lock_file):
            logger.info("🔐 Получена блокировка процесса")
            
            # Загружаем конфигурацию
            try:
                config = ProcessingConfig.from_json_file(config_path)
                logger.info(f"📝 Загружена конфигурация из {config_path}")
                logger.info(f"📊 Найдено провайдеров: {list(config.providers.keys())}")
            except (FileNotFoundError, ValidationError, json.JSONDecodeError) as e:
                error_msg = f"Ошибка загрузки конфигурации: {str(e)}"
                logger.error(error_msg)
                progress_tracker.update_progress("error", 0, message=error_msg)
                return {"success": False, "error": error_msg}
            
            # Инициализация прогресса
            progress_tracker.update_progress(
                "running", 
                0, 
                message="Инициализация обработки..."
            )
            
            total_providers = len(config.providers)
            processed_providers = []
            all_results = {}
            
            for i, (provider_name, provider_config) in enumerate(config.providers.items()):
                current_percent = int((i / total_providers) * 100)
                progress_tracker.update_progress(
                    "running",
                    current_percent,
                    current_provider=provider_name,
                    processed_providers=processed_providers,
                    message=f"Обработка провайдера {provider_name}..."
                )
                
                if progress_callback:
                    progress_callback(current_percent, provider_name)
                
                logger.info(f"🔄 Обработка провайдера: {provider_name}")
                
                try:
                    # Создаем оркестратор для конкретного провайдера
                    orchestrator = NewsPipelineOrchestrator(provider=provider_name)
                    
                    # Получаем параметры конфигурации
                    config_dict = provider_config.model_dump(exclude_none=True)
                    query = config_dict.get("query", "")
                    category = config_dict.get("category", "")
                    limit = config_dict.get("limit", 50)
                    language = config_dict.get("language", "en")
                    
                    # Запускаем pipeline (NOTE: dry_run не поддерживается в текущей версии)
                    result = orchestrator.run_pipeline(
                        query=query,
                        categories=[category] if category else [],
                        limit=limit,
                        language=language
                    )
                    all_results[provider_name] = {"success": result.success, "result": result}
                    
                    if result.success:
                        logger.info(f"✅ Провайдер {provider_name} обработан успешно")
                    else:
                        logger.error(f"❌ Ошибка обработки провайдера {provider_name}: {result.errors}")
                    
                    processed_providers.append(provider_name)
                    
                except Exception as e:
                    error_msg = f"Ошибка обработки {provider_name}: {str(e)}"
                    logger.error(error_msg)
                    all_results[provider_name] = {"success": False, "error": error_msg}
            
            # Финальный прогресс
            total_success = all([r.get("success", False) for r in all_results.values()])
            final_state = "completed" if total_success else "error"
            
            progress_tracker.update_progress(
                final_state,
                100,
                processed_providers=processed_providers,
                message="Обработка завершена" if total_success else "Обработка завершена с ошибками"
            )
            
            if progress_callback:
                progress_callback(100, None)
            
            logger.info("🏁 Обработка завершена")
            
            return {
                "success": total_success,
                "providers_processed": len(processed_providers),
                "total_providers": total_providers,
                "results": all_results
            }
            
    except RuntimeError as e:
        error_msg = str(e)
        logger.error(f"🔒 {error_msg}")
        progress_tracker.update_progress("error", 0, message=error_msg)
        return {"success": False, "error": error_msg}
    
    except Exception as e:
        error_msg = f"Критическая ошибка: {str(e)}"
        logger.error(f"💥 {error_msg}")
        progress_tracker.update_progress("error", 0, message=error_msg)
        return {"success": False, "error": error_msg}


def run_from_config_sync(
    config_path: str = "data/news_parsing_config.json",
    dry_run: bool = False,
    redis_url: str = "redis://localhost:6379"
) -> Dict[str, Any]:
    """
    Синхронная обёртка для использования в cron
    """
    return asyncio.run(run_from_config(
        config_path=config_path,
        dry_run=dry_run,
        redis_url=redis_url
    ))


# Для обратной совместимости с существующим кодом
async def run_pipeline_from_args(args) -> Dict[str, Any]:
    """
    Запуск pipeline из аргументов командной строки (для совместимости)
    """
    # Создаем временную конфигурацию из аргументов
    temp_config = {
        "thenewsapi": {  # Дефолтный провайдер
            "query": getattr(args, 'query', None),
            "category": getattr(args, 'category', None),
            "language": getattr(args, 'language', 'en'),
            "limit": getattr(args, 'limit', 50)
        }
    }
    
    # Удаляем None значения
    temp_config["thenewsapi"] = {k: v for k, v in temp_config["thenewsapi"].items() if v is not None}
    
    # Создаем временный файл конфигурации
    temp_config_path = "/tmp/temp_news_config.json"
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        json.dump(temp_config, f, ensure_ascii=False, indent=2)
    
    try:
        return await run_from_config(
            config_path=temp_config_path,
            dry_run=getattr(args, 'dry_run', False)
        )
    finally:
        # Очищаем временный файл
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path) 