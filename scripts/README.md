# Manual Testing Scripts

Этот каталог содержит скрипты для ручного тестирования компонентов системы в реальной среде.

## test_fetcher_manual.py

Скрипт для тестирования сборщика новостей с реальным API TheNewsAPI.

### Требования

1. **Переменные окружения** (в файле `.env` в корне проекта):
   ```bash
   # Обязательно для тестирования fetcher'а
   THENEWSAPI_API_TOKEN=your_actual_token_here
   
   # Заглушки для других компонентов (не используются в тестах fetcher'а)
   GOOGLE_GSHEET_ID=test-sheet-id
   GOOGLE_ACCOUNT_EMAIL=test@example.com
   GOOGLE_ACCOUNT_KEY=test-key
   OPENAI_API_KEY=sk-test-key
   ```

2. **API ключ TheNewsAPI**:
   - Зарегистрируйтесь на [thenewsapi.com](https://www.thenewsapi.com/)
   - Получите API ключ
   - Замените `your_actual_token_here` на реальный токен

### Настройка параметров

Перед запуском отредактируйте параметры тестов в начале файла `test_fetcher_manual.py` в секции **"НАСТРОЙКИ ТЕСТОВ"**:

```python
# ТЕСТ 1: Параметры для Headlines
HEADLINES_PARAMS = {
    "locale": "us",                    # Измените на нужную страну
    "language": "en",                  # Измените на нужный язык
    "headlines_per_category": 3,       # Количество заголовков (1-10)
    # "domains": "cnn.com,bbc.com",    # Раскомментируйте для фильтрации
}

# ТЕСТ 2: Параметры для All News  
ALL_NEWS_PARAMS = {
    "search": "AI technology",         # Измените поисковый запрос
    "language": "en",                  # Язык новостей
    "limit": 3,                        # Количество результатов (1-100)
    # "categories": "tech,business",   # Раскомментируйте для категорий
}

# ТЕСТ 3: Параметры для Sources
SOURCES_PARAMS = {
    "language": "en",                  # Язык источников
    "locale": "us",                    # Страна источников
}
```

### Запуск

```bash
# Из корня проекта
poetry run python scripts/test_fetcher_manual.py
```

### Что тестирует скрипт

Скрипт выполняет 3 теста с различными эндпоинтами TheNewsAPI. Параметры можно настроить в начале скрипта в секции **"НАСТРОЙКИ ТЕСТОВ"**.

#### ТЕСТ 1: Получение заголовков (`/v1/news/headlines`)
- **Доступность**: Только на Standard план и выше (платные планы)
- **Ожидаемый результат**: 403 ошибка на бесплатном плане - это нормально
- **Интерпретация**: 
  - ✅ 200 OK - план Standard+ работает
  - ❌ 403 Forbidden - бесплатный план, эндпоинт недоступен
  - ❌ 401 Unauthorized - неверный API ключ

#### ТЕСТ 2: Поиск новостей (`/v1/news/all`)
- **Доступность**: Доступен на всех планах (включая бесплатный)
- **Ожидаемый результат**: Должен работать на всех планах
- **Интерпретация**: 
  - ✅ 200 OK - API ключ валидный, всё работает
  - ❌ 401 Unauthorized - неверный API ключ
  - ❌ 429 Too Many Requests - превышен лимит запросов

#### ТЕСТ 3: Получение источников (`/v1/news/sources`)
- **Доступность**: Доступен на всех планах (включая бесплатный)
- **Ожидаемый результат**: Должен работать на всех планах
- **Интерпретация**: 
  - ✅ 200 OK - список источников получен
  - ❌ 401 Unauthorized - неверный API ключ
  - ❌ 429 Too Many Requests - превышен лимит запросов

**Примечание**: Эндпоинт `/v1/news/top` не тестируется в скрипте, но доступен в fetcher'е. Он имеет те же ограничения, что и `/v1/news/headlines` (только платные планы).

### Интерпретация результатов

#### ✅ Успешное выполнение
```
============================================================
✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!
🎉 Fetcher работает корректно с реальным API!
============================================================
```

**Что это означает:**
- API ключ валидный
- Сетевое подключение работает
- Fetcher корректно обрабатывает запросы и ответы
- Работает минимум 1 из 3 эндпоинтов

#### ❌ Ошибки выполнения
```
============================================================
❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!
💡 Проверьте API ключ и подключение к интернету
============================================================
```

**Возможные причины:**
- Неверный API ключ (401 ошибка)
- Отсутствует интернет-соединение
- Все эндпоинты недоступны на вашем плане

### Детальные логи

Скрипт выводит подробную информацию о каждом запросе:

#### Параметры запроса
```
📋 Параметры запроса:
  - search: AI technology
  - language: en
  - limit: 3
  - sort: relevance_score
  - sort_order: desc
```

#### HTTP запрос
```
🌐 GET https://api.thenewsapi.com/v1/news/all?search=AI+technology&language=en&limit=3&sort=relevance_score&sort_order=desc&api_token=abcd1234...xyz9
📤 Attempt 1/3
```

#### HTTP ответ
```
📥 Response: 200 OK
📊 Content-Type: application/json
📊 Content-Length: 15420 bytes
✅ Successfully fetched 3 items
```

### Коды ошибок

| Код | Значение | Действие |
|-----|----------|----------|
| 200 | Успех | ✅ Всё работает |
| 401 | Неверный API ключ | Проверьте токен в .env |
| 403 | Эндпоинт недоступен | Обновите план подписки |
| 429 | Превышен лимит запросов | Подождите или обновите план |
| 5xx | Ошибка сервера | Повторите позже |

### Планы подписки TheNewsAPI

- **Бесплатный план**: Ограниченный доступ к эндпоинтам
- **Платные планы**: Полный доступ ко всем функциям

Если получаете 403 ошибки, это нормально для бесплатного плана.

### Устранение неполадок

#### Проблема: "No module named 'requests'"
```bash
poetry install
```

#### Проблема: "THENEWSAPI_API_TOKEN not found"
1. Проверьте наличие файла `.env` в корне проекта
2. Убедитесь, что токен указан правильно
3. Перезапустите скрипт

#### Проблема: Все запросы возвращают 403
- Это нормально для бесплатного плана
- Рассмотрите обновление подписки на TheNewsAPI

#### Проблема: Timeout ошибки
- Проверьте интернет-соединение
- Убедитесь, что нет блокировки файрвола

## Справочник по параметрам API

### Эндпоинт: Headlines (`/v1/news/headlines`)

**Доступность**: Standard план и выше

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `api_token` | ✅ | string | Ваш API токен | `your_token_here` |
| `locale` | ❌ | string | Коды стран через запятую | `us`, `us,ca`, `gb,de` |
| `language` | ❌ | string | Коды языков через запятую | `en`, `en,es`, `ru,de` |
| `domains` | ❌ | string | Домены для включения | `cnn.com`, `bbc.com,reuters.com` |
| `exclude_domains` | ❌ | string | Домены для исключения | `example.com,spam.com` |
| `source_ids` | ❌ | string | ID источников для включения | `source1,source2` |
| `exclude_source_ids` | ❌ | string | ID источников для исключения | `source3,source4` |
| `published_on` | ❌ | string | Дата публикации | `2025-01-15` |
| `headlines_per_category` | ❌ | int | Количество заголовков на категорию (макс. 10) | `3`, `6`, `10` |
| `include_similar` | ❌ | bool | Включать похожие статьи | `true`, `false` |

**Дефолтные значения:**
- `locale`: `"us"`
- `language`: `"en"`
- `headlines_per_category`: `6`
- `include_similar`: `true`

### Эндпоинт: All News (`/v1/news/all`)

**Доступность**: Все планы

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `api_token` | ✅ | string | Ваш API токен | `your_token_here` |
| `search` | ❌ | string | Поисковый запрос с операторами | `"AI technology"`, `"bitcoin + crypto"`, `"apple - iphone"` |
| `locale` | ❌ | string | Коды стран через запятую | `us`, `us,ca`, `gb,de` |
| `language` | ❌ | string | Коды языков через запятую | `en`, `en,es`, `ru,de` |
| `domains` | ❌ | string | Домены для включения | `techcrunch.com,wired.com` |
| `exclude_domains` | ❌ | string | Домены для исключения | `spam.com,fake.com` |
| `source_ids` | ❌ | string | ID источников для включения | `source1,source2` |
| `exclude_source_ids` | ❌ | string | ID источников для исключения | `source3,source4` |
| `categories` | ❌ | string | Категории для включения | `business`, `tech,business` |
| `exclude_categories` | ❌ | string | Категории для исключения | `sports,entertainment` |
| `published_after` | ❌ | string | Дата начала поиска | `2025-01-01` |
| `published_before` | ❌ | string | Дата окончания поиска | `2025-01-15` |
| `published_on` | ❌ | string | Конкретная дата | `2025-01-15` |
| `sort` | ❌ | string | Сортировка | `published_at`, `relevance_score` |
| `sort_order` | ❌ | string | Порядок сортировки | `asc`, `desc` |
| `limit` | ❌ | int | Количество результатов (макс. 100) | `10`, `50`, `100` |
| `page` | ❌ | int | Номер страницы | `1`, `2`, `3` |

**Дефолтные значения:**
- `sort`: `"published_at"`
- `sort_order`: `"desc"`
- `limit`: `100`
- `page`: `1`

**Операторы поиска:**
- `+` - обязательное слово: `"bitcoin + crypto"`
- `-` - исключить слово: `"apple - iphone"`
- `|` - ИЛИ: `"bitcoin | ethereum"`
- `()` - группировка: `"crypto + (bitcoin | ethereum)"`

### Эндпоинт: Top Stories (`/v1/news/top`)

**Доступность**: Standard план и выше

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `api_token` | ✅ | string | Ваш API токен | `your_token_here` |
| `locale` | ❌ | string | Коды стран через запятую | `us`, `us,ca`, `gb,de` |
| `language` | ❌ | string | Коды языков через запятую | `en`, `en,es`, `ru,de` |
| `domains` | ❌ | string | Домены для включения | `cnn.com`, `bbc.com,reuters.com` |
| `exclude_domains` | ❌ | string | Домены для исключения | `example.com,spam.com` |
| `source_ids` | ❌ | string | ID источников для включения | `source1,source2` |
| `exclude_source_ids` | ❌ | string | ID источников для исключения | `source3,source4` |
| `categories` | ❌ | string | Категории для включения | `business`, `tech,business` |
| `exclude_categories` | ❌ | string | Категории для исключения | `sports,entertainment` |
| `published_after` | ❌ | string | Дата начала поиска | `2025-01-01` |
| `published_before` | ❌ | string | Дата окончания поиска | `2025-01-15` |
| `published_on` | ❌ | string | Конкретная дата | `2025-01-15` |
| `sort` | ❌ | string | Сортировка | `published_at`, `relevance_score` |
| `sort_order` | ❌ | string | Порядок сортировки | `asc`, `desc` |
| `limit` | ❌ | int | Количество результатов (макс. 100) | `10`, `50`, `100` |
| `page` | ❌ | int | Номер страницы | `1`, `2`, `3` |

**Дефолтные значения:**
- `locale`: `"us"`
- `language`: `"en"`
- `sort`: `"published_at"`
- `sort_order`: `"desc"`
- `limit`: `100`
- `page`: `1`

### Эндпоинт: Sources (`/v1/news/sources`)

**Доступность**: Все планы

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `api_token` | ✅ | string | Ваш API токен | `your_token_here` |
| `locale` | ❌ | string | Коды стран через запятую | `us`, `us,ca`, `gb,de` |
| `language` | ❌ | string | Коды языков через запятую | `en`, `en,es`, `ru,de` |
| `categories` | ❌ | string | Категории для фильтрации | `business`, `tech,business` |

**Дефолтные значения:** Все параметры необязательны (None)

### Поддерживаемые страны (`locale`)

| Код | Страна | Код | Страна | Код | Страна |
|-----|--------|-----|--------|-----|--------|
| `ar` | Argentina | `am` | Armenia | `au` | Australia |
| `at` | Austria | `by` | Belarus | `be` | Belgium |
| `bo` | Bolivia | `br` | Brazil | `bg` | Bulgaria |
| `ca` | Canada | `cl` | Chile | `cn` | China |
| `co` | Colombia | `hr` | Croatia | `cz` | Czechia |
| `ec` | Ecuador | `eg` | Egypt | `fr` | France |
| `de` | Germany | `gr` | Greece | `hn` | Honduras |
| `hk` | Hong Kong | `in` | India | `id` | Indonesia |
| `ir` | Iran | `ie` | Ireland | `il` | Israel |
| `it` | Italy | `jp` | Japan | `kr` | Korea |
| `mx` | Mexico | `nl` | Netherlands | `nz` | New Zealand |
| `ni` | Nicaragua | `pk` | Pakistan | `pa` | Panama |
| `pe` | Peru | `pl` | Poland | `pt` | Portugal |
| `qa` | Qatar | `ro` | Romania | `ru` | Russia |
| `sa` | Saudi Arabia | `za` | South Africa | `es` | Spain |
| `ch` | Switzerland | `sy` | Syria | `tw` | Taiwan |
| `th` | Thailand | `tr` | Turkey | `ua` | Ukraine |
| `gb` | United Kingdom | `us` | United States | `uy` | Uruguay |
| `ve` | Venezuela | | | | |

### Поддерживаемые языки (`language`)

| Код | Язык | Код | Язык | Код | Язык |
|-----|------|-----|------|-----|------|
| `ar` | Arabic | `bg` | Bulgarian | `bn` | Bengali |
| `cs` | Czech | `da` | Danish | `de` | German |
| `el` | Greek | `en` | English | `es` | Spanish |
| `et` | Estonian | `fa` | Persian | `fi` | Finnish |
| `fr` | French | `he` | Hebrew | `hi` | Hindi |
| `hr` | Croatian | `hu` | Hungarian | `id` | Indonesian |
| `it` | Italian | `ja` | Japanese | `ko` | Korean |
| `lt` | Lithuanian | `multi` | Multi-language | `nl` | Dutch |
| `no` | Norwegian | `pl` | Polish | `pt` | Portuguese |
| `ro` | Romanian | `ru` | Russian | `sk` | Slovak |
| `sv` | Swedish | `ta` | Tamil | `th` | Thai |
| `tr` | Turkish | `uk` | Ukrainian | `vi` | Vietnamese |
| `zh` | Chinese | | | | |

### Категории новостей

**Примечание**: Список ниже содержит основные категории из документации API. Полный список доступных категорий можно получить с помощью скрипта `scripts/get_categories.py`, который анализирует все источники и извлекает их категории.

Основные категории, поддерживаемые API:
- `business` - Бизнес
- `tech` - Технологии  
- `sports` - Спорт
- `entertainment` - Развлечения
- `health` - Здоровье
- `science` - Наука
- `general` - Общие новости
- `travel` - Путешествия

**Получение полного списка категорий:**
```bash
# Запуск скрипта для получения всех доступных категорий
poetry run python scripts/get_categories.py
```

Скрипт создаст файл `scripts/available_categories.txt` с полным списком категорий и статистикой по количеству источников в каждой категории.

### Тарифные планы и ограничения

#### Планы подписки

| План | Стоимость | Запросов/месяц | Доступные эндпоинты |
|------|-----------|----------------|-------------------|
| **Free** | $0 | 50 | `/v1/news/all`, `/v1/news/sources` |
| **Standard** | $9.99 | 10,000 | Все эндпоинты |
| **Professional** | $49.99 | 100,000 | Все эндпоинты |
| **Enterprise** | $199.99 | 1,000,000 | Все эндпоинты |

#### Ограничения по эндпоинтам

| Эндпоинт | Free | Standard+ | Примечания |
|----------|------|-----------|-----------|
| `/v1/news/headlines` | ❌ | ✅ | Только платные планы |
| `/v1/news/top` | ❌ | ✅ | Только платные планы |
| `/v1/news/all` | ✅ | ✅ | Доступен всем |
| `/v1/news/sources` | ✅ | ✅ | Доступен всем |

#### Лимиты запросов

- **Rate Limit**: 100 запросов в минуту для всех планов
- **Timeout**: 30 секунд на запрос
- **Максимальный размер ответа**: 10MB

#### Статус коды ошибок

| Код | Описание | Причина | Решение |
|-----|----------|---------|---------|
| 200 | Успех | Запрос выполнен | - |
| 400 | Неверный запрос | Неправильные параметры | Проверьте параметры запроса |
| 401 | Неавторизован | Неверный API ключ | Проверьте токен в .env |
| 403 | Запрещено | Эндпоинт недоступен на плане | Обновите план подписки |
| 429 | Превышен лимит | Слишком много запросов | Подождите или обновите план |
| 500 | Ошибка сервера | Внутренняя ошибка API | Повторите запрос позже |
| 503 | Сервис недоступен | Техническое обслуживание | Повторите запрос позже |

#### Форматы данных

**Дата и время:**
- Формат: ISO 8601 (`YYYY-MM-DDTHH:MM:SS.sssZ`)
- Часовой пояс: UTC
- Примеры: `2025-01-15T10:30:00.000Z`, `2025-01-15`

**Поля ответа статей:**
- `uuid` - уникальный идентификатор статьи
- `title` - заголовок статьи
- `description` - мета-описание (может быть сокращено)
- `snippet` - первые 60 символов тела статьи
- `url` - ссылка на оригинальную статью
- `image_url` - ссылка на главное изображение
- `language` - язык статьи (ISO 639-1)
- `published_at` - дата и время публикации
- `source` - домен источника
- `categories` - массив категорий
- `locale` - страна источника (ISO 3166-1)
- `keywords` - ключевые слова статьи

**Поля ответа источников:**
- `id` - уникальный идентификатор источника
- `name` - название источника
- `description` - описание источника
- `url` - официальный сайт источника
- `domain` - домен источника
- `language` - язык источника
- `country` - страна источника
- `categories` - массив категорий источника

### Дополнительная информация

- **Документация API**: [TheNewsAPI Docs](https://www.thenewsapi.com/documentation)
- **Тарифные планы**: [TheNewsAPI Pricing](https://www.thenewsapi.com/pricing)
- **Поддержка**: Создайте issue в репозитории проекта
- **Статус API**: [TheNewsAPI Status](https://status.thenewsapi.com/) 