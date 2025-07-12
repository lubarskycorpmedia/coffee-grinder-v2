# /tests/services/news/test_rubrics_config.py

import pytest
from typing import Dict, Any, List

from src.services.news.rubrics_config import (
    get_rubrics_config,
    get_active_rubrics,
    validate_rubric_config,
    get_rubric_by_name,
    RUBRICS_CONFIG
)


class TestRubricsConfig:
    """Тесты для конфигурации рубрик"""
    
    def test_get_rubrics_config_returns_list(self):
        """Тест что get_rubrics_config возвращает список"""
        config = get_rubrics_config()
        assert isinstance(config, list)
        assert len(config) > 0
    
    def test_get_rubrics_config_structure(self):
        """Тест структуры конфигурации рубрик"""
        config = get_rubrics_config()
        
        # Проверяем что в конфигурации есть ожидаемые рубрики
        assert len(config) == 2  # Только активные рубрики в тестовом режиме
        
        # Проверяем структуру каждой рубрики
        for rubric in config:
            assert isinstance(rubric, dict)
            assert "rubric" in rubric
            assert "category" in rubric
            assert "query" in rubric
            assert isinstance(rubric["rubric"], str)
            assert isinstance(rubric["category"], str)
            assert isinstance(rubric["query"], str)
    
    def test_get_active_rubrics_filters_correctly(self):
        """Тест что get_active_rubrics правильно фильтрует рубрики"""
        active_rubrics = get_active_rubrics()
        
        assert isinstance(active_rubrics, list)
        
        # Проверяем что все активные рубрики имеют непустые category и query
        for rubric in active_rubrics:
            assert rubric["category"].strip() != ""
            assert rubric["query"].strip() != ""
    
    def test_get_active_rubrics_expected_count(self):
        """Тест ожидаемого количества активных рубрик"""
        active_rubrics = get_active_rubrics()
        
        # Подсчитываем ожидаемое количество активных рубрик
        expected_active = []
        for rubric in RUBRICS_CONFIG:
            if rubric["category"].strip() and rubric["query"].strip():
                expected_active.append(rubric)
        
        assert len(active_rubrics) == len(expected_active)
    
    def test_validate_rubric_config_valid(self):
        """Тест валидации правильной конфигурации рубрики"""
        valid_rubric = {
            "rubric": "Test Rubric",
            "category": "general",
            "query": "test query"
        }
        
        assert validate_rubric_config(valid_rubric) is True
    
    def test_validate_rubric_config_missing_fields(self):
        """Тест валидации с отсутствующими полями"""
        invalid_rubric = {
            "rubric": "Test Rubric",
            "category": "general"
            # отсутствует query
        }
        
        assert validate_rubric_config(invalid_rubric) is False
    
    def test_validate_rubric_config_wrong_types(self):
        """Тест валидации с неправильными типами данных"""
        invalid_rubric = {
            "rubric": "Test Rubric",
            "category": 123,  # должно быть строкой
            "query": "test query"
        }
        
        assert validate_rubric_config(invalid_rubric) is False
    
    def test_get_rubric_by_name_existing(self):
        """Тест получения рубрики по существующему имени"""
        rubric = get_rubric_by_name("02. Trump")
        
        assert isinstance(rubric, dict)
        assert rubric["rubric"] == "02. Trump"
        assert rubric["category"] == "politics"
        assert rubric["query"] == "Trump"
    
    def test_get_rubric_by_name_non_existing(self):
        """Тест получения рубрики по несуществующему имени"""
        rubric = get_rubric_by_name("Non-existing Rubric")
        
        assert isinstance(rubric, dict)
        assert len(rubric) == 0
    
    def test_all_rubrics_have_valid_structure(self):
        """Тест что все рубрики в конфигурации имеют валидную структуру"""
        config = get_rubrics_config()
        
        for rubric in config:
            assert validate_rubric_config(rubric) is True
    
    def test_specific_rubrics_exist(self):
        """Тест что конкретные ожидаемые рубрики существуют"""
        config = get_rubrics_config()
        rubric_names = [rubric["rubric"] for rubric in config]
        
        # Только активные рубрики в тестовом режиме
        expected_rubrics = [
            "01. Big picture",
            "02. Trump"
        ]
        
        for expected_rubric in expected_rubrics:
            assert expected_rubric in rubric_names
    
    def test_active_rubrics_are_subset_of_all(self):
        """Тест что активные рубрики являются подмножеством всех рубрик"""
        all_rubrics = get_rubrics_config()
        active_rubrics = get_active_rubrics()
        
        all_rubric_names = [rubric["rubric"] for rubric in all_rubrics]
        active_rubric_names = [rubric["rubric"] for rubric in active_rubrics]
        
        for active_name in active_rubric_names:
            assert active_name in all_rubric_names 