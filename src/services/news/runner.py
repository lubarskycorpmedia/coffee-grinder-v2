# /src/services/news/runner.py

import json
import fcntl
import time
import os
import asyncio
from typing import Dict, Any, Optional, Callable, Union, List
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path

import redis

from src.config import get_news_providers_settings, get_ai_settings, get_google_settings
from src.utils.input_validator import validate_api_input
from src.logger import setup_logger
from src.services.news.pipeline import NewsPipelineOrchestrator


def load_config_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Загрузить конфигурацию из JSON файла с валидацией безопасности
    
    Args:
        file_path: Путь к файлу конфигурации
        
    Returns:
        Список запросов в формате [{"provider": "name", "config": {...}}]
        
    Raises:
        FileNotFoundError: Если файл не найден
        json.JSONDecodeError: Если JSON невалидный
        ValueError: Если данные не прошли валидацию безопасности
    """
    logger = setup_logger(__name__)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # ТОЛЬКО единый формат {requests: [...]}
    if not isinstance(config_data, dict) or "requests" not in config_data:
        raise ValueError(f"Конфигурация должна быть в формате {{requests: [...]}}, получен: {type(config_data)}")
    
    logger.info("✅ Единый формат конфигурации {requests: [...]}")
    requests_list = config_data["requests"]
    
    if not isinstance(requests_list, list):
        raise ValueError(f"Поле 'requests' должно быть массивом, получен: {type(requests_list)}")
    
    # Валидируем данные на безопасность
    validated_list = validate_api_input(requests_list)
    
    return validated_list


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
                       processed_providers: Optional[list] = None,
                       start_time_override: Optional[float] = None):
        """Обновить прогресс в Redis"""
        current_time = datetime.now(timezone.utc)
        progress_data = {
            "state": state,  # idle|running|completed|error
            "percent": percent,
            "current_provider": current_provider or "",
            "processed_providers": json.dumps(processed_providers or []),
            "message": message,
            "timestamp": current_time.isoformat(),
        }
        
        current_progress = self.get_progress()
        
        # Устанавливаем время начала
        if state == "running":
            # Если передан start_time_override - используем его
            if start_time_override is not None:
                override_time = datetime.fromtimestamp(start_time_override, timezone.utc)
                progress_data["start_time"] = override_time.isoformat()
            else:
                # Если предыдущий статус был completed/error/idle - это новый запуск
                prev_state = current_progress.get("state", "idle")
                if prev_state in ["completed", "error", "idle"]:
                    # Новый запуск - устанавливаем новое время начала
                    progress_data["start_time"] = current_time.isoformat()
                else:
                    # Продолжение работы - сохраняем существующий start_time
                    progress_data["start_time"] = current_progress.get("start_time", current_time.isoformat())
        
        # Устанавливаем время окончания и длительность
        if state in ["completed", "error"] and "start_time" in current_progress:
            progress_data["end_time"] = current_time.isoformat()
            
            # Вычисляем длительность
            try:
                start_time_str = current_progress["start_time"]
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                duration_seconds = (current_time - start_time).total_seconds()
                progress_data["duration"] = round(duration_seconds, 2)
            except (ValueError, KeyError) as e:
                # Если не удалось вычислить длительность, просто логируем
                pass
        
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


def run_news_parsing_from_config(
    config_path: str = "data/news_parsing_config.json",
    progress_callback: Optional[Callable] = None,
    test_without_export: bool = False,
    redis_url: str = "redis://localhost:6379"
) -> Dict[str, Any]:
    """
    Унифицированная точка входа для запуска обработки новостей
    
    Args:
        config_path: Путь к JSON файлу конфигурации
        progress_callback: Функция для отслеживания прогресса (опционально)
        test_without_export: Режим тестирования без экспорта в Google Sheets
        redis_url: URL Redis для tracking прогресса
        
    Returns:
        Словарь с результатами обработки
    """
    # ЗАМЕР ВРЕМЕНИ НАЧИНАЕТСЯ СРАЗУ ПРИ ЗАПУСКЕ
    start_time = time.time()
    
    logger = setup_logger(__name__)
    progress_tracker = ProgressTracker(redis_url)
    lock_file = "/tmp/news_processing.lock"
    
    try:
        with file_lock(lock_file):
            logger.info("🔐 Получена блокировка процесса")
            
            # МАРКЕР НАЧАЛА ОБРАБОТКИ
            logger.info("🚀 Pipeline started - Начинается обработка новостей")
            
            # Загружаем конфигурацию
            try:
                config_requests = load_config_from_file(config_path)
                logger.info(f"📝 Загружена конфигурация из {config_path}")
                logger.info(f"📊 Найдено запросов: {len(config_requests)}")
                provider_names = [req["provider"] for req in config_requests]
                logger.info(f"📋 Провайдеры в запросах: {provider_names}")
            except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
                error_msg = f"Ошибка загрузки конфигурации: {str(e)}"
                logger.error(error_msg)
                progress_tracker.update_progress("error", 0, message=error_msg)
                logger.error("💥 Pipeline completed - Завершена обработка с ошибкой конфигурации")
                return {"success": False, "error": error_msg}
            
            # Инициализация прогресса
            progress_tracker.update_progress(
                "running", 
                0, 
                message="Инициализация обработки...",
                start_time_override=start_time
            )
            
            total_requests = len(config_requests)
            processed_requests = []
            all_results = {}
            
            for i, request in enumerate(config_requests):
                provider_name = request["provider"]
                provider_config = request["config"]
                
                current_percent = int((i / total_requests) * 100)
                request_id = f"{provider_name}_{i+1}"
                
                progress_tracker.update_progress(
                    "running",
                    current_percent,
                    current_provider=provider_name,
                    processed_providers=processed_requests,
                    message=f"Обработка запроса {i+1}/{total_requests} для {provider_name}..."
                )
                
                if progress_callback:
                    progress_callback(current_percent, f"{provider_name} (запрос {i+1})")
                
                # МАРКЕР НАЧАЛА ОБРАБОТКИ ПРОВАЙДЕРА
                logger.info(f"▶️ Starting - Начинается обработка провайдера: {provider_name}")
                
                try:
                    # Создаем оркестратор для конкретного провайдера
                    orchestrator = NewsPipelineOrchestrator(provider=provider_name)
                    
                    # Получаем параметры конфигурации
                    config_dict = provider_config
                    query = config_dict.get("query", "")
                    category = config_dict.get("category", "")
                    limit = config_dict.get("limit", 50)
                    language = config_dict.get("language", "en")
                    published_after = config_dict.get("published_after")
                    published_before = config_dict.get("published_before")
                    
                    # Запускаем pipeline (NOTE: test_without_export не поддерживается в текущей версии)
                    result = orchestrator.run_pipeline(
                        query=query,
                        categories=[category] if category else [],
                        limit=limit,
                        language=language,
                        published_after=published_after,
                        published_before=published_before
                    )
                    all_results[request_id] = {"success": result.success, "result": result}
                    
                    if result.success:
                        logger.info(f"✅ Запрос {request_id} обработан успешно")
                        # МАРКЕР УСПЕШНОГО ЗАВЕРШЕНИЯ ПРОВАЙДЕРА
                        logger.info(f"✅ Completed - Завершена обработка запроса: {request_id}")
                    else:
                        logger.error(f"❌ Ошибка обработки запроса {request_id}: {result.errors}")
                        # МАРКЕР ЗАВЕРШЕНИЯ ПРОВАЙДЕРА С ОШИБКОЙ
                        logger.error(f"❌ Completed - Завершена обработка запроса с ошибками: {request_id}")
                    
                    processed_requests.append(request_id)
                    
                except Exception as e:
                    error_msg = f"Ошибка обработки {request_id}: {str(e)}"
                    logger.error(error_msg)
                    all_results[request_id] = {"success": False, "error": error_msg}
                    # МАРКЕР ЗАВЕРШЕНИЯ ПРОВАЙДЕРА С ИСКЛЮЧЕНИЕМ
                    logger.error(f"💥 Completed - Завершена обработка запроса с исключением: {request_id}")
                    processed_requests.append(request_id)
            
            # Финальный прогресс
            total_success = all([r.get("success", False) for r in all_results.values()])
            final_state = "completed" if total_success else "error"
            
            progress_tracker.update_progress(
                final_state,
                100,
                processed_providers=processed_requests,
                message="Обработка завершена" if total_success else "Обработка завершена с ошибками"
            )
            
            if progress_callback:
                progress_callback(100, None)
            
            # МАРКЕР ФИНАЛЬНОГО ЗАВЕРШЕНИЯ
            if total_success:
                logger.info("🏁 Pipeline finished - Завершение pipeline: все провайдеры обработаны успешно")
            else:
                logger.error("🚩 Pipeline finished - Завершение pipeline: обработка завершена с ошибками")
            
            return {
                "success": total_success,
                "providers_processed": len(processed_requests),
                "total_providers": total_requests,
                "results": all_results
            }
            
    except RuntimeError as e:
        error_msg = str(e)
        logger.error(f"🔒 {error_msg}")
        progress_tracker.update_progress("error", 0, message=error_msg)
        # МАРКЕР ЗАВЕРШЕНИЯ С ОШИБКОЙ БЛОКИРОВКИ
        logger.error("🔒 Pipeline completed - Завершена обработка: ошибка блокировки процесса")
        return {"success": False, "error": error_msg}
    
    except Exception as e:
        error_msg = f"Критическая ошибка: {str(e)}"
        logger.error(f"💥 {error_msg}")
        progress_tracker.update_progress("error", 0, message=error_msg)
        # МАРКЕР ЗАВЕРШЕНИЯ С КРИТИЧЕСКОЙ ОШИБКОЙ
        logger.error("💥 Pipeline completed - Завершена обработка: критическая ошибка")
        return {"success": False, "error": error_msg}


def run_news_parsing_sync(
    config_path: str = "data/news_parsing_config.json",
    test_without_export: bool = False,
    redis_url: str = "redis://localhost:6379"
) -> Dict[str, Any]:
    """
    Синхронная обёртка для использования в cron
    """
    return run_news_parsing_from_config(
        config_path=config_path,
        test_without_export=test_without_export,
        redis_url=redis_url
    )


 