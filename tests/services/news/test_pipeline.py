# /tests/services/news/test_pipeline.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from src.services.news.pipeline import (
    NewsPipelineOrchestrator,
    PipelineResult,
    StageResult,
    create_news_pipeline_orchestrator
)


class TestNewsPipelineOrchestrator:
    """Тесты для NewsPipelineOrchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Фикстура для создания оркестратора"""
        with patch('src.services.news.pipeline.get_pipeline_settings'), \
             patch('src.services.news.pipeline.get_faiss_settings'), \
             patch('src.services.news.pipeline.setup_logger'):
            return NewsPipelineOrchestrator()
    
    @pytest.fixture
    def mock_active_rubrics(self):
        """Фикстура с мок-данными активных рубрик"""
        return [
            {
                "rubric": "02. Trump",
                "category": "politics",
                "query": "Trump | Mask"
            },
            {
                "rubric": "03. US",
                "category": "general",
                "query": "USA"
            },
            {
                "rubric": "05. Ukraine",
                "category": "politics",
                "query": "Ukraine | war | Zelensky"
            }
        ]
    
    @pytest.fixture
    def mock_pipeline_result(self):
        """Фикстура с мок-результатом pipeline"""
        return PipelineResult(
            success=True,
            total_stages=3,
            completed_stages=3,
            total_execution_time=10.5,
            results={
                "fetcher": StageResult(success=True, execution_time=3.0),
                "deduplication": StageResult(success=True, execution_time=4.0),
                "export": StageResult(success=True, execution_time=3.5)
            },
            errors=[]
        )
    
    @patch('src.services.news.pipeline.get_active_rubrics')
    def test_run_all_rubrics_no_active_rubrics(self, mock_get_active_rubrics, orchestrator):
        """Тест run_all_rubrics когда нет активных рубрик"""
        mock_get_active_rubrics.return_value = []
        
        results = orchestrator.run_all_rubrics()
        
        assert isinstance(results, list)
        assert len(results) == 0
        mock_get_active_rubrics.assert_called_once()
    
    @patch('src.services.news.pipeline.get_active_rubrics')
    def test_run_all_rubrics_with_active_rubrics(self, mock_get_active_rubrics, 
                                                orchestrator, mock_active_rubrics, 
                                                mock_pipeline_result):
        """Тест run_all_rubrics с активными рубриками"""
        mock_get_active_rubrics.return_value = mock_active_rubrics
        
        # Мокируем run_pipeline
        orchestrator.run_pipeline = Mock(return_value=mock_pipeline_result)
        
        results = orchestrator.run_all_rubrics(limit=5)
        
        assert isinstance(results, list)
        assert len(results) == 3
        
        # Проверяем что run_pipeline был вызван для каждой рубрики
        assert orchestrator.run_pipeline.call_count == 3
        
        # Проверяем структуру результатов
        for i, result in enumerate(results):
            assert "rubric" in result
            assert "category" in result
            assert "query" in result
            assert "pipeline_result" in result
            assert result["rubric"] == mock_active_rubrics[i]["rubric"]
            assert result["category"] == mock_active_rubrics[i]["category"]
            assert result["query"] == mock_active_rubrics[i]["query"]
            assert result["pipeline_result"] == mock_pipeline_result
    
    @patch('src.services.news.pipeline.get_active_rubrics')
    def test_run_all_rubrics_with_pipeline_error(self, mock_get_active_rubrics, 
                                                orchestrator, mock_active_rubrics):
        """Тест run_all_rubrics с ошибкой в pipeline"""
        mock_get_active_rubrics.return_value = mock_active_rubrics[:1]  # Только одна рубрика
        
        # Мокируем run_pipeline чтобы выбрасывал исключение
        orchestrator.run_pipeline = Mock(side_effect=Exception("Pipeline error"))
        
        results = orchestrator.run_all_rubrics()
        
        assert isinstance(results, list)
        assert len(results) == 1
        
        result = results[0]
        assert "error" in result
        assert result["pipeline_result"] is None
        assert "Pipeline error" in result["error"]
    
    @patch('src.services.news.pipeline.get_active_rubrics')
    def test_run_all_rubrics_parameters_passed_correctly(self, mock_get_active_rubrics, 
                                                        orchestrator, mock_active_rubrics,
                                                        mock_pipeline_result):
        """Тест что параметры правильно передаются в run_pipeline"""
        mock_get_active_rubrics.return_value = mock_active_rubrics[:1]  # Только одна рубрика
        orchestrator.run_pipeline = Mock(return_value=mock_pipeline_result)
        
        test_limit = 10
        test_language = "ru"
        
        orchestrator.run_all_rubrics(limit=test_limit, language=test_language)
        
        # Проверяем что run_pipeline был вызван с правильными параметрами
        orchestrator.run_pipeline.assert_called_once_with(
            query=mock_active_rubrics[0]["query"],
            categories=[mock_active_rubrics[0]["category"]],
            limit=test_limit,
            language=test_language
        )
    
    @patch('src.services.news.pipeline.get_active_rubrics')
    def test_run_all_rubrics_default_parameters(self, mock_get_active_rubrics, 
                                               orchestrator, mock_active_rubrics,
                                               mock_pipeline_result):
        """Тест дефолтных параметров run_all_rubrics"""
        mock_get_active_rubrics.return_value = mock_active_rubrics[:1]
        orchestrator.run_pipeline = Mock(return_value=mock_pipeline_result)
        
        orchestrator.run_all_rubrics()
        
        # Проверяем что используются дефолтные параметры
        orchestrator.run_pipeline.assert_called_once_with(
            query=mock_active_rubrics[0]["query"],
            categories=[mock_active_rubrics[0]["category"]],
            limit=5,  # дефолтный лимит
            language="en"  # дефолтный язык
        )
    
    @patch('src.services.news.pipeline.get_active_rubrics')
    def test_run_all_rubrics_mixed_success_failure(self, mock_get_active_rubrics, 
                                                  orchestrator, mock_active_rubrics,
                                                  mock_pipeline_result):
        """Тест run_all_rubrics со смешанными результатами (успех и ошибка)"""
        mock_get_active_rubrics.return_value = mock_active_rubrics[:2]
        
        # Первый вызов успешный, второй с ошибкой
        orchestrator.run_pipeline = Mock(side_effect=[
            mock_pipeline_result,
            Exception("Second pipeline error")
        ])
        
        results = orchestrator.run_all_rubrics()
        
        assert len(results) == 2
        
        # Первый результат успешный
        assert results[0]["pipeline_result"] == mock_pipeline_result
        assert "error" not in results[0]
        
        # Второй результат с ошибкой
        assert results[1]["pipeline_result"] is None
        assert "error" in results[1]
        assert "Second pipeline error" in results[1]["error"]
    
    def test_create_news_pipeline_orchestrator_factory(self):
        """Тест фабричной функции create_news_pipeline_orchestrator"""
        with patch('src.services.news.pipeline.get_pipeline_settings'), \
             patch('src.services.news.pipeline.get_faiss_settings'), \
             patch('src.services.news.pipeline.setup_logger'):
            
            orchestrator = create_news_pipeline_orchestrator(
                provider="thenewsapi",
                worksheet_name="TestSheet",
                ranking_criteria="Test criteria"
            )
            
            assert isinstance(orchestrator, NewsPipelineOrchestrator)
            assert orchestrator.provider == "thenewsapi"
            assert orchestrator.worksheet_name == "TestSheet"
            assert orchestrator.ranking_criteria == "Test criteria"
    
    def test_orchestrator_initialization(self):
        """Тест инициализации оркестратора"""
        with patch('src.services.news.pipeline.get_pipeline_settings'), \
             patch('src.services.news.pipeline.get_faiss_settings'), \
             patch('src.services.news.pipeline.setup_logger'):
            
            orchestrator = NewsPipelineOrchestrator(
                provider="newsapi",
                worksheet_name="CustomSheet"
            )
            
            assert orchestrator.provider == "newsapi"
            assert orchestrator.worksheet_name == "CustomSheet"
            assert orchestrator._fetcher is None
            assert orchestrator._news_chain is None
            assert orchestrator._exporter is None 