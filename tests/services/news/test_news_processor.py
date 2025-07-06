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
    def mock_news_settings(self):
        """Фикстура для мокирования настроек новостей"""
        mock_settings = Mock()
        mock_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_settings.MAX_RETRIES = 3
        mock_settings.BACKOFF_FACTOR = 0.5
        return mock_settings
    
    @pytest.fixture
    def mock_ai_settings(self):
        """Фикстура для мокирования AI настроек"""
        mock_settings = Mock()
        mock_settings.OPENAI_API_KEY = "test_openai_key"
        mock_settings.OPENAI_MODEL = "gpt-3.5-turbo"
        mock_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
        mock_settings.MAX_TOKENS = 1000
        mock_settings.TEMPERATURE = 0.7
        return mock_settings
    
    @pytest.fixture
    def mock_google_settings(self):
        """Фикстура для мокирования Google настроек"""
        mock_settings = Mock()
        mock_settings.GOOGLE_GSHEET_ID = "test_sheet_id"
        mock_settings.GOOGLE_ACCOUNT_KEY = '{"type": "service_account"}'
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        return mock_settings
    
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
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    def test_init_success(self, mock_get_google_settings, mock_get_ai_settings, mock_get_news_settings, 
                         mock_news_settings, mock_ai_settings, mock_google_settings):
        """Тест успешной инициализации процессора"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        processor = NewsProcessor(
            news_provider="thenewsapi",
            spreadsheet_id="custom_sheet_id",
            max_news_items=100,
            similarity_threshold=0.9
        )
        
        assert processor.news_provider == "thenewsapi"
        assert processor.spreadsheet_id == "custom_sheet_id"
        assert processor.max_news_items == 100
        assert processor.similarity_threshold == 0.9
        assert processor.fail_on_errors is False
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    def test_init_missing_news_token(self, mock_get_ai_settings, mock_get_news_settings, 
                                   mock_ai_settings):
        """Тест инициализации без токена новостей"""
        mock_news_settings_no_token = Mock()
        mock_news_settings_no_token.THENEWSAPI_API_TOKEN = None
        mock_get_news_settings.return_value = mock_news_settings_no_token
        mock_get_ai_settings.return_value = mock_ai_settings
        
        with pytest.raises(NewsProcessingError, match="THENEWSAPI_API_TOKEN is required"):
            NewsProcessor()
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    def test_init_missing_openai_key(self, mock_get_ai_settings, mock_get_news_settings, 
                                   mock_news_settings):
        """Тест инициализации без OpenAI ключа"""
        mock_ai_settings_no_key = Mock()
        mock_ai_settings_no_key.OPENAI_API_KEY = None
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings_no_key
        
        with pytest.raises(NewsProcessingError, match="OPENAI_API_KEY is required"):
            NewsProcessor()
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    @patch('src.services.news.news_processor.create_news_fetcher_with_config')
    def test_fetch_news_success(self, mock_create_fetcher, mock_get_google_settings, 
                               mock_get_ai_settings, mock_get_news_settings,
                               mock_news_settings, mock_ai_settings, mock_google_settings):
        """Тест успешного получения новостей"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
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
            language="en",
            limit=10
        )
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    @patch('src.services.news.news_processor.create_news_fetcher_with_config')
    def test_fetch_news_error_no_fail(self, mock_create_fetcher, mock_get_google_settings,
                                     mock_get_ai_settings, mock_get_news_settings,
                                     mock_news_settings, mock_ai_settings, mock_google_settings):
        """Тест ошибки получения новостей без прерывания"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        # Мокаем ошибку в fetcher
        mock_fetcher = Mock()
        mock_fetcher.fetch_news.side_effect = Exception("API Error")
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor(fail_on_errors=False)
        news_items = processor.fetch_news()
        
        assert news_items == []
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    @patch('src.services.news.news_processor.create_news_fetcher_with_config')
    def test_fetch_news_error_with_fail(self, mock_create_fetcher, mock_get_google_settings,
                                       mock_get_ai_settings, mock_get_news_settings,
                                       mock_news_settings, mock_ai_settings, mock_google_settings):
        """Тест ошибки получения новостей с прерыванием"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        # Мокаем ошибку в fetcher
        mock_fetcher = Mock()
        mock_fetcher.fetch_news.side_effect = Exception("API Error")
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor(fail_on_errors=True)
        
        with pytest.raises(NewsProcessingError, match="Failed to fetch news"):
            processor.fetch_news()
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    @patch('src.services.news.news_processor.create_news_processing_chain')
    @patch('src.services.news.news_processor.OpenAIClient')
    def test_process_news_success(self, mock_openai_client, mock_create_chain, mock_get_google_settings,
                                 mock_get_ai_settings, mock_get_news_settings, 
                                 mock_news_settings, mock_ai_settings, mock_google_settings, sample_news_items):
        """Тест успешной обработки новостей"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        # Мокаем OpenAI client
        mock_openai_client.return_value = Mock()
        
        # Мокаем processing chain
        mock_chain = Mock()
        processed_items = sample_news_items.copy()
        processed_items[0].relevance_score = 8.5
        processed_items[1].relevance_score = 7.2
        mock_chain.process_news.return_value = processed_items
        mock_create_chain.return_value = mock_chain
        
        processor = NewsProcessor()
        result = processor.process_news(sample_news_items)
        
        assert len(result) == 2
        assert result[0].relevance_score == 8.5
        assert result[1].relevance_score == 7.2
        mock_chain.process_news.assert_called_once_with(
            sample_news_items,
            fail_on_errors=False
        )
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    def test_process_news_empty_list(self, mock_get_google_settings, mock_get_ai_settings, mock_get_news_settings,
                                   mock_news_settings, mock_ai_settings, mock_google_settings):
        """Тест обработки пустого списка новостей"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        processor = NewsProcessor()
        result = processor.process_news([])
        
        assert result == []
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    @patch('src.services.news.news_processor.create_google_sheets_exporter')
    def test_export_to_sheets_success(self, mock_create_exporter, mock_get_google_settings,
                                     mock_get_ai_settings, mock_get_news_settings, 
                                     mock_news_settings, mock_ai_settings, mock_google_settings, sample_news_items):
        """Тест успешного экспорта в Google Sheets"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        # Мокаем exporter
        mock_exporter = Mock()
        mock_exporter.export_news.return_value = True
        mock_create_exporter.return_value = mock_exporter
        
        processor = NewsProcessor()
        result = processor.export_to_sheets(sample_news_items)
        
        assert result is True
        mock_exporter.export_news.assert_called_once_with(sample_news_items, append=True)
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    @patch('src.services.news.news_processor.create_news_fetcher_with_config')
    @patch('src.services.news.news_processor.create_news_processing_chain')
    @patch('src.services.news.news_processor.create_google_sheets_exporter')
    @patch('src.services.news.news_processor.OpenAIClient')
    def test_run_full_pipeline_success(self, mock_openai_client, mock_create_exporter, mock_create_chain, 
                                      mock_create_fetcher, mock_get_google_settings,
                                      mock_get_ai_settings, mock_get_news_settings,
                                      mock_news_settings, mock_ai_settings, mock_google_settings):
        """Тест успешного выполнения полного пайплайна"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        # Мокаем OpenAI client
        mock_openai_client.return_value = Mock()
        
        # Мокаем fetcher
        mock_fetcher = Mock()
        mock_fetcher.fetch_news.return_value = {
            "articles": [
                {
                    "title": "Test Article 1",
                    "description": "Test description 1",
                    "url": "http://example.com/1",
                    "published_at": "2024-01-01T12:00:00Z",
                    "source": "Test Source",
                    "category": "Technology"
                },
                {
                    "title": "Test Article 2",
                    "description": "Test description 2",
                    "url": "http://example.com/2",
                    "published_at": "2024-01-02T14:00:00Z",
                    "source": "Another Source",
                    "category": "Science"
                }
            ]
        }
        mock_create_fetcher.return_value = mock_fetcher
        
        # Мокаем processing chain
        mock_chain = Mock()
        processed_items = [
            NewsItem(
                title="Processed Article 1",
                description="Processed description 1",
                url="http://example.com/1",
                published_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                source="Test Source",
                category="Technology"
            )
        ]
        processed_items[0].relevance_score = 8.5
        processed_items[0].is_duplicate = False
        mock_chain.process_news.return_value = processed_items
        mock_create_chain.return_value = mock_chain
        
        # Мокаем exporter
        mock_exporter = Mock()
        mock_exporter.export_news.return_value = True
        mock_create_exporter.return_value = mock_exporter
        
        processor = NewsProcessor()
        result = processor.run_full_pipeline(
            query="test",
            category="technology",
            limit=10
        )
        
        assert result["success"] is True
        assert result["fetched_count"] == 2
        assert result["processed_count"] == 1
        assert result["exported_count"] == 1
        assert result["duplicates_found"] == 0
        assert "duration_seconds" in result
        assert "start_time" in result
        assert "end_time" in result
        
        # Проверяем вызовы
        mock_fetcher.fetch_news.assert_called_once()
        mock_chain.process_news.assert_called_once()
        mock_exporter.export_news.assert_called_once()
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    @patch('src.services.news.news_processor.create_news_fetcher_with_config')
    def test_run_full_pipeline_no_news(self, mock_create_fetcher, mock_get_google_settings,
                                      mock_get_ai_settings, mock_get_news_settings,
                                      mock_news_settings, mock_ai_settings, mock_google_settings):
        """Тест выполнения пайплайна без новостей"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        # Мокаем fetcher без новостей
        mock_fetcher = Mock()
        mock_fetcher.fetch_news.return_value = {"articles": []}
        mock_create_fetcher.return_value = mock_fetcher
        
        processor = NewsProcessor()
        result = processor.run_full_pipeline()
        
        assert result["success"] is True
        assert result["fetched_count"] == 0
        assert result["processed_count"] == 0
        assert result["exported_count"] == 0
        assert result["duplicates_found"] == 0
        assert "duration_seconds" in result
        assert "start_time" in result
        assert "end_time" in result
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    @patch('src.services.news.news_processor.create_google_sheets_exporter')
    def test_get_export_summary(self, mock_create_exporter, mock_get_google_settings,
                               mock_get_ai_settings, mock_get_news_settings,
                               mock_news_settings, mock_ai_settings, mock_google_settings):
        """Тест получения сводки экспорта"""
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        # Мокаем exporter
        mock_exporter = Mock()
        mock_exporter.get_export_summary.return_value = {
            "spreadsheet_id": "test_sheet_id",
            "worksheet_name": "News",
            "total_rows": 100,
            "data_rows": 99
        }
        mock_create_exporter.return_value = mock_exporter
        
        processor = NewsProcessor()
        summary = processor.get_export_summary()
        
        assert summary["spreadsheet_id"] == "test_sheet_id"
        assert summary["worksheet_name"] == "News"
        assert summary["total_rows"] == 100
        assert summary["data_rows"] == 99
        mock_exporter.get_export_summary.assert_called_once()


class TestCreateNewsProcessor:
    """Тесты для функции create_news_processor"""
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    def test_create_processor_defaults(self, mock_get_google_settings, mock_get_ai_settings, mock_get_news_settings):
        """Тест создания процессора с настройками по умолчанию"""
        mock_news_settings = Mock()
        mock_news_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_news_settings.MAX_RETRIES = 3
        mock_news_settings.BACKOFF_FACTOR = 0.5
        
        mock_ai_settings = Mock()
        mock_ai_settings.OPENAI_API_KEY = "test_openai_key"
        mock_ai_settings.OPENAI_MODEL = "gpt-3.5-turbo"
        mock_ai_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
        mock_ai_settings.MAX_TOKENS = 1000
        mock_ai_settings.TEMPERATURE = 0.7
        
        mock_google_settings = Mock()
        mock_google_settings.GOOGLE_GSHEET_ID = "test_sheet_id"
        mock_google_settings.GOOGLE_ACCOUNT_KEY = '{"type": "service_account"}'
        mock_google_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        processor = create_news_processor()
        
        assert isinstance(processor, NewsProcessor)
        assert processor.news_provider == "thenewsapi"
        assert processor.max_news_items == 50
        assert processor.similarity_threshold == 0.85
        assert processor.fail_on_errors is False
    
    @patch('src.services.news.news_processor.get_news_settings')
    @patch('src.services.news.news_processor.get_ai_settings')
    @patch('src.services.news.news_processor.get_google_settings')
    def test_create_processor_custom_params(self, mock_get_google_settings, mock_get_ai_settings, mock_get_news_settings):
        """Тест создания процессора с пользовательскими параметрами"""
        mock_news_settings = Mock()
        mock_news_settings.THENEWSAPI_API_TOKEN = "test_token"
        mock_news_settings.MAX_RETRIES = 3
        mock_news_settings.BACKOFF_FACTOR = 0.5
        
        mock_ai_settings = Mock()
        mock_ai_settings.OPENAI_API_KEY = "test_openai_key"
        mock_ai_settings.OPENAI_MODEL = "gpt-3.5-turbo"
        mock_ai_settings.OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
        mock_ai_settings.MAX_TOKENS = 1000
        mock_ai_settings.TEMPERATURE = 0.7
        
        mock_google_settings = Mock()
        mock_google_settings.GOOGLE_GSHEET_ID = "test_sheet_id"
        mock_google_settings.GOOGLE_ACCOUNT_KEY = '{"type": "service_account"}'
        mock_google_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        
        mock_get_news_settings.return_value = mock_news_settings
        mock_get_ai_settings.return_value = mock_ai_settings
        mock_get_google_settings.return_value = mock_google_settings
        
        processor = create_news_processor(
            news_provider="custom_provider",
            max_news_items=100,
            similarity_threshold=0.9,
            fail_on_errors=True
        )
        
        assert isinstance(processor, NewsProcessor)
        assert processor.news_provider == "custom_provider"
        assert processor.max_news_items == 100
        assert processor.similarity_threshold == 0.9
        assert processor.fail_on_errors is True


class TestNewsProcessingError:
    """Тесты для класса исключения NewsProcessingError"""
    
    def test_news_processing_error(self):
        """Тест NewsProcessingError"""
        error = NewsProcessingError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception) 