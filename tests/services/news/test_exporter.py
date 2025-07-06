# /tests/services/news/test_exporter.py

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import gspread

from src.services.news.exporter import (
    GoogleSheetsExporter,
    create_google_sheets_exporter,
    GoogleSheetsExportError,
    AuthenticationError,
    SheetNotFoundError,
    QuotaExceededError
)
from src.langchain.news_chain import NewsItem


class TestGoogleSheetsExporter:
    """Тесты для GoogleSheetsExporter"""
    
    @pytest.fixture
    def mock_google_settings(self):
        """Фикстура для мокирования Google настроек"""
        mock_settings = Mock()
        mock_settings.GOOGLE_GSHEET_ID = "test_spreadsheet_id"
        mock_settings.GOOGLE_ACCOUNT_KEY = '{"type": "service_account", "project_id": "test"}'
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        return mock_settings
    
    @pytest.fixture
    def sample_news_items(self):
        """Фикстура с тестовыми новостями"""
        # Создаем базовые NewsItem объекты
        item1 = NewsItem(
            title="Test News 1",
            description="Test description 1",
            url="http://example.com/1",
            published_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source="Test Source",
            category="Technology",
            language="en"
        )
        # Устанавливаем дополнительные атрибуты
        item1.relevance_score = 8.5
        item1.similarity_score = 0.95
        item1.is_duplicate = False
        
        item2 = NewsItem(
            title="Test News 2",
            description="Test description 2",
            url="http://example.com/2",
            published_at=datetime(2024, 1, 2, 14, 30, 0, tzinfo=timezone.utc),
            source="Another Source",
            category="Science",
            language="en"
        )
        # Устанавливаем дополнительные атрибуты
        item2.relevance_score = 7.2
        item2.similarity_score = 0.75
        item2.is_duplicate = True
        item2.duplicate_of = "http://example.com/1"
        
        return [item1, item2]
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_init_success(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест успешной инициализации экспортера"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        
        assert exporter.spreadsheet_id == "test_spreadsheet_id"
        assert exporter.worksheet_name == "News"
        assert exporter.max_retries == 3
        assert exporter.retry_delay == 1.0
        assert exporter._client == mock_client
        
        mock_credentials.assert_called_once()
        mock_authorize.assert_called_once()
    
    @patch('src.services.news.exporter.get_google_settings')
    def test_init_invalid_json_key(self, mock_get_settings):
        """Тест инициализации с невалидным JSON ключом"""
        mock_settings = Mock()
        mock_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_settings.GOOGLE_ACCOUNT_KEY = "invalid json"
        mock_get_settings.return_value = mock_settings
        
        with pytest.raises(AuthenticationError, match="Invalid Google service account key JSON"):
            GoogleSheetsExporter()
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_init_authorization_error(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест ошибки авторизации при инициализации"""
        mock_get_settings.return_value = mock_google_settings
        mock_authorize.side_effect = Exception("Authorization failed")
        
        with pytest.raises(AuthenticationError, match="Failed to initialize Google Sheets client"):
            GoogleSheetsExporter()
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_get_worksheet_existing(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест получения существующего листа"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        # Мокаем spreadsheet и worksheet
        mock_spreadsheet = Mock()
        mock_spreadsheet.title = "Test Spreadsheet"
        mock_worksheet = Mock()
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        
        exporter = GoogleSheetsExporter()
        result = exporter._get_worksheet()
        
        assert result == mock_worksheet
        mock_client.open_by_key.assert_called_once_with("test_spreadsheet_id")
        mock_spreadsheet.worksheet.assert_called_once_with("News")
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_get_worksheet_create_new(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест создания нового листа"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        # Мокаем spreadsheet
        mock_spreadsheet = Mock()
        mock_spreadsheet.title = "Test Spreadsheet"
        mock_client.open_by_key.return_value = mock_spreadsheet
        
        # Лист не существует, создаем новый
        mock_spreadsheet.worksheet.side_effect = gspread.WorksheetNotFound("Not found")
        mock_new_worksheet = Mock()
        mock_spreadsheet.add_worksheet.return_value = mock_new_worksheet
        
        exporter = GoogleSheetsExporter()
        result = exporter._get_worksheet()
        
        assert result == mock_new_worksheet
        mock_spreadsheet.add_worksheet.assert_called_once_with(
            title="News",
            rows=1000,
            cols=20
        )
        # Проверяем что добавились заголовки
        mock_new_worksheet.insert_row.assert_called_once()
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_get_worksheet_spreadsheet_not_found(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест когда таблица не найдена"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        mock_client.open_by_key.side_effect = gspread.SpreadsheetNotFound("Not found")
        
        exporter = GoogleSheetsExporter()
        
        with pytest.raises(SheetNotFoundError, match="Spreadsheet not found"):
            exporter._get_worksheet()
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_prepare_export_data(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings, sample_news_items):
        """Тест подготовки данных для экспорта"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        rows_data = exporter._prepare_export_data(sample_news_items)
        
        assert len(rows_data) == 2
        
        # Проверяем первую строку
        row1 = rows_data[0]
        assert row1[1] == "Test News 1"  # Title
        assert row1[2] == "Test description 1"  # Description
        assert row1[3] == "http://example.com/1"  # URL
        assert row1[5] == "Test Source"  # Source
        assert row1[6] == "Technology"  # Category
        assert row1[7] == "en"  # Language
        assert row1[8] == "8.5"  # Relevance Score
        assert row1[9] == "0.95"  # Similarity Score
        assert row1[10] == "No"  # Is Duplicate
        assert row1[11] == ""  # Duplicate Of
        
        # Проверяем вторую строку
        row2 = rows_data[1]
        assert row2[1] == "Test News 2"  # Title
        assert row2[10] == "Yes"  # Is Duplicate
        assert row2[11] == "http://example.com/1"  # Duplicate Of
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_retry_with_backoff_success(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест успешного выполнения операции с повторными попытками"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        
        # Создаем функцию которая выполняется успешно
        mock_func = Mock(return_value="success")
        
        result = exporter._retry_with_backoff(mock_func, "arg1", kwarg1="value1")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    @patch('src.services.news.exporter.time.sleep')
    def test_retry_with_backoff_quota_exceeded(self, mock_sleep, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест повторных попыток при превышении квоты"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        
        # Создаем функцию которая сначала выбрасывает ошибку квоты, потом успешно выполняется
        mock_func = Mock(side_effect=[
            Exception("quota exceeded"),
            "success"
        ])
        
        result = exporter._retry_with_backoff(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once_with(1.0)
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_retry_with_backoff_authentication_error(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест что ошибки аутентификации не повторяются"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        
        # Создаем функцию которая выбрасывает ошибку аутентификации
        mock_func = Mock(side_effect=Exception("authentication failed"))
        
        with pytest.raises(AuthenticationError):
            exporter._retry_with_backoff(mock_func)
        
        # Проверяем что функция была вызвана только один раз (без повторных попыток)
        mock_func.assert_called_once()
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_export_news_empty_list(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест экспорта пустого списка новостей"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        
        result = exporter.export_news([])
        
        assert result is True
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_export_news_append_mode(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings, sample_news_items):
        """Тест экспорта новостей в режиме добавления"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        # Мокаем worksheet
        mock_worksheet = Mock()
        mock_client.open_by_key.return_value.worksheet.return_value = mock_worksheet
        
        exporter = GoogleSheetsExporter()
        exporter._get_worksheet = Mock(return_value=mock_worksheet)
        
        result = exporter.export_news(sample_news_items, append=True)
        
        assert result is True
        mock_worksheet.append_rows.assert_called_once()
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_export_news_overwrite_mode(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings, sample_news_items):
        """Тест экспорта новостей в режиме перезаписи"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        # Мокаем worksheet
        mock_worksheet = Mock()
        mock_worksheet.row_count = 5
        mock_client.open_by_key.return_value.worksheet.return_value = mock_worksheet
        
        exporter = GoogleSheetsExporter()
        exporter._get_worksheet = Mock(return_value=mock_worksheet)
        
        result = exporter.export_news(sample_news_items, append=False)
        
        assert result is True
        mock_worksheet.delete_rows.assert_called_once_with(2, 5)
        mock_worksheet.insert_rows.assert_called_once()
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_export_news_error(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings, sample_news_items):
        """Тест обработки ошибки при экспорте"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        exporter._get_worksheet = Mock(side_effect=Exception("Test error"))
        
        with pytest.raises(GoogleSheetsExportError, match="Failed to export news"):
            exporter.export_news(sample_news_items)
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_get_export_summary_success(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест получения сводки экспорта"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        # Мокаем worksheet с данными
        mock_worksheet = Mock()
        mock_worksheet.row_count = 101  # 100 строк данных + заголовок
        mock_spreadsheet = Mock()
        mock_spreadsheet.title = "Test Spreadsheet"
        
        exporter = GoogleSheetsExporter()
        exporter._get_worksheet = Mock(return_value=mock_worksheet)
        exporter._spreadsheet = mock_spreadsheet
        
        summary = exporter.get_export_summary()
        
        assert summary["total_rows"] == 101
        assert summary["data_rows"] == 100  # Исключая заголовок
        assert summary["worksheet_name"] == "News"
        assert summary["spreadsheet_id"] == "test_spreadsheet_id"
        assert summary["spreadsheet_title"] == "Test Spreadsheet"
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_get_export_summary_error(self, mock_credentials, mock_authorize, mock_get_settings, mock_google_settings):
        """Тест обработки ошибки при получении сводки"""
        mock_get_settings.return_value = mock_google_settings
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = GoogleSheetsExporter()
        exporter._get_worksheet = Mock(side_effect=Exception("Test error"))
        
        summary = exporter.get_export_summary()
        
        assert "error" in summary
        assert summary["spreadsheet_id"] == "test_spreadsheet_id"
        assert summary["worksheet_name"] == "News"


class TestCreateGoogleSheetsExporter:
    """Тесты для функции create_google_sheets_exporter"""
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_create_exporter_defaults(self, mock_credentials, mock_authorize, mock_get_settings):
        """Тест создания экспортера с настройками по умолчанию"""
        mock_settings = Mock()
        mock_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_settings.GOOGLE_ACCOUNT_KEY = '{"type": "service_account"}'
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = create_google_sheets_exporter()
        
        assert isinstance(exporter, GoogleSheetsExporter)
        assert exporter.spreadsheet_id == "test_id"
        assert exporter.worksheet_name == "News"
        assert exporter.max_retries == 3
        assert exporter.retry_delay == 1.0
    
    @patch('src.services.news.exporter.get_google_settings')
    @patch('src.services.news.exporter.gspread.authorize')
    @patch('src.services.news.exporter.Credentials.from_service_account_info')
    def test_create_exporter_custom_params(self, mock_credentials, mock_authorize, mock_get_settings):
        """Тест создания экспортера с пользовательскими параметрами"""
        mock_settings = Mock()
        mock_settings.GOOGLE_GSHEET_ID = "test_id"
        mock_settings.GOOGLE_ACCOUNT_KEY = '{"type": "service_account"}'
        mock_settings.GOOGLE_ACCOUNT_EMAIL = "test@example.com"
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_authorize.return_value = mock_client
        
        exporter = create_google_sheets_exporter(
            spreadsheet_id="custom_id",
            worksheet_name="CustomSheet",
            max_retries=5,
            retry_delay=2.0
        )
        
        assert isinstance(exporter, GoogleSheetsExporter)
        assert exporter.spreadsheet_id == "custom_id"
        assert exporter.worksheet_name == "CustomSheet"
        assert exporter.max_retries == 5
        assert exporter.retry_delay == 2.0


class TestExceptionClasses:
    """Тесты для классов исключений"""
    
    def test_google_sheets_export_error(self):
        """Тест GoogleSheetsExportError"""
        error = GoogleSheetsExportError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_authentication_error(self):
        """Тест AuthenticationError"""
        error = AuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert isinstance(error, GoogleSheetsExportError)
    
    def test_sheet_not_found_error(self):
        """Тест SheetNotFoundError"""
        error = SheetNotFoundError("Sheet not found")
        assert str(error) == "Sheet not found"
        assert isinstance(error, GoogleSheetsExportError)
    
    def test_quota_exceeded_error(self):
        """Тест QuotaExceededError"""
        error = QuotaExceededError("Quota exceeded")
        assert str(error) == "Quota exceeded"
        assert isinstance(error, GoogleSheetsExportError) 