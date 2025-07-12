# /src/services/news/rubrics_config.py

import json
from typing import List, Dict, Any
from src.logger import setup_logger


# Конфигурация рубрик в формате JSON
RUBRICS_CONFIG = [
    {
        "rubric": "01. Big picture",
        "category": "general",
        "query": "Big picture"
    },
    {
        "rubric": "02. Trump",
        "category": "politics",
        "query": "Trump"
    },
    # {
    #     "rubric": "02. Trump",
    #     "category": "politics",
    #     "query": "Mask"
    # },
    # {
    #     "rubric": "03. US",
    #     "category": "general", 
    #     "query": "USA"
    # },
    # {
    #     "rubric": "04. Left reaction",
    #     "category": "general",
    #     "query": ""
    # },
    # {
    #     "rubric": "05. Ukraine",
    #     "category": "politics",
    #     "query": "Ukraine"
    # },
    # {
    #     "rubric": "05. Ukraine",
    #     "category": "politics",
    #     "query": "war"
    # },
    # {
    #     "rubric": "05. Ukraine",
    #     "category": "general",
    #     "query": "war"
    # },
    # {
    #     "rubric": "06. Coffee grounds",
    #     "category": "politics",
    #     "query": "Zelensky"
    # },
    # {
    #     "rubric": "07. World",
    #     "category": "general",
    #     "query": "World | Israil | Iran | "
    # },
    # {
    #     "rubric": "08. Marasmus",
    #     "category": "entertainment",
    #     "query": "Marasmus"
    # },
    # {
    #     "rubric": "09. Blitz",
    #     "category": "general",
    #     "query": "Blitz"
    # },
    # {
    #     "rubric": "10. Tech",
    #     "category": "tech",
    #     "query": "tech | AI"
    # },
    # {
    #     "rubric": "11. Crazy",
    #     "category": "general",
    #     "query": "Crazy"
    # },
    # {
    #     "rubric": "other",
    #     "category": "general",
    #     "query": "Rubio"
    # }
]


def get_rubrics_config() -> List[Dict[str, Any]]:
    """
    Возвращает конфигурацию рубрик новостей
    
    Returns:
        Список словарей с конфигурацией рубрик
    """
    logger = setup_logger(__name__)
    logger.debug(f"Loading rubrics config with {len(RUBRICS_CONFIG)} rubrics")
    
    return RUBRICS_CONFIG


def get_active_rubrics() -> List[Dict[str, Any]]:
    """
    Возвращает только активные рубрики (с непустыми category и query)
    
    Returns:
        Список словарей с активными рубриками
    """
    logger = setup_logger(__name__)
    
    active_rubrics = []
    for rubric in RUBRICS_CONFIG:
        category = rubric.get("category", "").strip()
        query = rubric.get("query", "").strip()
        
        if category and query:
            active_rubrics.append(rubric)
    
    logger.info(f"Found {len(active_rubrics)} active rubrics out of {len(RUBRICS_CONFIG)} total")
    return active_rubrics


def validate_rubric_config(rubric: Dict[str, Any]) -> bool:
    """
    Валидирует структуру конфигурации рубрики
    
    Args:
        rubric: Словарь с конфигурацией рубрики
        
    Returns:
        True если структура валидна
    """
    required_fields = ["rubric", "category", "query"]
    
    for field in required_fields:
        if field not in rubric:
            return False
        if not isinstance(rubric[field], str):
            return False
    
    return True


def get_rubric_by_name(rubric_name: str) -> Dict[str, Any]:
    """
    Возвращает конфигурацию рубрики по имени
    
    Args:
        rubric_name: Имя рубрики
        
    Returns:
        Словарь с конфигурацией рубрики или пустой словарь если не найдена
    """
    for rubric in RUBRICS_CONFIG:
        if rubric.get("rubric") == rubric_name:
            return rubric
    
    return {} 