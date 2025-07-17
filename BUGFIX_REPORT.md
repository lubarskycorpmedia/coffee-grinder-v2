# Отчет об исправлении ошибок API

## 🐛 Проблема

После рефакторинга архитектуры фронтенд выдавал ошибки:
```
GET /news/api/available_parameter_values 500 (Internal Server Error)
GET /news/api/provider_parameters 500 (Internal Server Error)
```

## 🔍 Причины ошибок

1. **Удален метод `get_enabled_providers()`** - в рефакторинге `fetcher_fabric.py` был удален метод `FetcherFactory.get_enabled_providers()`, который использовался в API эндпоинтах

2. **Отсутствовал параметр API ключа** - оба эндпоинта не требовали `api_key` параметр, в отличие от остальных API методов

3. **Дублирующий импорт** - `FetcherFactory` импортировался дважды в `news.py`

## ✅ Исправления

### 1. Восстановлен метод `get_enabled_providers()`
**Файл:** `src/services/news/fetcher_fabric.py`
```python
@classmethod
def get_enabled_providers(cls) -> list[str]:
    """Возвращает список включенных провайдеров из конфига"""
    from src.config import get_news_providers_settings
    
    providers_settings = get_news_providers_settings()
    return list(providers_settings.get_enabled_providers().keys())
```

### 2. Добавлен параметр API ключа в эндпоинты
**Файл:** `src/api/routers/news.py`
```python
# Было:
async def get_available_parameter_values() -> Dict[str, Any]:

# Стало:
async def get_available_parameter_values(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
```

```python
# Было:
async def get_provider_parameters() -> Dict[str, Any]:

# Стало:  
async def get_provider_parameters(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
```

### 3. Убран дублирующий импорт
**Файл:** `src/api/routers/news.py`
```python
# Убрано второе:
# from src.services.news.fetcher_fabric import FetcherFactory
```

## 🎯 Результат

Теперь API эндпоинты должны работать корректно:
- ✅ `/news/api/available_parameter_values` - возвращает категории и языки провайдеров
- ✅ `/news/api/provider_parameters` - возвращает параметры форм провайдеров

## 🔧 Затронутые файлы

1. `src/services/news/fetcher_fabric.py` - восстановлен метод
2. `src/api/routers/news.py` - добавлен API ключ, убран дублирующий импорт

## 📝 Примечания

Исправления сохраняют обратную совместимость с существующим фронтендом и не нарушают новую архитектуру рефакторинга. 