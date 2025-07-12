# /tests/services/news/test_news_processor.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.services.news.news_processor import (
    NewsProcessor,
    create_news_processor,
    NewsProcessingError
)
from src.langchain.news_chain import NewsItem


class TestNewsProcessor:
    """Тесты для NewsProcessor"""
    
    @pytest.fixture
    def sample_news_items(self):
        """Фикстура с тестовыми новостями"""
        return [
            NewsItem(
                title="Test News 1",
                description="Test description 1",
                url="http://example.com/1",
                published_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                source="Test Source",
                category="Technology",
                language="en"
            ),
            NewsItem(
                title="Test News 2",
                description="Test description 2",
                url="http://example.com/2",
                published_at=datetime(2024, 1, 2, 14, 30, 0, tzinfo=timezone.utc),
                source="Another Source",
                category="Science",
                language="en"
            )
        ]
    
    def test_init_success(self):
        """Тест успешной инициализации процессора"""
        processor = NewsProcessor(
            news_provider="thenewsapi",
            fail_on_errors=False,
            enable_deduplication=True,
            max_items_per_request=100
        )
        
        assert processor.news_provider == "thenewsapi"
        assert processor.fail_on_errors is False
        assert processor.enable_deduplication is True
        assert processor.max_items_per_request == 100
    
    @patch('src.services.news.news_processor.FetcherFactory.create_fetcher_from_config')
    def test_fetch_news_success(self, mock_create_fetcher):
        """Тест успешного получения новостей"""
        # Мокаем fetcher
        mock_fetcher = Mock()
        mock_fetcher.fetch_news.return_value = {
            "articles": [
                {
                    "title": "Test Article",
                    "description": "Test description",
                    "url": "http://example.com/test",
                    "published_at": "2024-01-01T12:00:00Z",
                    "source": "Test Source",
                    "category": "Technology"
                }
            ]
        }
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor()
        news_items = processor.fetch_news(query="test", category="technology", limit=10)
        
        assert len(news_items) == 1
        assert news_items[0].title == "Test Article"
        assert news_items[0].category == "Technology"
        mock_fetcher.fetch_news.assert_called_once_with(
            query="test",
            category="technology",
            language=None,
            limit=10
        )
    
    @patch('src.services.news.news_processor.FetcherFactory.create_fetcher_from_config')
    def test_fetch_news_error_no_fail(self, mock_create_fetcher):
        """Тест ошибки получения новостей без прерывания"""
        # Мокаем ошибку в fetcher
        mock_fetcher = Mock()
        mock_fetcher.fetch_news.side_effect = Exception("API Error")
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor(fail_on_errors=False)
        news_items = processor.fetch_news()
        
        assert news_items == []
    
    @patch('src.services.news.news_processor.FetcherFactory.create_fetcher_from_config')
    def test_fetch_news_error_with_fail(self, mock_create_fetcher):
        """Тест ошибки получения новостей с прерыванием"""
        # Мокаем ошибку в fetcher
        mock_fetcher = Mock()
        mock_fetcher.fetch_news.side_effect = Exception("API Error")
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor(fail_on_errors=True)
        
        with pytest.raises(NewsProcessingError):
            processor.fetch_news()
    
    @patch('src.services.news.news_processor.FetcherFactory.create_fetcher_from_config')
    def test_search_news_success(self, mock_create_fetcher):
        """Тест успешного поиска новостей"""
        # Мокаем fetcher
        mock_fetcher = Mock()
        mock_fetcher.search_news.return_value = [
            {
                "title": "Search Result",
                "description": "Search description",
                "url": "http://example.com/search",
                "published_at": "2024-01-01T12:00:00Z",
                "source": "Search Source",
                "category": "Technology"
            }
        ]
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor()
        news_items = processor.search_news(query="test search", limit=5)
        
        assert len(news_items) == 1
        assert news_items[0].title == "Search Result"
        mock_fetcher.search_news.assert_called_once_with(
            query="test search",
            language=None,
            limit=5
        )
    
    def test_validate_news_items(self, sample_news_items):
        """Тест валидации новостных элементов"""
        processor = NewsProcessor()
        
        # Добавляем элемент с пустым заголовком
        invalid_item = NewsItem(
            title="",
            description="Invalid description",
            url="http://example.com/invalid",
            published_at=datetime.now(timezone.utc),
            source="Invalid Source"
        )
        
        test_items = sample_news_items + [invalid_item]
        valid_items = processor.validate_news_items(test_items)
        
        # Должно остаться только 2 валидных элемента
        assert len(valid_items) == 2
        assert all(item.title for item in valid_items)
        assert all(item.url for item in valid_items)
    
    def test_validate_news_items_duplicates(self, sample_news_items):
        """Тест дедупликации новостных элементов"""
        processor = NewsProcessor(enable_deduplication=True)
        
        # Добавляем дубликат
        duplicate_item = NewsItem(
            title="Duplicate News",
            description="Duplicate description",
            url="http://example.com/1",  # Тот же URL что и у первого элемента
            published_at=datetime.now(timezone.utc),
            source="Duplicate Source"
        )
        
        test_items = sample_news_items + [duplicate_item]
        valid_items = processor.validate_news_items(test_items)
        
        # Должно остаться только 2 уникальных элемента
        assert len(valid_items) == 2
        unique_urls = {item.url for item in valid_items}
        assert len(unique_urls) == 2
    
    @patch('src.services.news.news_processor.FetcherFactory.create_fetcher_from_config')
    def test_run_full_pipeline_success(self, mock_create_fetcher):
        """Тест успешного выполнения полного пайплайна"""
        # Мокаем fetcher
        mock_fetcher = Mock()
        mock_fetcher.fetch_news.return_value = {
            "articles": [
                {
                    "title": "Pipeline Test",
                    "description": "Pipeline description",
                    "url": "http://example.com/pipeline",
                    "published_at": "2024-01-01T12:00:00Z",
                    "source": "Pipeline Source",
                    "category": "Technology"
                }
            ]
        }
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor()
        result = processor.run_full_pipeline(
            query="test",
            category="technology",
            limit=10,
            export_to_sheets=False  # Отключаем экспорт для простоты
        )
        
        assert result["success"] is True
        assert result["fetched_count"] == 1
        assert result["processed_count"] == 1
        assert result["exported_count"] == 0
        assert result["duplicates_found"] == 0
        assert "processing_time" in result
        assert "start_time" in result
        assert "end_time" in result
    
    @patch('src.services.news.news_processor.FetcherFactory.create_fetcher_from_config')
    def test_run_full_pipeline_no_news(self, mock_create_fetcher):
        """Тест выполнения пайплайна без новостей"""
        # Мокаем fetcher без новостей
        mock_fetcher = Mock()
        mock_fetcher.fetch_news.return_value = {"articles": []}
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor()
        result = processor.run_full_pipeline(export_to_sheets=False)
        
        assert result["success"] is False
        assert result["fetched_count"] == 0
        assert result["processed_count"] == 0
        assert result["exported_count"] == 0
        assert "No news items fetched" in result["errors"]
    
    @patch('src.services.news.news_processor.FetcherFactory.create_fetcher_from_config')
    def test_get_provider_info(self, mock_create_fetcher):
        """Тест получения информации о провайдере"""
        # Мокаем fetcher
        mock_fetcher = Mock()
        mock_fetcher.get_categories.return_value = ["technology", "science"]
        mock_fetcher.get_languages.return_value = ["en", "ru"]
        mock_fetcher.check_health.return_value = {"status": "healthy"}
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor()
        info = processor.get_provider_info()
        
        assert info["provider"] == "thenewsapi"
        assert info["status"] == "active"
        assert info["categories"] == ["technology", "science"]
        assert info["languages"] == ["en", "ru"]
        assert info["health"] == {"status": "healthy"}


class TestCreateNewsProcessor:
    """Тесты для функции create_news_processor"""
    
    def test_create_processor_defaults(self):
        """Тест создания процессора с настройками по умолчанию"""
        processor = create_news_processor()
        
        assert isinstance(processor, NewsProcessor)
        assert processor.news_provider == "thenewsapi"
        assert processor.max_items_per_request == 50
        assert processor.enable_deduplication is True
        assert processor.fail_on_errors is False
    
    def test_create_processor_custom_params(self):
        """Тест создания процессора с пользовательскими параметрами"""
        processor = create_news_processor(
            news_provider="custom_provider",
            max_news_items=100,
            similarity_threshold=0.9,
            fail_on_errors=True
        )
        
        assert isinstance(processor, NewsProcessor)
        assert processor.news_provider == "custom_provider"
        assert processor.max_items_per_request == 100
        assert processor.fail_on_errors is True


class TestNewsProcessingError:
    """Тесты для класса исключения NewsProcessingError"""
    
    def test_news_processing_error(self):
        """Тест NewsProcessingError"""
        error = NewsProcessingError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception) 