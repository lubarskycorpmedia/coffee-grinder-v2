# /tests/services/news/test_exporter_simple.py

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from src.services.news.exporter import (
    GoogleSheetsExporter,
    create_google_sheets_exporter,
    GoogleSheetsExportError,
    AuthenticationError,
    SheetNotFoundError,
    QuotaExceededError
)
from src.langchain.news_chain import NewsItem


class TestGoogleSheetsExporterSimple:
    """Упрощенные тесты для GoogleSheetsExporter"""
    
    @pytest.fixture
    def mock_google_settings(self):
        """Фикстура для мокирования Google настроек"""
        mock_settings = Mock()
        mock_settings.GOOGLE_SHEET_ID = "test_spreadsheet_id"
        mock_settings.GOOGLE_SERVICE_ACCOUNT_PATH = "/test/path/service_account.json"
        mock_settings.GOOGLE_ACCOUNT_KEY = '{"type": "service_account", "project_id": "test"}'
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        return mock_settings
    
    @pytest.fixture
    def sample_news_items(self):
        """Фикстура с тестовыми новостями"""
        item1 = NewsItem(
            title="Test News 1",
            description="Test description 1",
            url="http://example.com/1",
            published_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source="Test Source",
            category="Technology",
            language="en"
        )
        item1.relevance_score = 8.5
        item1.similarity_score = 0.95
        item1.is_duplicate = False
        
        return [item1]
    
    @patch('src.services.news.exporter.os.path.exists')
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_file')
    def test_init_success(self, mock_credentials, mock_authorize, mock_get_settings, mock_exists, mock_google_settings):
        """Тест успешной инициализации экспортера"""
        mock_exists.return_value = True
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        
        assert exporter.spreadsheet_id == "test_spreadsheet_id"
        assert exporter.worksheet_name == "News"
        assert exporter.max_retries == 3
        assert exporter.retry_delay == 1.0
        assert exporter._client == mock_client
    
    @patch('src.services.news.exporter.os.path.exists')
    @patch('src.services.news.exporter.get_google_settings')
    def test_init_file_not_found(self, mock_get_settings, mock_exists, mock_google_settings):
        """Тест инициализации когда файл service account не найден"""
        mock_exists.return_value = False
        mock_get_settings.return_value = mock_google_settings
        
        with pytest.raises(AuthenticationError, match="Google service account file not found"):
            GoogleSheetsExporter()
    
    @patch('src.services.news.exporter.os.path.exists')
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_file')
    def test_prepare_export_data(self, mock_credentials, mock_authorize, mock_get_settings, mock_exists, mock_google_settings, sample_news_items):
        """Тест подготовки данных для экспорта"""
        mock_exists.return_value = True
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        rows_data = exporter._prepare_export_data(sample_news_items)
        
        assert len(rows_data) == 1
        
        # Проверяем первую строку согласно реальной структуре
        row1 = rows_data[0]
        # 0: Timestamp, 1: Title, 2: Description, 3: URL, 4: Image URL, 5: Published At, 6: Source, 7: Category, 8: Language, etc.
        assert row1[1] == "Test News 1"  # Title
        assert row1[2] == "Test description 1"  # Description
        assert row1[3] == "http://example.com/1"  # URL
        assert row1[5] == "2024-01-01T12:00:00+00:00"  # Published At
        assert row1[6] == "Test Source"  # Source
        assert row1[7] == "Technology"  # Category
        assert row1[8] == "en"  # Language
        assert row1[12] == "8.5"  # Relevance Score
        assert row1[13] == "0.95"  # Similarity Score
        assert row1[14] == "No"  # Is Duplicate


class TestCreateGoogleSheetsExporter:
    """Тесты для create_google_sheets_exporter"""
    
    @patch('src.services.news.exporter.os.path.exists')
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_file')
    def test_create_exporter_defaults(self, mock_credentials, mock_authorize, mock_get_settings, mock_exists):
        """Тест создания экспортера с настройками по умолчанию"""
        mock_exists.return_value = True
        mock_settings = Mock()
        mock_settings.GOOGLE_SHEET_ID = "test_id"
        mock_settings.GOOGLE_SERVICE_ACCOUNT_PATH = "/test/path/service_account.json"
        mock_settings.GOOGLE_ACCOUNT_KEY = '{"type": "service_account"}'
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = create_google_sheets_exporter()
        
        assert isinstance(exporter, GoogleSheetsExporter)
        assert exporter.spreadsheet_id == "test_id"
        assert exporter.worksheet_name == "News"


class TestExceptionClasses:
    """Тесты для классов исключений"""
    
    def test_google_sheets_export_error(self):
        """Тест GoogleSheetsExportError"""
        error = GoogleSheetsExportError("Test error")
        assert str(error) == "Test error"
    
    def test_authentication_error(self):
        """Тест AuthenticationError"""
        error = AuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
    
    def test_sheet_not_found_error(self):
        """Тест SheetNotFoundError"""
        error = SheetNotFoundError("Sheet not found")
        assert str(error) == "Sheet not found"
    
    def test_quota_exceeded_error(self):
        """Тест QuotaExceededError"""
        error = QuotaExceededError("Quota exceeded")
        assert str(error) == "Quota exceeded" 