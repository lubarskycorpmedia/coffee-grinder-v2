# NewsData.io Provider Documentation

Документация для провайдера NewsData.io в системе coffee-grinder-v2.

## Обзор

NewsData.io - это современный сервис для получения новостей со всего мира с поддержкой множества языков и стран. NewsData.io собирает новости из более чем **84,770 источников новостей**, которые охватывают около **206 стран** на **89 языках**. На данный момент NewsData.io имеет доступ к более чем **100 миллионам новостных статей**, собранных с 2018 года по сегодняшний день.

Провайдер предоставляет доступ к:
- **Latest News API** - последние новости (до 48 часов)
- **Crypto News API** - криптовалютные новости и блоги
- **News Archive API** - архивные данные (до 5 лет для корпоративных планов)
- **News Sources API** - информация об источниках новостей
- **AI-анализ** - теги, анализ тональности, регионы, организации
- **Расширенный поиск** - по ключевым словам, фразам, заголовкам, мета-данным

## Настройка

### 1. Получение API ключа

1. Зарегистрируйтесь на [NewsData.io](https://newsdata.io/)
2. Подтвердите email
3. Получите API ключ в личном кабинете
4. Выберите подходящий тарифный план

### 2. Конфигурация

Добавьте настройки в файл `.env`:
```bash
# NewsData.io настройки
NEWSDATA_API_KEY=your_api_key_here
```

Настройки провайдера в `src/config.py`:
```python
"newsdata": {
    "enabled": True,
    "priority": 3,
    "api_key": os.getenv("NEWSDATA_API_KEY"),
    "base_url": "https://newsdata.io/api/1",
    "page_size": 50
}
```

### 3. Параметры конфигурации

- **enabled**: Включить/выключить провайдер
- **priority**: Приоритет провайдера (1-10, где 3 = третий по приоритету)
- **api_key**: API ключ от NewsData.io
- **base_url**: Базовый URL API (обычно не меняется)
- **page_size**: Количество статей за запрос (макс. 50 для бесплатного плана)

## Возможности провайдера

### Поддерживаемые методы

1. **fetch_news(rubrics)** - Получение новостей по рубрикам
2. **search_news(query, **kwargs)** - Поиск новостей по запросу
3. **get_sources()** - Получение доступных источников
4. **check_health()** - Проверка состояния провайдера
5. **get_categories()** - Получение поддерживаемых категорий
6. **get_languages()** - Получение поддерживаемых языков

### Эндпоинты NewsData.io

NewsData.io предоставляет два основных эндпоинта для получения новостей:

#### 1. Latest News API (`/api/1/latest`)
- **Использование**: Получение последних новостей с фильтрацией
- **Методы провайдера**: `fetch_news()`, `search_news()`
- **Доступность**: Все планы
- **Особенности**: Универсальный эндпоинт с множеством параметров фильтрации

#### 2. Sources API (`/api/1/sources`)
- **Использование**: Получение списка доступных источников
- **Метод провайдера**: `get_sources()`
- **Доступность**: Все планы
- **Особенности**: Информация об источниках с метаданными

### Маппинг рубрик

Рубрики coffee-grinder автоматически маппятся в категории NewsData.io:

| Рубрика | NewsData.io категория |
|---------|----------------------|
| политика | politics |
| экономика | business |
| технологии | technology |
| спорт | sports |
| здоровье | health |
| наука | science |
| развлечения | entertainment |
| мир | world |
| туризм | tourism |
| еда | food |
| окружающая среда | environment |
| *другие* | top |

### Поддерживаемые языки (38 языков)

NewsData.io поддерживает 38 языков:

| Код | Язык | Код | Язык | Код | Язык |
|-----|------|-----|------|-----|------|
| `ar` | Arabic | `bn` | Bengali | `bg` | Bulgarian |
| `zh` | Chinese | `hr` | Croatian | `cs` | Czech |
| `da` | Danish | `nl` | Dutch | `en` | English |
| `et` | Estonian | `fi` | Finnish | `fr` | French |
| `de` | German | `el` | Greek | `he` | Hebrew |
| `hi` | Hindi | `hu` | Hungarian | `id` | Indonesian |
| `it` | Italian | `ja` | Japanese | `ko` | Korean |
| `lv` | Latvian | `lt` | Lithuanian | `ms` | Malay |
| `no` | Norwegian | `pl` | Polish | `pt` | Portuguese |
| `ro` | Romanian | `ru` | Russian | `sk` | Slovak |
| `sl` | Slovenian | `es` | Spanish | `sv` | Swedish |
| `th` | Thai | `tr` | Turkish | `uk` | Ukrainian |
| `ur` | Urdu | `vi` | Vietnamese | | |

### Поддерживаемые страны (180+ стран)

NewsData.io поддерживает более 180 стран. Основные:

| Код | Страна | Код | Страна | Код | Страна |
|-----|--------|-----|--------|-----|--------|
| `us` | United States | `gb` | United Kingdom | `au` | Australia |
| `ca` | Canada | `de` | Germany | `fr` | France |
| `it` | Italy | `es` | Spain | `nl` | Netherlands |
| `be` | Belgium | `ch` | Switzerland | `at` | Austria |
| `se` | Sweden | `no` | Norway | `dk` | Denmark |
| `fi` | Finland | `pl` | Poland | `cz` | Czech Republic |
| `ru` | Russia | `cn` | China | `jp` | Japan |
| `kr` | South Korea | `in` | India | `br` | Brazil |

## Тестирование

### Быстрый тест

```bash
poetry run python scripts/test_newsdata_quick.py
```

Выполняет базовые проверки:
- Health check
- Получение категорий и языков
- Получение источников
- Получение новостей
- Поиск новостей

### Детальное тестирование

```bash
poetry run python scripts/test_newsdata_provider.py
```

Подробное тестирование с логированием:
- Проверка конфигурации
- Тестирование всех методов
- Обработка ошибок
- Детальные логи

### Что тестируют скрипты

Скрипты выполняют различные тесты с эндпоинтами NewsData.io. Все эндпоинты доступны на всех планах.

#### ТЕСТ 1: Health Check
- **Эндпоинт**: `/api/1/sources` (простой запрос)
- **Доступность**: Все планы
- **Ожидаемый результат**: Должен работать на всех планах
- **Интерпретация**: 
  - ✅ 200 OK - API ключ валидный, подключение работает
  - ❌ 401 Unauthorized - неверный API ключ
  - ❌ 429 Too Many Requests - превышен лимит запросов

#### ТЕСТ 2: Получение источников (`/api/1/sources`)
- **Доступность**: Все планы
- **Ожидаемый результат**: Список доступных источников
- **Интерпретация**: 
  - ✅ 200 OK - источники получены
  - ❌ 401 Unauthorized - неверный API ключ
  - ❌ 429 Too Many Requests - превышен лимит запросов

#### ТЕСТ 3: Получение новостей (`/api/1/latest`)
- **Доступность**: Все планы
- **Ожидаемый результат**: Список новостей
- **Интерпретация**: 
  - ✅ 200 OK - новости получены
  - ❌ 401 Unauthorized - неверный API ключ
  - ❌ 429 Too Many Requests - превышен лимит запросов

#### ТЕСТ 4: Поиск новостей (`/api/1/latest` с параметром q)
- **Доступность**: Все планы
- **Ожидаемый результат**: Результаты поиска
- **Интерпретация**: 
  - ✅ 200 OK - поиск работает
  - ❌ 401 Unauthorized - неверный API ключ
  - ❌ 429 Too Many Requests - превышен лимит запросов

### Интерпретация результатов

#### ✅ Успешное выполнение
```
============================================================
✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!
🎉 NewsData.io провайдер работает корректно!
============================================================
```

**Что это означает:**
- API ключ валидный
- Сетевое подключение работает
- Провайдер корректно обрабатывает запросы и ответы
- Все основные функции работают

#### ❌ Ошибки выполнения
```
============================================================
❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!
💡 Проверьте API ключ и подключение к интернету
============================================================
```

**Возможные причины:**
- Неверный API ключ (401 ошибка)
- Превышен лимит запросов (429 ошибка)
- Отсутствует интернет-соединение
- Проблемы с сервером NewsData.io

### Детальные логи

Скрипты выводят подробную информацию о каждом запросе:

#### Проверка конфигурации
```
📋 NewsData.io настройки: enabled=True, priority=3
🔧 Создаем NewsData.io fetcher...
✅ Fetcher создан: newsdata
```

#### Health Check
```
🏥 Проверка health check...
✅ Health check результат: {'status': 'healthy', 'provider': 'newsdata', 'message': 'NewsData.io is accessible'}
```

#### Получение данных
```
📰 Получение источников...
✅ Найдено источников: 25000+
  - BBC News (bbc-news)
  - CNN (cnn)
  - Reuters (reuters)
  - TechCrunch (techcrunch)
  - The Guardian (the-guardian)
```

### Коды ошибок

| Код | Значение | Действие |
|-----|----------|----------|
| 200 | Успех | ✅ Всё работает |
| 401 | Неверный API ключ | Проверьте ключ в .env |
| 429 | Превышен лимит запросов | Подождите или обновите план |
| 500 | Ошибка сервера | Повторите позже |

### Планы подписки NewsData.io

| План | Стоимость | API кредиты | Статей за кредит | Особенности |
|------|-----------|-------------|------------------|-------------|
| **Free** | Бесплатно | 200/день | 10 | Latest News API |
| **Basic** | $199.99/месяц | 20,000/месяц | 50 | + Crypto News, Archive (6 мес) |
| **Professional** | $349.99/месяц | 50,000/месяц | 50 | + AI Tags, Sentiment (2 года) |
| **Corporate** | $1,299.99/месяц | 1,000,000/месяц | 50 | + AI Region, AI Org (5 лет) |

### Тестирование доступности источников

```bash
poetry run python scripts/test_sources_availability.py --provider newsdata
```

Проверяет доступность различных источников через NewsData.io.

### Настройка параметров

Перед запуском отредактируйте параметры тестов в начале файла в секции **"НАСТРОЙКИ ТЕСТОВ"**:

```python
# Пример настроек для NewsData.io тестов
NEWSDATA_PARAMS = {
    "language": "en",                  # Измените на нужный язык
    "country": "us",                   # Измените на нужную страну
    "category": "technology",          # Категория новостей
    "size": 5,                        # Количество результатов (1-50)
    # "domain": "bbc.com,cnn.com",    # Раскомментируйте для фильтрации
}
```

## Примеры использования доменов в коде

### Автоматическое определение типа домена

```python
from src.services.news.fetchers.newsdata_io import NewsDataIOFetcher
from src.config import get_news_providers_settings

# Получение настроек
settings = get_news_providers_settings()
newsdata_settings = settings.providers.get('newsdata')
fetcher = NewsDataIOFetcher(newsdata_settings)

# Поиск новостей по именам доменов (автоматически использует параметр domain)
news_by_domain = fetcher.fetch_news(
    query="bitcoin",
    domain="cnn,bbc",  # Имена доменов без точки → параметр domain
    limit=5
)

# Поиск новостей по URL доменам (автоматически использует параметр domainurl)
news_by_url = fetcher.fetch_news(
    query="bitcoin",
    domain="edition.cnn.com,bbc.com",  # URL домены с точками → параметр domainurl
    limit=5
)

# Смешанные типы доменов обрабатываются автоматически
mixed_domains = fetcher.fetch_news(
    query="technology",
    domain="cnn,reuters.com,bbc",  # Код определит тип по наличию точки
    limit=10
)
```

### Использование параметра domains

```python
# Параметр domains работает как синоним domain
news_domains = fetcher.fetch_news(
    query="AI",
    domains="techcrunch.com,wired.com",  # Также поддерживается
    limit=5
)
```

### Ограничения для Sources API

```python
# Источники НЕ поддерживают фильтрацию по доменам в базовых планах
sources_basic = fetcher.get_sources(
    country="us",
    category="technology"
    # domain="cnn" - будет игнорироваться
)

# Домены в параметрах sources будут проигнорированы
sources_ignored = fetcher.get_sources(
    domain="cnn.com",  # Этот параметр игнорируется
    country="us"       # Работает только базовая фильтрация
)
```

## Справочник по параметрам API

### Эндпоинт: Latest News (`/api/1/latest`)

**Описание**: Эндпоинт последних новостей предоставляет доступ к последним и экстренным новостям. Новостные статьи сортируются по дате публикации. С эндпоинтом "Latest" вы можете получить доступ к новостным статьям за последние 48 часов.

**URL**: `https://newsdata.io/api/1/latest?apikey=YOUR_API_KEY`

**Доступность**: Все планы

**Лимит запросов**: 1800 кредитов за 15 минут (платные планы)

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `apikey` | ✅ | string | Ваш API ключ для доступа к NewsData API | `your_api_key_here` |
| `id` | ❌ | string | Поиск конкретной статьи по уникальному article_id. До 50 ID в запросе | `article_id`, `id1,id2,id3` |
| `q` | ❌ | string | Поиск по ключевым словам в заголовке, контенте, URL, мета-ключевых словах и мета-описании. Макс. 100 символов | `pizza`, `social AND media`, `"exact phrase"` |
| `qInTitle` | ❌ | string | Поиск только в заголовках статей. Макс. 100 символов. Нельзя использовать с q или qInMeta | `bitcoin`, `AI technology` |
| `qInMeta` | ❌ | string | Поиск в заголовках, URL, мета-ключевых словах и мета-описании. Макс. 100 символов | `crypto`, `machine learning` |
| `timeframe` | ❌ | string | Временной период (часы: 1-48, минуты: 1m-2880m) | `6`, `24`, `15m`, `90m` |
| `country` | ❌ | string | Коды стран через запятую (до 5 стран) | `us`, `us,gb`, `ru,de,fr` |
| `category` | ❌ | string | Категории через запятую (до 5 категорий) | `business`, `technology,science` |
| `excludecategory` | ❌ | string | Исключить категории (до 5). Нельзя использовать с category | `sports`, `entertainment,politics` |
| `language` | ❌ | string | Коды языков через запятую (до 5 языков) | `en`, `en,es`, `ru,de` |
| `tag` | ❌ | string | AI-классифицированные теги (до 5). Только Professional/Corporate | `food,tourism`, `politics` |
| `sentiment` | ❌ | string | Фильтр по тональности. Только Professional/Corporate | `positive`, `negative`, `neutral` |
| `region` | ❌ | string | Географические регионы (до 5). Только Corporate | `los angeles-california-usa`, `new york,chicago` |
| `domain` | ❌ | string | Домены источников (до 5) | `nytimes,bbc`, `cnn,reuters` |
| `domainurl` | ❌ | string | URL доменов источников (до 5) | `nytimes.com,bbc.com`, `cnn.com` |
| `excludedomain` | ❌ | string | Исключить домены (до 5) | `example.com`, `spam.com,fake.com` |
| `excludefield` | ❌ | string | Исключить поля из ответа (кроме articles) | `pubdate`, `source_icon,pubdate,link` |
| `prioritydomain` | ❌ | string | Приоритетные домены | `top`, `medium`, `low` |
| `timezone` | ❌ | string | Часовой пояс для поиска | `America/New_York`, `Asia/Kolkata` |
| `full_content` | ❌ | int | Полный контент статей (1/0) | `1`, `0` |
| `image` | ❌ | int | Статьи с изображениями (1/0) | `1`, `0` |
| `video` | ❌ | int | Статьи с видео (1/0) | `1`, `0` |
| `removeduplicate` | ❌ | int | Удалить дубликаты (1 - удалить) | `1` |
| `size` | ❌ | int | Количество результатов (1-50). Free: макс 10, Paid: макс 50 | `10`, `25`, `50` |
| `page` | ❌ | string | Токен следующей страницы для пагинации | `nextPage_token_here` |

**Дефолтные значения:**
- `size`: `10`
- `language`: Все языки
- `country`: Все страны
- `full_content`: `0`
- `image`: `0`
- `video`: `0`
- `excludeduplicates`: `1`

**Примечание о параметрах доменов:**
- Параметр `domain` (имена доменов) поддерживается в коде провайдера для Latest News и Crypto News
- Параметр `domainurl` (URL доменов) поддерживается в коде провайдера для Latest News и Crypto News
- Код автоматически определяет тип домена по наличию точки и использует соответствующий параметр API
- Для Sources API фильтрация по доменам не поддерживается в базовых планах NewsData.io

### Эндпоинт: Crypto News (`/api/1/crypto`)

**Описание**: Поиск и мониторинг новостей и блогов о криптовалютах со всего мира из самых надежных новостных и блоговых веб-сайтов.

**URL**: `https://newsdata.io/api/1/crypto?apikey=YOUR_API_KEY`

**Доступность**: Basic, Professional, Corporate планы

**Лимит запросов**: 1800 кредитов за 15 минут (платные планы)

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `apikey` | ✅ | string | Ваш API ключ для доступа к NewsData API | `your_api_key_here` |
| `id` | ❌ | string | Поиск конкретной статьи по уникальному article_id. До 50 ID в запросе | `article_id`, `id1,id2,id3` |
| `coin` | ❌ | string | Поиск новостей по конкретным криптовалютам (только короткие формы, до 5 монет) | `btc`, `eth,usdt,bnb` |
| `q` | ❌ | string | Поиск по ключевым словам в заголовке, контенте, URL, мета-данных. Макс. 100 символов | `bitcoin`, `defi AND ethereum` |
| `qInTitle` | ❌ | string | Поиск только в заголовках статей. Макс. 100 символов | `blockchain`, `cryptocurrency` |
| `qInMeta` | ❌ | string | Поиск в заголовках, URL, мета-данных. Макс. 100 символов | `crypto`, `nft` |
| `timeframe` | ❌ | string | Временной период (часы: 1-48, минуты: 1m-2880m) | `6`, `24`, `15m`, `90m` |
| `from_date` | ❌ | string | Дата начала (YYYY-MM-DD или YYYY-MM-DD HH:MM:SS) | `2025-01-01`, `2025-01-01 06:12:45` |
| `to_date` | ❌ | string | Дата окончания (YYYY-MM-DD или YYYY-MM-DD HH:MM:SS) | `2025-01-30`, `2025-01-30 18:00:00` |
| `language` | ❌ | string | Коды языков через запятую (до 5 языков) | `en`, `en,es,fr` |
| `tag` | ❌ | string | AI-классифицированные теги (до 5). Только Professional/Corporate | `blockchain`, `defi,nft` |
| `sentiment` | ❌ | string | Фильтр по тональности. Только Professional/Corporate | `positive`, `negative`, `neutral` |
| `domain` | ❌ | string | Домены источников (до 5) | `coindesk,cointelegraph`, `decrypt` |
| `domainurl` | ❌ | string | URL доменов источников (до 5) | `coindesk.com,cointelegraph.com` |
| `excludedomain` | ❌ | string | Исключить домены (до 5) | `spam.com,fake.com` |
| `excludefield` | ❌ | string | Исключить поля из ответа (кроме articles) | `pubdate`, `source_icon,link` |
| `prioritydomain` | ❌ | string | Приоритетные домены | `top`, `medium`, `low` |
| `timezone` | ❌ | string | Часовой пояс для поиска | `America/New_York`, `UTC` |
| `full_content` | ❌ | int | Полный контент статей (1/0) | `1`, `0` |
| `image` | ❌ | int | Статьи с изображениями (1/0) | `1`, `0` |
| `video` | ❌ | int | Статьи с видео (1/0) | `1`, `0` |
| `removeduplicate` | ❌ | int | Удалить дубликаты (1 - удалить) | `1` |
| `size` | ❌ | int | Количество результатов (1-50). Paid: макс 50 | `10`, `25`, `50` |
| `page` | ❌ | string | Токен следующей страницы для пагинации | `nextPage_token_here` |

**Дополнительные поля ответа для Crypto News:**
- `coin` - символы криптовалют, упомянутых в статье (только для Crypto endpoint)
- `pubDateTZ` - часовой пояс даты публикации

### Эндпоинт: News Archive (`/api/1/archive`)

**Описание**: Эндпоинт архива новостей предоставляет доступ к старым новостным данным по теме, событию, стране, конкретной категории в стране или для одного или нескольких доменов. Позволяет получать прошлые новостные данные для исследований и анализа.

**URL**: `https://newsdata.io/api/1/archive?apikey=YOUR_API_KEY&from_date=2025-03-13&to_date=2025-03-26&category=technology`

**Доступность**: Basic (6 месяцев), Professional (2 года), Corporate (5 лет)

**Лимит запросов**: 1800 кредитов за 15 минут (платные планы)

**Требование**: Запрос должен содержать хотя бы один из параметров: `q`, `qInTitle`, `qInMeta`, `domain`, `country`, `category`, `language`, `full_content`, `image`, `video`, `prioritydomain`, `domainurl`

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `apikey` | ✅ | string | Ваш API ключ для доступа к NewsData API | `your_api_key_here` |
| `id` | ❌ | string | Поиск конкретной статьи по уникальному article_id. До 50 ID в запросе | `article_id`, `id1,id2,id3` |
| `q` | ❌ | string | Поиск по ключевым словам в заголовке, контенте, URL, мета-данных. Макс. 100 символов | `covid`, `climate change` |
| `qInTitle` | ❌ | string | Поиск только в заголовках статей. Макс. 100 символов | `election`, `technology` |
| `qInMeta` | ❌ | string | Поиск в заголовках, URL, мета-данных. Макс. 100 символов | `sports`, `business` |
| `from_date` | ❌ | string | Дата начала (YYYY-MM-DD или YYYY-MM-DD HH:MM:SS) | `2024-01-01`, `2024-06-15 10:00:00` |
| `to_date` | ❌ | string | Дата окончания (YYYY-MM-DD или YYYY-MM-DD HH:MM:SS) | `2024-12-31`, `2024-06-20 23:59:59` |
| `language` | ❌ | string | Коды языков через запятую (до 5 языков) | `en`, `ru,de,fr` |
| `country` | ❌ | string | Коды стран через запятую (до 5 стран) | `us`, `ru,gb,de` |
| `category` | ❌ | string | Категории через запятую (до 5 категорий) | `politics`, `technology,science` |
| `excludecategory` | ❌ | string | Исключить категории (до 5). Нельзя использовать с category | `sports`, `entertainment` |
| `domain` | ❌ | string | Домены источников (до 5) | `bbc,cnn`, `reuters,ap` |
| `domainurl` | ❌ | string | URL доменов источников (до 5) | `bbc.com,cnn.com`, `reuters.com` |
| `excludedomain` | ❌ | string | Исключить домены (до 5) | `spam.com`, `unreliable.com` |
| `excludefield` | ❌ | string | Исключить поля из ответа (кроме articles) | `pubdate`, `source_icon,link` |
| `prioritydomain` | ❌ | string | Приоритетные домены | `top`, `medium`, `low` |
| `timezone` | ❌ | string | Часовой пояс для поиска | `Europe/London`, `Asia/Tokyo` |
| `full_content` | ❌ | int | Полный контент статей (1/0) | `1`, `0` |
| `image` | ❌ | int | Статьи с изображениями (1/0) | `1`, `0` |
| `video` | ❌ | int | Статьи с видео (1/0) | `1`, `0` |
| `size` | ❌ | int | Количество результатов (1-50). Paid: макс 50 | `10`, `25`, `50` |
| `page` | ❌ | string | Токен следующей страницы для пагинации | `nextPage_token_here` |

### Эндпоинт: Sources (`/api/1/sources`)

**Описание**: Эндпоинт источников предоставляет названия случайно выбранных 100 доменов из страны, категории и/или языка. Это в основном удобный эндпоинт, который вы можете использовать для отслеживания издателей, доступных в API.

**URL**: `https://newsdata.io/api/1/sources?apikey=YOUR_API_KEY`

**Доступность**: Все планы

**Лимит запросов**: 1800 кредитов за 15 минут (платные планы)

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `apikey` | ✅ | string | Ваш API ключ для доступа к NewsData API | `your_api_key_here` |
| `language` | ❌ | string | Коды языков через запятую (до 5 языков) | `en`, `ru,de`, `es,fr,it` |
| `country` | ❌ | string | Коды стран через запятую (до 5 стран) | `us`, `gb,de`, `ru,fr,it` |
| `category` | ❌ | string | Категории через запятую (до 5 категорий) | `business`, `technology,science` |
| `domainurl` | ❌ | string | Поиск источников по конкретным доменам (до 5). Если домен неверный, API даст предложения | `nytimes.com,bbc.com`, `cnn.com,reuters.com` |
| `prioritydomain` | ❌ | string | Источники только из топ новостных доменов | `top`, `medium`, `low` |

**Поля ответа Sources:**

| Поле | Описание |
|------|----------|
| `status` | success/error - статус запроса |
| `id` | Идентификатор домена (можно использовать с другими эндпоинтами) |
| `name` | Название домена (определяется модераторами NewsData.io) |
| `url` | URL домена |
| `category` | Категории домена (определяются модераторами NewsData.io) |
| `language` | Язык домена (определяется модераторами NewsData.io) |
| `country` | Страны домена (определяются модераторами NewsData.io) |

**Дефолтные значения:** Все параметры необязательны (None)

## Расширенный поиск

NewsData.io поддерживает расширенный поиск с использованием операторов для параметров `q`, `qInTitle` и `qInMeta`. **Максимальная длина запроса: 100 символов** (включая операторы, скобки и пробелы).

### Операторы поиска

| Операция | Синтаксис | Пример | Описание |
|----------|-----------|--------|----------|
| **Одно ключевое слово** | `q=keyword` | `q=social` | Поиск статей содержащих слово "social" |
| **Точная фраза** | `q="exact phrase"` | `q="social pizza"` | Поиск точной фразы "social pizza" |
| **И (AND)** | `q=word1 AND word2` | `q=social AND pizza AND pasta` | Все слова должны присутствовать |
| **НЕ (NOT)** | `q=word1 NOT word2` | `q=social NOT pizza` | Исключить статьи со словом "pizza" |
| **Исключить несколько** | `q=word1 NOT (word2 AND word3)` | `q=social NOT (pizza AND wildfire)` | Исключить статьи с "pizza" И "wildfire" |
| **ИЛИ (OR)** | `q=word1 OR word2` | `q=social OR pizza OR pasta` | Любое из слов должно присутствовать |
| **Комбинированный** | `q=(word1 OR word2) NOT word3` | `q=(pizza OR social) NOT pasta` | Сложные логические выражения |

### Примеры запросов

#### Latest News примеры

```bash
# Новости из Австралии и США
https://newsdata.io/api/1/latest?apikey=YOUR_API_KEY&country=au,us

# Новости с доменов BBC
https://newsdata.io/api/1/latest?apikey=YOUR_API_KEY&domain=bbc

# Новости категории "наука"
https://newsdata.io/api/1/latest?apikey=YOUR_API_KEY&category=science

# Поиск с операторами
https://newsdata.io/api/1/latest?apikey=YOUR_API_KEY&q=bitcoin AND (price OR value)

# Временной период - последние 6 часов
https://newsdata.io/api/1/latest?apikey=YOUR_API_KEY&timeframe=6&category=technology
```

#### Crypto News примеры

```bash
# Новости только о Bitcoin
https://newsdata.io/api/1/crypto?apikey=YOUR_API_KEY&coin=btc

# Крипто-новости на итальянском и японском
https://newsdata.io/api/1/crypto?apikey=YOUR_API_KEY&language=it,jp

# Новости с домена CoinDesk
https://newsdata.io/api/1/crypto?apikey=YOUR_API_KEY&domainurl=coindesk.com
```

#### Archive примеры

```bash
# Новости категорий "технологии" и "наука"
https://newsdata.io/api/1/archive?apikey=YOUR_API_KEY&category=technology,science

# Новости с 29 июня по 12 июля 2025
https://newsdata.io/api/1/archive?apikey=YOUR_API_KEY&from_date=2025-06-29&to_date=2025-07-12&category=technology

# Новости с 13 июня 2025 до настоящего времени
https://newsdata.io/api/1/archive?apikey=YOUR_API_KEY&from_date=2025-06-13&category=science
```

#### Sources примеры

```bash
# Источники из конкретной страны
https://newsdata.io/api/1/sources?apikey=YOUR_API_KEY&country=ua

# Источники конкретной категории
https://newsdata.io/api/1/sources?apikey=YOUR_API_KEY&category=politics

# Источники на определенном языке
https://newsdata.io/api/1/sources?apikey=YOUR_API_KEY&language=nl
```

### Поддерживаемые категории (12 категорий)

NewsData.io поддерживает следующие категории:

- `business` - Бизнес и финансы
- `entertainment` - Развлечения
- `environment` - Окружающая среда
- `food` - Еда и кулинария
- `health` - Здоровье и медицина
- `politics` - Политика
- `science` - Наука и технологии
- `sports` - Спорт
- `technology` - Технологии
- `top` - Топ новости
- `tourism` - Туризм и путешествия
- `world` - Мировые новости

### Тарифные планы и ограничения

#### Планы подписки

| План | Стоимость | API кредиты | Статей за кредит | Лимит запросов | Исторические данные |
|------|-----------|-------------|------------------|----------------|---------------------|
| **Free** | Бесплатно | 200/день | 10 | 30 кредитов/15 мин | Нет |
| **Basic** | $199.99/месяц | 20,000/месяц | 50 | 1800 кредитов/15 мин | 6 месяцев |
| **Professional** | $349.99/месяц | 50,000/месяц | 50 | 1800 кредитов/15 мин | 2 года |
| **Corporate** | $1,299.99/месяц | 1,000,000/месяц | 50 | 1800 кредитов/15 мин | 5 лет |

#### Доступность функций по планам

| Функция | Free | Basic | Professional | Corporate |
|---------|------|-------|--------------|-----------|
| **Latest News API** | ✅ | ✅ | ✅ | ✅ |
| **Crypto News API** | ❌ | ✅ | ✅ | ✅ |
| **News Archive API** | ❌ | ✅ | ✅ | ✅ |
| **AI Tags** | ❌ | ❌ | ✅ | ✅ |
| **Sentiment Analysis** | ❌ | ❌ | ✅ | ✅ |
| **AI Region** | ❌ | ❌ | ❌ | ✅ |
| **AI Organization** | ❌ | ❌ | ❌ | ✅ |
| **Real-time availability** | ❌ | ✅ | ✅ | ✅ |
| **AI Summary (скоро)** | ❌ | ✅ | ✅ | ✅ |
| **AI Content (скоро)** | ❌ | ❌ | ✅ | ✅ |
| **Query Limit (символы)** | 100 | 100 | 256 | 512 |
| **Поддержка** | Базовая | Базовая | Выделенная | Выделенная |

#### Ограничения бесплатного плана

- **200 запросов в день** (~6,000 в месяц)
- **Только последние 30 дней** данных
- **Базовые параметры** фильтрации
- **Без полного контента** статей
- **Rate limiting**: 1 запрос в секунду

#### Лимиты запросов

- **Rate Limit**: 1 запрос в секунду для всех планов
- **Timeout**: 30 секунд на запрос
- **Максимальный размер ответа**: 10MB
- **Максимальная длина запроса**: 500 символов

#### Статус коды ошибок

| Код | Описание | Причина | Решение |
|-----|----------|---------|---------|
| 200 | Успех | Запрос выполнен | - |
| 400 | Неверный запрос | Неправильные параметры | Проверьте параметры запроса |
| 401 | Неавторизован | Неверный API ключ | Проверьте ключ в .env |
| 429 | Превышен лимит | Слишком много запросов | Подождите или обновите план |
| 500 | Ошибка сервера | Внутренняя ошибка API | Повторите запрос позже |

#### Форматы данных

**Дата и время:**
- Формат: ISO 8601 (`YYYY-MM-DD HH:MM:SS`)
- Часовой пояс: UTC
- Примеры: `2025-01-15 10:30:00`, `2025-01-15`

**Поля ответа статей:**
- `article_id` - уникальный идентификатор статьи
- `title` - заголовок статьи
- `link` - ссылка на оригинальную статью
- `keywords` - ключевые слова статьи (массив)
- `creator` - автор статьи (массив)
- `video_url` - ссылка на видео (если есть)
- `description` - описание статьи
- `content` - полный контент (только для платных планов)
- `pubDate` - дата и время публикации
- `image_url` - ссылка на изображение
- `source_id` - идентификатор источника
- `source_priority` - приоритет источника
- `country` - страна источника (массив)
- `category` - категория статьи (массив)
- `language` - язык статьи
- `ai_tag` - AI-генерированные теги
- `sentiment` - анализ тональности
- `sentiment_stats` - статистика тональности
- `duplicate` - статус дубликата

**Поля ответа источников:**
- `id` - уникальный идентификатор источника
- `name` - название источника
- `url` - официальный сайт источника
- `description` - описание источника
- `category` - категория источника (массив)
- `language` - язык источника (массив)
- `country` - страна источника (массив)
- `status` - статус источника (active/inactive)

## Ограничения

### Бесплатный план

- 200 запросов в день
- Только новости за последние 30 дней
- Нет доступа к полному контенту
- Ограничение по rate limit (1 запрос/сек)

### Технические ограничения

- Максимум 50 статей за запрос
- Некоторые источники могут быть недоступны
- Задержки в обновлении новостей
- Ограничения по геолокации

## Обработка ошибок

Провайдер обрабатывает следующие типы ошибок:

1. **NewsDataAPIException** - Ошибки API
2. **RequestException** - Сетевые ошибки
3. **ValueError** - Ошибки валидации
4. **KeyError** - Ошибки структуры данных

Все ошибки логируются и возвращаются в стандартном формате.

## Примеры использования

### Получение новостей по рубрикам

```python
from src.services.news.fetcher_fabric import create_news_fetcher_from_config

# Создание fetcher'а
fetcher = create_news_fetcher_from_config("newsdata")

# Получение новостей
news = fetcher.fetch_news(["технологии", "спорт"])
print(f"Найдено {len(news)} новостей")
```

### Поиск новостей

```python
# Поиск по ключевым словам
search_results = fetcher.search_news(
    query="искусственный интеллект",
    language="ru",
    limit=20
)
```

### Получение источников

```python
# Получение всех источников
sources = fetcher.get_sources()
print(f"Доступно {len(sources['data'])} источников")

# Фильтрация по категории и стране
tech_sources = fetcher.get_sources(category="technology", country="us")
```

## Стандартизация данных

Провайдер автоматически стандартизирует данные NewsData.io под общий формат:

### Структура ответа NewsData.io

#### Поля ответа для всех эндпоинтов

| Поле | Описание | Доступность |
|------|----------|-------------|
| `status` | Статус запроса ("success" или "error") | Все планы |
| `totalResults` | Общее количество результатов для запроса | Все планы |
| `article_id` | Уникальный идентификатор новостной статьи | Все планы |
| `title` | Заголовок новостной статьи | Все планы |
| `link` | URL новостной статьи | Все планы |
| `source_id` | Идентификатор источника статьи | Все планы |
| `source_name` | Название источника | Все планы |
| `source_url` | URL источника | Все планы |
| `source_icon` | URL логотипа источника | Все планы |
| `source_priority` | Ранг доменов по трафику и достоверности (чем меньше число, тем достовернее) | Все планы |
| `keywords` | Связанные ключевые слова статьи | Все планы |
| `creator` | Автор новостной статьи | Все планы |
| `image_url` | URL изображения в статье | Все планы |
| `video_url` | URL видео в статье | Все планы |
| `description` | Краткое описание статьи | Все планы |
| `pubDate` | Дата публикации статьи | Все планы |
| `pubDateTZ` | Часовой пояс даты публикации | Все планы |
| `content` | Полное содержание статьи | Все планы |
| `country` | Страна издателя | Все планы |
| `category` | Категория, присвоенная статье NewsData.io | Все планы |
| `language` | Язык новостной статьи | Все планы |
| `ai_tag` | AI-классифицированные теги для лучшего понимания статьи | Professional, Corporate |
| `sentiment` | Общая тональность статьи (positive, negative, neutral) | Professional, Corporate |
| `sentiment_stats` | Статистика распределения тональности | Professional, Corporate |
| `ai_region` | AI-классифицированный географический регион статьи | Corporate |
| `ai_org` | AI-классифицированные организации, упомянутые в статье | Corporate |
| `duplicate` | Индикатор дубликата статьи (true/false) | Все планы |
| `coin` | Символы криптовалют, упомянутых в статье | Crypto endpoint |
| `nextPage` | Токен для перехода к следующей странице | Все планы |

#### Пример структуры статьи

```json
{
    "status": "success",
    "totalResults": 1495,
    "results": [
        {
            "article_id": "465ed7ead13ab7aad6b95bb0471feae7",
            "title": "Заголовок новостной статьи",
            "link": "https://example.com/article",
            "keywords": ["технологии", "AI", "инновации"],
            "creator": ["Имя Автора"],
            "description": "Краткое описание статьи...",
            "content": "Полное содержание статьи...",
            "pubDate": "2025-07-12 06:55:30",
            "pubDateTZ": "UTC",
            "image_url": "https://example.com/image.jpg",
            "video_url": null,
            "source_id": "source_identifier",
            "source_name": "Название Источника",
            "source_priority": 1039,
            "source_url": "https://source.com",
            "source_icon": "https://source.com/icon.png",
            "language": "russian",
            "country": ["russia"],
            "category": ["technology"],
            "sentiment": "neutral",
            "sentiment_stats": {
                "positive": 1.89,
                "neutral": 86.69,
                "negative": 11.42
            },
            "ai_tag": ["технологии"],
            "ai_region": ["москва,россия,европа"],
            "ai_org": ["компания xyz"],
            "duplicate": false,
            "coin": ["btc", "eth"]
        }
    ],
    "nextPage": "next_page_token_here"
}
```

### Структура источника

```python
{
    "id": "source_id",
    "name": "Название источника",
    "description": "Описание источника",
    "url": "https://source.com",
    "categories": ["technology", "science"],
    "languages": ["en", "ru"],
    "countries": ["us", "gb"],
    "status": "active"
}
```

## Пагинация

NewsData.io использует пагинацию для разбивки больших наборов результатов на управляемые части. По умолчанию размер страницы составляет **10 статей для бесплатного плана** и **50 статей для платных планов**.

### Как работает пагинация

```bash
# Первый запрос (по умолчанию получаете первую страницу)
https://newsdata.io/api/1/latest?apikey=YOUR_API_KEY&q=YOUR_QUERY

# Для перехода к следующей странице используйте токен nextPage из ответа
https://newsdata.io/api/1/latest?apikey=YOUR_API_KEY&q=YOUR_QUERY&page=XXXPPPXXXXXXXXXX
```

### Важные особенности пагинации

- **Только вперед**: Вы можете переходить только к следующей странице от текущей
- **Сохранение токенов**: Для возврата к предыдущим страницам сохраняйте токены `nextPage` в базе данных
- **Время жизни**: Токены пагинации имеют ограниченное время жизни

### Пример работы с пагинацией в Python

```python
from newsdataapi import NewsDataApiClient

api = NewsDataApiClient(apikey="YOUR_API_KEY")
page = None
all_articles = []

while True:
    response = api.news_api(q="bitcoin", page=page)
    
    if response.get("results"):
        all_articles.extend(response["results"])
    
    page = response.get('nextPage')
    if not page:
        break

print(f"Собрано {len(all_articles)} статей")
```

## Аутентификация

NewsData.io использует аутентификацию по API ключу для доступа к функциям и данным платформы. API ключ - это уникальная строка символов, которая генерируется для каждой учетной записи и требуется во всех запросах к API.

### Способы передачи API ключа

1. **Query parameter** (рекомендуется):
```bash
https://newsdata.io/api/1/latest?apikey=YOUR_API_KEY&q=bitcoin
```

2. **Request header**:
```bash
curl -H "X-ACCESS-KEY: YOUR_API_KEY" "https://newsdata.io/api/1/latest?q=bitcoin"
```

### Ошибки аутентификации

- **403 Unauthorized**: API ключ отсутствует или недействителен
- **429 Too Many Requests**: Превышен лимит запросов для вашего плана

## Rate Limiting (Ограничения запросов)

NewsData.io имеет ограничения на количество запросов для обеспечения доступности API для всех пользователей.

### Лимиты по планам

| План | Лимит запросов |
|------|----------------|
| **Free** | 30 кредитов каждые 15 минут |
| **Платные планы** | 1800 кредитов каждые 15 минут |

### Обработка превышения лимитов

При превышении лимита API вернет ошибку **"Rate Limit Exceeded"**, и вы не сможете делать дальнейшие запросы до сброса лимита через 15 минут.

### Мониторинг использования

Отслеживайте лимит API кредитов и контролируйте использование API в вашей учетной записи NewsData.io.

## HTTP коды ответов

| Код | Результат | Описание | Решение |
|-----|-----------|----------|---------|
| **200** | Успешная операция | Запрос API выполнен успешно | - |
| **400** | Отсутствует параметр | Запрос API неправильно сформирован или содержит недопустимые параметры | Проверьте параметры запроса |
| **401** | Неавторизован | API ключ недействителен или отсутствует | Проверьте правильность API ключа |
| **403** | CORS policy failed | IP/домен ограничен | Проверьте настройки CORS |
| **409** | Дублирование параметра | Параметр передан с дублирующимся значением | Убедитесь, что каждый параметр уникален |
| **415** | Неподдерживаемый тип | API не может обработать запрос из-за неподдерживаемого формата | Проверьте формат запроса |
| **422** | Необрабатываемая сущность | Семантическая ошибка в запросе | Проверьте логику запроса |
| **429** | Слишком много запросов | Превышен лимит запросов для вашего плана | Дождитесь сброса лимита |
| **500** | Внутренняя ошибка сервера | Неожиданная ошибка на сервере | Повторите запрос позже |

## Клиентские библиотеки

NewsData.io предоставляет официальные клиентские библиотеки для упрощения интеграции с API.

### Python Client

**Установка:**
```bash
pip install newsdataapi
```

**Использование:**
```python
from newsdataapi import NewsDataApiClient

# Инициализация клиента с API ключом
api = NewsDataApiClient(apikey="YOUR_API_KEY")

# Получение новостей (можете передать пустые параметры или с фильтрами)
response = api.news_api(q="bitcoin", country="us")
```

**Пагинация в Python:**
```python
from newsdataapi import NewsDataApiClient

api = NewsDataApiClient(apikey="YOUR_API_KEY")
page = None

while True:
    response = api.news_api(page=page)
    page = response.get('nextPage', None)
    if not page:
        break
```

### React Client

**Установка:**
```bash
npm install newsdataapi
```

**Использование:**
```javascript
import useNewsDataApiClient from "newsdataapi";

// Инициализация клиента с API ключом
const { latest } = useNewsDataApiClient("YOUR_API_KEY");

// Получение новостей
const data = await latest({ q: "bitcoin", country: "us" });
```

**Пагинация в React:**
```javascript
import useNewsDataApiClient from "newsdataapi";

const { latest } = useNewsDataApiClient("YOUR_API_KEY");
let allNews = [];
let nextPage;

while (true) {
    const params = { q: "bitcoin", country: "us" };
    if (nextPage) params.page = nextPage;
    
    const data = await latest(params);
    
    if (data?.results?.length) {
        allNews.push(...data.results);
    }
    
    if (!data.nextPage) break;
    nextPage = data.nextPage;
}
```

### PHP Client

**Установка:**
```bash
composer require newsdataio/newsdataapi
```

**Использование:**
```php
<?php
require_once '../autoload.php';
use NewsdataIO\NewsdataApi;

$newsdataApiObj = new NewsdataApi("YOUR_API_KEY");

// Передача параметров в массиве с уникальными ключами
$data = array("q" => "bitcoin", "country" => "us");
$response = $newsdataApiObj->get_latest_news($data);
?>
```

## Отладка

### Включение подробного логирования

```python
import logging
logging.getLogger("newsdata").setLevel(logging.DEBUG)
```

### Проверка конфигурации

```python
from src.config import get_news_providers_settings

settings = get_news_providers_settings()
print(settings.providers["newsdata"])
```

### Тестирование подключения

```python
fetcher = create_news_fetcher_from_config("newsdata")
health = fetcher.check_health()
print(f"Статус: {health['status']}")
```

## Полезные ссылки

### Официальные ресурсы
- [Официальная документация NewsData.io](https://newsdata.io/documentation)
- [Регистрация и получение API ключа](https://newsdata.io/register)
- [Тарифные планы и цены](https://newsdata.io/pricing)
- [Статус сервиса NewsData.io](https://status.newsdata.io/)
- [Поддержка и контакты](https://newsdata.io/contact)

### Клиентские библиотеки
- [Python Client Library](https://pypi.org/project/newsdataapi/)
- [React Client Library](https://www.npmjs.com/package/newsdataapi)
- [PHP Client Library](https://packagist.org/packages/newsdataio/newsdataapi)

### Блог и примеры
- [Получение API ключа NewsData.io](https://newsdata.io/blog/how-to-get-your-newsdata-io-news-api-key)
- [Первый запрос к NewsData.io](https://newsdata.io/blog/how-to-make-your-first-request-with-newsdata-io)
- [Пагинация в NewsData.io API](https://newsdata.io/blog/all-about-pagination-in-newsdata-io-news-api)
- [Использование параметров q, qInTitle и qInMeta](https://newsdata.io/blog/how-to-use-q-qintitle-and-qinmeta-parameters)
- [Latest News Endpoint подробно](https://newsdata.io/blog/get-latest-news-using-newsdata-io-news-endpoint-in-detail)
- [Crypto News API Endpoints](https://newsdata.io/blog/crypto-news-api-endpoints)
- [News Archive Endpoint](https://newsdata.io/blog/all-about-news-archive-endpoint)
- [News Sources Endpoints](https://newsdata.io/blog/news-sources-endpoints)
- [Rate Limit NewsData.io](https://newsdata.io/blog/rate-limit-of-newsdata-io)
- [Как потребляются API кредиты](https://newsdata.io/blog/how-newsdata-io-credits-are-consumed)
- [NewsData.io с Python Client](https://newsdata.io/blog/newsdata-io-news-api-with-python-client)
- [NewsData.io с React Client](https://newsdata.io/blog/newsdata-io-news-api-with-react-client)
- [Интеграция бесплатного News API](https://newsdata.io/blog/integrate-free-news-api-into-your-application/)

### Справочники
- [Коды стран](https://newsdata.io/documentation#country-codes)
- [Коды языков](https://newsdata.io/documentation#language-codes)
- [Коды категорий](https://newsdata.io/documentation#category-codes)
- [AI теги](https://newsdata.io/documentation#ai-tags)
- [Криптовалютные AI теги](https://newsdata.io/documentation#crypto-ai-tags)
- [Часовые пояса](https://newsdata.io/documentation#timezones)
- [Домены источников](https://newsdata.io/documentation#news-sources)

## Сравнение с другими провайдерами

| Критерий | NewsData.io | TheNewsAPI | NewsAPI.org |
|----------|-------------|------------|-------------|
| **Бесплатные запросы** | 200/день | 100/день | 1000/день |
| **Стоимость платного плана** | $199.99-1299.99/месяц | $15-199/месяц | $449/месяц |
| **Количество источников** | 84,770+ | 50,000+ | 80,000+ |
| **Поддерживаемые языки** | 89 | 50+ | 14 |
| **Поддерживаемые страны** | 206 | 150+ | 54 |
| **Исторические данные** | Да (до 5 лет) | Да (до 5 лет) | Нет |
| **Анализ тональности** | Да (Pro/Corp) | Нет | Нет |
| **AI теги и регионы** | Да (Pro/Corp) | Нет | Нет |
| **Поддержка криптовалют** | Да | Нет | Нет |
| **Archive API** | Да (платные) | Да | Нет |
| **Расширенный поиск** | Да (AND/OR/NOT) | Да | Да |
| **Лимит символов запроса** | 100-512 | 100 | 500 |
| **Пагинация** | Токены | Offset | Страницы |
| **Приоритет в проекте** | Средний | Высокий | Низкий |

## Устранение неполадок

### Ошибка аутентификации

```
Error: 401 Unauthorized
```

**Решение**: Проверьте правильность API ключа в `.env` файле.

### Превышение лимитов

```
Error: 429 Too Many Requests
```

**Решение**: Дождитесь сброса лимитов или обновите план.

### Пустые результаты

```
Warning: No articles found
```

**Возможные причины**:
- Слишком специфический запрос
- Неподдерживаемый язык/страна
- Отсутствие новостей по теме

### Ошибки сети

```
Error: Connection timeout
```

**Решение**: Проверьте интернет соединение и статус API.

### Устранение неполадок

#### Проблема: "No module named 'newsdataapi'"
```bash
poetry install
```

#### Проблема: "NEWSDATA_API_KEY not found"
1. Проверьте наличие файла `.env` в корне проекта
2. Убедитесь, что API ключ указан правильно
3. Перезапустите скрипт

#### Проблема: Все запросы возвращают 401
- Проверьте правильность API ключа
- Убедитесь, что ключ активен на NewsData.io
- Проверьте, что ключ не истек

#### Проблема: Ошибка 429 (Too Many Requests)
- Превышен лимит запросов (200/день на бесплатном плане)
- Подождите до следующего дня или обновите план
- Проверьте количество оставшихся запросов в личном кабинете

#### Проблема: Timeout ошибки
- Проверьте интернет-соединение
- Убедитесь, что нет блокировки файрвола
- Попробуйте позже (возможны проблемы с сервером)

#### Проблема: Пустые результаты поиска
- Попробуйте более общие ключевые слова
- Проверьте правильность параметров фильтрации
- Убедитесь, что новости по теме существуют

#### Проблема: Ошибки парсинга дат
- Убедитесь, что даты в формате YYYY-MM-DD
- Проверьте, что даты не старше 30 дней (ограничение API)
- Используйте UTC время зону

#### Проблема: Отсутствие полного контента
- Полный контент доступен только на платных планах
- Используйте параметр `full_content=1` для платных планов
- Проверьте, что ваш план поддерживает эту функцию 