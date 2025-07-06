# /src/services/news/exporter.py
# Экспорт в Google Sheets 

import json
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import gspread
from google.oauth2.service_account import Credentials

from src.config import get_google_settings
from src.logger import setup_logger
from src.langchain.news_chain import NewsItem


class GoogleSheetsExportError(Exception):
    """Базовое исключение для ошибок экспорта в Google Sheets"""
    pass


class AuthenticationError(GoogleSheetsExportError):
    """Ошибка аутентификации Google API"""
    pass


class SheetNotFoundError(GoogleSheetsExportError):
    """Ошибка когда таблица не найдена"""
    pass


class QuotaExceededError(GoogleSheetsExportError):
    """Ошибка превышения квоты Google API"""
    pass


class GoogleSheetsExporter:
    """Класс для экспорта новостей в Google Sheets"""
    
    def __init__(self, 
                 spreadsheet_id: Optional[str] = None,
                 worksheet_name: str = "News",
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """
        Инициализация экспортера Google Sheets
        
        Args:
            spreadsheet_id: ID Google таблицы (если None, берется из настроек)
            worksheet_name: Имя листа в таблице
            max_retries: Максимальное количество повторных попыток
            retry_delay: Задержка между попытками (секунды)
        """
        self.worksheet_name = worksheet_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._logger = None
        self._client = None
        self._spreadsheet = None
        self._worksheet = None
        
        # Получаем настройки Google
        self.settings = get_google_settings()
        self.spreadsheet_id = spreadsheet_id or self.settings.GOOGLE_SHEET_ID
        
        # Инициализируем клиент
        self._setup_client()
    
    @property
    def logger(self):
        """Ленивое создание логгера"""
        if self._logger is None:
            self._logger = setup_logger(__name__)
        return self._logger
    
    def _setup_client(self):
        """Настройка Google Sheets клиента"""
        try:
            # Создаем credentials из файла
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Проверяем наличие файла с service account
            service_account_path = self.settings.GOOGLE_SERVICE_ACCOUNT_PATH
            if not os.path.exists(service_account_path):
                raise AuthenticationError(f"Google service account file not found: {service_account_path}")
            
            credentials = Credentials.from_service_account_file(
                service_account_path, 
                scopes=scopes
            )
            
            # Создаем клиент gspread
            self._client = gspread.authorize(credentials)
            
            self.logger.info(f"Google Sheets client initialized successfully using {service_account_path}")
            
        except Exception as e:
            error_msg = f"Failed to initialize Google Sheets client: {str(e)}"
            self.logger.error(error_msg)
            raise AuthenticationError(error_msg) from e
    
    def _get_worksheet(self) -> gspread.Worksheet:
        """
        Получает рабочий лист, создавая его если необходимо
        
        Returns:
            Объект рабочего листа gspread
            
        Raises:
            SheetNotFoundError: Если таблица не найдена
            GoogleSheetsExportError: При других ошибках
        """
        if self._worksheet is not None:
            return self._worksheet
        
        try:
            # Открываем таблицу
            if self._spreadsheet is None:
                self._spreadsheet = self._client.open_by_key(self.spreadsheet_id)
                self.logger.info(f"Opened spreadsheet: {self._spreadsheet.title}")
            
            # Пытаемся найти существующий лист
            try:
                self._worksheet = self._spreadsheet.worksheet(self.worksheet_name)
                self.logger.info(f"Found existing worksheet: {self.worksheet_name}")
            except gspread.WorksheetNotFound:
                # Создаем новый лист
                self._worksheet = self._spreadsheet.add_worksheet(
                    title=self.worksheet_name,
                    rows=1000,
                    cols=20
                )
                self.logger.info(f"Created new worksheet: {self.worksheet_name}")
                
                # Добавляем заголовки
                self._setup_headers()
            
            return self._worksheet
            
        except gspread.SpreadsheetNotFound:
            raise SheetNotFoundError(f"Spreadsheet not found: {self.spreadsheet_id}")
        except Exception as e:
            error_msg = f"Failed to get worksheet: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"Spreadsheet ID: {self.spreadsheet_id}")
            self.logger.error(f"Worksheet name: {self.worksheet_name}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            raise GoogleSheetsExportError(error_msg) from e
    
    def _setup_headers(self):
        """Настраивает заголовки в новом листе"""
        headers = [
            "Timestamp",
            "Title", 
            "Description",
            "URL",
            "Published At",
            "Source",
            "Category",
            "Language",
            "Relevance Score",
            "Similarity Score",
            "Is Duplicate",
            "Duplicate Of",
            "Processing Date"
        ]
        
        try:
            self._worksheet.insert_row(headers, 1)
            self.logger.info("Headers added to worksheet")
        except Exception as e:
            self.logger.error(f"Failed to add headers: {str(e)}")
            raise GoogleSheetsExportError(f"Failed to add headers: {str(e)}")
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Выполняет функцию с повторными попытками при ошибках квоты
        
        Args:
            func: Функция для выполнения
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы
            
        Returns:
            Результат выполнения функции
            
        Raises:
            QuotaExceededError: Если квота исчерпана
            GoogleSheetsExportError: При других ошибках
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                error_message = str(e).lower()
                
                # Проверяем тип ошибки
                if "quota" in error_message or "rate limit" in error_message or "429" in error_message:
                    if attempt < self.max_retries:
                        delay = self.retry_delay * (2 ** attempt)  # Экспоненциальная задержка
                        self.logger.warning(f"Quota exceeded, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        time.sleep(delay)
                        continue
                    else:
                        raise QuotaExceededError(f"Google API quota exceeded after {self.max_retries + 1} attempts")
                
                elif "authentication" in error_message or "unauthorized" in error_message:
                    raise AuthenticationError(f"Authentication failed: {str(e)}")
                
                else:
                    # Для других ошибок делаем ограниченные повторы
                    if attempt < min(2, self.max_retries):
                        delay = self.retry_delay
                        self.logger.warning(f"API error, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries + 1}): {str(e)}")
                        time.sleep(delay)
                        continue
                    else:
                        raise GoogleSheetsExportError(f"Google Sheets API error: {str(e)}")
        
        # Если дошли сюда, значит все попытки исчерпаны
        raise GoogleSheetsExportError(f"All retry attempts failed. Last error: {str(last_exception)}")
    
    def export_news(self, news_items: List[NewsItem], append: bool = True) -> bool:
        """
        Экспортирует новости в Google Sheets
        
        Args:
            news_items: Список новостей для экспорта
            append: Если True, добавляет к существующим данным, иначе перезаписывает
            
        Returns:
            True если экспорт успешен, False иначе
            
        Raises:
            GoogleSheetsExportError: При ошибках экспорта
        """
        if not news_items:
            self.logger.warning("No news items to export")
            return True
        
        self.logger.info(f"Exporting {len(news_items)} news items to Google Sheets")
        
        try:
            worksheet = self._get_worksheet()
            
            # Подготавливаем данные для экспорта
            rows_data = self._prepare_export_data(news_items)
            
            if append:
                # Добавляем к существующим данным
                self._append_rows(worksheet, rows_data)
            else:
                # Перезаписываем данные (оставляем заголовки)
                self._overwrite_data(worksheet, rows_data)
            
            self.logger.info(f"Successfully exported {len(news_items)} news items")
            return True
            
        except Exception as e:
            error_msg = f"Failed to export news: {str(e)}"
            self.logger.error(error_msg)
            raise GoogleSheetsExportError(error_msg) from e
    
    def _prepare_export_data(self, news_items: List[NewsItem]) -> List[List[str]]:
        """
        Подготавливает данные новостей для экспорта
        
        Args:
            news_items: Список новостей
            
        Returns:
            Список строк для вставки в таблицу
        """
        rows_data = []
        current_time = datetime.now(timezone.utc).isoformat()
        
        for item in news_items:
            row = [
                current_time,  # Timestamp
                item.title or "",
                item.description or "",
                item.url or "",
                item.published_at.isoformat() if item.published_at else "",
                item.source or "",
                item.category or "",
                item.language or "",
                str(item.relevance_score) if item.relevance_score is not None else "",
                str(item.similarity_score) if item.similarity_score is not None else "",
                "Yes" if item.is_duplicate else "No",
                item.duplicate_of or "",
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            ]
            rows_data.append(row)
        
        return rows_data
    
    def _append_rows(self, worksheet: gspread.Worksheet, rows_data: List[List[str]]):
        """Добавляет строки к существующим данным"""
        def _append():
            return worksheet.append_rows(rows_data)
        
        self._retry_with_backoff(_append)
        self.logger.info(f"Appended {len(rows_data)} rows to worksheet")
    
    def _overwrite_data(self, worksheet: gspread.Worksheet, rows_data: List[List[str]]):
        """Перезаписывает данные (оставляя заголовки)"""
        def _clear_and_insert():
            # Очищаем все кроме первой строки (заголовки)
            if worksheet.row_count > 1:
                worksheet.delete_rows(2, worksheet.row_count)
            
            # Вставляем новые данные
            if rows_data:
                worksheet.insert_rows(rows_data, 2)
        
        self._retry_with_backoff(_clear_and_insert)
        self.logger.info(f"Overwrote worksheet with {len(rows_data)} rows")
    
    def get_export_summary(self) -> Dict[str, Any]:
        """
        Получает сводную информацию об экспорте
        
        Returns:
            Словарь с информацией о таблице и данных
        """
        try:
            worksheet = self._get_worksheet()
            
            return {
                "spreadsheet_id": self.spreadsheet_id,
                "spreadsheet_title": self._spreadsheet.title if self._spreadsheet else "Unknown",
                "worksheet_name": self.worksheet_name,
                "total_rows": worksheet.row_count,
                "data_rows": max(0, worksheet.row_count - 1),  # Исключаем заголовки
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "url": f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get export summary: {str(e)}")
            return {
                "error": str(e),
                "spreadsheet_id": self.spreadsheet_id,
                "worksheet_name": self.worksheet_name
            }


def create_google_sheets_exporter(spreadsheet_id: Optional[str] = None, 
                                 worksheet_name: str = "News",
                                 **kwargs) -> GoogleSheetsExporter:
    """
    Удобная функция для создания экспортера Google Sheets
    
    Args:
        spreadsheet_id: ID Google таблицы
        worksheet_name: Имя листа
        **kwargs: Дополнительные параметры для GoogleSheetsExporter
        
    Returns:
        Экземпляр GoogleSheetsExporter
    """
    return GoogleSheetsExporter(
        spreadsheet_id=spreadsheet_id,
        worksheet_name=worksheet_name,
        **kwargs
    ) 