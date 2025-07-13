# MediaStack API Provider Documentation

Документация для провайдера MediaStack в системе coffee-grinder-v2.

## Обзор

MediaStack - это современный сервис для получения новостей в реальном времени со всего мира. MediaStack собирает новости из более чем **7,500 источников новостей**, которые охватывают около **50 стран** на **13 языках**. API предоставляет доступ к миллионам новостных статей с возможностью поиска и фильтрации.

Провайдер предоставляет доступ к:
- **Live News API** - актуальные новости в реальном времени (с задержкой 30 минут на Free плане)
- **Historical News API** - архивные данные (Standard+ планы)
- **News Sources API** - информация об источниках новостей
- **Расширенный поиск** - по ключевым словам, категориям, странам, языкам
- **Фильтрация** - по источникам, датам, сортировке

## Настройка

### 1. Получение API ключа

1. Зарегистрируйтесь на [MediaStack](https://mediastack.com/)
2. Подтвердите email
3. Получите Access Key в личном кабинете
4. Выберите подходящий тарифный план

### 2. Конфигурация

Добавьте настройки в файл `.env`:
```bash
# MediaStack настройки
MEDIASTACK_API_KEY=your_access_key_here
```

Настройки провайдера в `src/config.py`:
```python
"mediastack": {
    "enabled": True,
    "priority": 4,
    "access_key": os.getenv("MEDIASTACK_API_KEY"),
    "base_url": "https://api.mediastack.com/v1",
    "page_size": 25
}
```

### 3. Параметры конфигурации

- **enabled**: Включить/выключить провайдер
- **priority**: Приоритет провайдера (1-10, где 4 = четвертый по приоритету)
- **access_key**: Access Key от MediaStack
- **base_url**: Базовый URL API (обычно не меняется)
- **page_size**: Количество статей за запрос (макс. 100)

## Возможности провайдера

### Поддерживаемые методы

1. **fetch_news(rubrics)** - Получение новостей по рубрикам
2. **fetch_headlines()** - Получение топ заголовков
3. **fetch_all_news()** - Получение всех новостей
4. **fetch_top_stories()** - Получение топ историй
5. **fetch_historical_news()** - Получение исторических новостей
6. **search_news(query, **kwargs)** - Поиск новостей по запросу
7. **get_sources()** - Получение доступных источников
8. **check_health()** - Проверка состояния провайдера
9. **get_categories()** - Получение поддерживаемых категорий
10. **get_languages()** - Получение поддерживаемых языков
11. **get_supported_countries()** - Получение поддерживаемых стран

### Эндпоинты MediaStack

MediaStack предоставляет два основных эндпоинта для получения новостей:

#### 1. Live News API (`/v1/news`)
- **Использование**: Получение актуальных новостей с фильтрацией
- **Методы провайдера**: `fetch_news()`, `search_news()`, `fetch_headlines()`, `fetch_all_news()`, `fetch_top_stories()`
- **Доступность**: Все планы
- **Особенности**: Универсальный эндпоинт с множеством параметров фильтрации
- **Задержка**: 30 минут на Free плане, реальное время на Standard+

#### 2. Historical News API (`/v1/news` с параметром date)
- **Использование**: Получение исторических новостей
- **Метод провайдера**: `fetch_historical_news()`
- **Доступность**: Standard+ планы
- **Особенности**: Доступ к архивным данным

#### 3. Sources API (`/v1/sources`)
- **Использование**: Получение списка доступных источников
- **Метод провайдера**: `get_sources()`
- **Доступность**: Все планы
- **Особенности**: Информация об источниках с метаданными

### Маппинг рубрик

Рубрики coffee-grinder автоматически маппятся в категории MediaStack:

| Рубрика | MediaStack категория |
|---------|---------------------|
| политика | general |
| экономика | business |
| технологии | technology |
| спорт | sports |
| здоровье | health |
| наука | science |
| развлечения | entertainment |
| *другие* | general |

### Поддерживаемые языки (13 языков)

MediaStack поддерживает 13 языков:

| Код | Язык | Код | Язык | Код | Язык |
|-----|------|-----|------|-----|------|
| `ar` | Arabic | `de` | German | `en` | English |
| `es` | Spanish | `fr` | French | `he` | Hebrew |
| `it` | Italian | `nl` | Dutch | `no` | Norwegian |
| `pt` | Portuguese | `ru` | Russian | `se` | Swedish |
| `zh` | Chinese | | | | |

### Поддерживаемые страны (50+ стран)

MediaStack поддерживает более 50 стран. Основные:

| Код | Страна | Код | Страна | Код | Страна |
|-----|--------|-----|--------|-----|--------|
| `us` | United States | `gb` | United Kingdom | `au` | Australia |
| `ca` | Canada | `de` | Germany | `fr` | France |
| `it` | Italy | `es` | Spain | `nl` | Netherlands |
| `be` | Belgium | `ch` | Switzerland | `at` | Austria |
| `se` | Sweden | `no` | Norway | `dk` | Denmark |
| `fi` | Finland | `pl` | Poland | `cz` | Czech Republic |
| `ru` | Russia | `cn` | China | `jp` | Japan |
| `br` | Brazil | `in` | India | `mx` | Mexico |

## Тестирование

### Быстрый тест

```bash
poetry run python scripts/test_mediastack_integration.py
```

Выполняет базовые проверки:
- Health check
- Получение категорий, языков и стран
- Получение источников
- Получение новостей
- Поиск новостей
- Тестирование исторических новостей

### Что тестирует скрипт

Скрипт выполняет различные тесты с эндпоинтами MediaStack. Все эндпоинты доступны на соответствующих планах.

#### ТЕСТ 1: Health Check
- **Эндпоинт**: `/v1/sources` (простой запрос)
- **Доступность**: Все планы
- **Ожидаемый результат**: Должен работать на всех планах
- **Интерпретация**: 
  - ✅ 200 OK - Access Key валидный, подключение работает
  - ❌ 401 Unauthorized - неверный Access Key
  - ❌ 429 Too Many Requests - превышен лимит запросов

#### ТЕСТ 2: Получение источников (`/v1/sources`)
- **Доступность**: Все планы
- **Ожидаемый результат**: Список доступных источников
- **Интерпретация**: 
  - ✅ 200 OK - источники получены
  - ❌ 401 Unauthorized - неверный Access Key
  - ❌ 429 Too Many Requests - превышен лимит запросов

#### ТЕСТ 3: Получение новостей (`/v1/news`)
- **Доступность**: Все планы
- **Ожидаемый результат**: Список новостей
- **Интерпретация**: 
  - ✅ 200 OK - новости получены
  - ❌ 401 Unauthorized - неверный Access Key
  - ❌ 429 Too Many Requests - превышен лимит запросов

#### ТЕСТ 4: Поиск новостей (`/v1/news` с параметром keywords)
- **Доступность**: Все планы
- **Ожидаемый результат**: Результаты поиска
- **Интерпретация**: 
  - ✅ 200 OK - поиск работает
  - ❌ 401 Unauthorized - неверный Access Key
  - ❌ 429 Too Many Requests - превышен лимит запросов

#### ТЕСТ 5: Исторические новости (`/v1/news` с параметром date)
- **Доступность**: Standard+ планы
- **Ожидаемый результат**: 401 ошибка на Free плане - это нормально
- **Интерпретация**: 
  - ✅ 200 OK - план Standard+ работает
  - ❌ 401 Unauthorized - Free план или неверный Access Key
  - ❌ 429 Too Many Requests - превышен лимит запросов

### Интерпретация результатов

#### ✅ Успешное выполнение
```
============================================================
✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!
🎉 MediaStack провайдер работает корректно!
============================================================
```

**Что это означает:**
- Access Key валидный
- Сетевое подключение работает
- Провайдер корректно обрабатывает запросы и ответы
- Все основные функции работают

#### ❌ Ошибки выполнения
```
============================================================
❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!
💡 Проверьте Access Key и подключение к интернету
============================================================
```

**Возможные причины:**
- Неверный Access Key (401 ошибка)
- Превышен лимит запросов (429 ошибка)
- Отсутствует интернет-соединение
- Проблемы с сервером MediaStack

### Детальные логи

Скрипты выводят подробную информацию о каждом запросе:

#### Проверка конфигурации
```
📋 MediaStack настройки: enabled=True, priority=4
🔧 Создаем MediaStack fetcher...
✅ Fetcher создан: mediastack
```

#### Health Check
```
🏥 Проверка health check...
✅ Health check результат: {'status': 'healthy', 'provider': 'mediastack', 'message': 'MediaStack is accessible'}
```

#### Получение данных
```
📰 Получение источников...
✅ Найдено источников: 7500+
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
| 401 | Неверный Access Key | Проверьте ключ в .env |
| 429 | Превышен лимит запросов | Подождите или обновите план |
| 500 | Ошибка сервера | Повторите позже |

### Планы подписки MediaStack

| План | Стоимость | Запросов/месяц | Исторические данные | Задержка |
|------|-----------|----------------|---------------------|----------|
| **Free** | Бесплатно | 1,000 | Нет | 30 минут |
| **Standard** | $9.99/месяц | 10,000 | Да | Реальное время |
| **Professional** | $49.99/месяц | 50,000 | Да | Реальное время |
| **Business** | $199.99/месяц | 250,000 | Да | Реальное время |

## Справочник по параметрам API

### Эндпоинт: Live News (`/v1/news`)

**Описание**: Эндпоинт актуальных новостей предоставляет доступ к последним новостям в реальном времени. Новости обновляются каждые 30 минут на Free плане и в реальном времени на платных планах.

**URL**: `https://api.mediastack.com/v1/news?access_key=YOUR_ACCESS_KEY`

**Доступность**: Все планы

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `access_key` | ✅ | string | Ваш Access Key для доступа к MediaStack API | `your_access_key_here` |
| `keywords` | ❌ | string | Поиск по ключевым словам. Макс. 500 символов | `bitcoin`, `artificial intelligence`, `covid-19` |
| `categories` | ❌ | string | Категории новостей через запятую | `business`, `technology,science`, `sports` |
| `countries` | ❌ | string | Коды стран через запятую | `us`, `us,gb`, `ru,de,fr` |
| `languages` | ❌ | string | Коды языков через запятую | `en`, `en,es`, `ru,de` |
| `sources` | ❌ | string | Включить/исключить источники (префикс "-" для исключения) | `cnn,bbc`, `cnn,-fox`, `-tabloid1,-tabloid2` |
| `date` | ❌ | string | Дата или диапазон дат (YYYY-MM-DD или YYYY-MM-DD,YYYY-MM-DD) | `2024-01-15`, `2024-01-01,2024-01-31` |
| `sort` | ❌ | string | Сортировка результатов | `published_desc`, `published_asc`, `popularity` |
| `limit` | ❌ | int | Количество результатов (макс. 100) | `25`, `50`, `100` |
| `offset` | ❌ | int | Смещение для пагинации | `0`, `25`, `50` |

**Дефолтные значения:**
- `sort`: `"published_desc"`
- `limit`: `25`
- `offset`: `0`

### Эндпоинт: Historical News (`/v1/news` с параметром date)

**Описание**: Доступ к историческим новостям для анализа и исследований. Доступен только на Standard+ планах.

**URL**: `https://api.mediastack.com/v1/news?access_key=YOUR_ACCESS_KEY&date=2024-01-15`

**Доступность**: Standard+ планы

Параметры те же, что и для Live News, но обязательно указание параметра `date`.

### Эндпоинт: Sources (`/v1/sources`)

**Описание**: Получение списка доступных источников новостей с метаданными.

**URL**: `https://api.mediastack.com/v1/sources?access_key=YOUR_ACCESS_KEY`

**Доступность**: Все планы

| Параметр | Обязательный | Тип | Описание | Примеры значений |
|----------|-------------|-----|----------|------------------|
| `access_key` | ✅ | string | Ваш Access Key для доступа к MediaStack API | `your_access_key_here` |
| `search` | ❌ | string | Поиск источников по названию | `cnn`, `bbc`, `reuters` |
| `countries` | ❌ | string | Коды стран через запятую | `us`, `gb,de`, `ru,fr,it` |
| `categories` | ❌ | string | Категории через запятую | `business`, `technology,science` |
| `languages` | ❌ | string | Коды языков через запятую | `en`, `ru,de`, `es,fr,it` |
| `limit` | ❌ | int | Количество результатов (макс. 100) | `25`, `50`, `100` |
| `offset` | ❌ | int | Смещение для пагинации | `0`, `25`, `50` |

**Дефолтные значения:**
- `limit`: `25`
- `offset`: `0`

### Расширенный поиск

MediaStack поддерживает расширенный поиск с использованием специального синтаксиса для параметра `keywords`.

#### Операторы поиска

| Операция | Синтаксис | Пример | Описание |
|----------|-----------|--------|----------|
| **Одно ключевое слово** | `keywords=word` | `keywords=bitcoin` | Поиск статей содержащих слово "bitcoin" |
| **Несколько слов (И)** | `keywords=word1 word2` | `keywords=bitcoin crypto` | Статьи содержащие ОБА слова |
| **Точная фраза** | `keywords="exact phrase"` | `keywords="artificial intelligence"` | Поиск точной фразы |
| **ИЛИ** | `keywords=word1 OR word2` | `keywords=bitcoin OR ethereum` | Любое из слов должно присутствовать |
| **НЕ** | `keywords=word1 NOT word2` | `keywords=crypto NOT scam` | Исключить статьи со словом "scam" |
| **Группировка** | `keywords=(word1 OR word2) AND word3` | `keywords=(bitcoin OR ethereum) AND price` | Сложные логические выражения |

#### Примеры запросов

```bash
# Простой поиск
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&keywords=technology

# Точная фраза
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&keywords="machine learning"

# Логические операторы
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&keywords=bitcoin AND (price OR value)

# Исключение слов
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&keywords=Apple NOT iPhone

# Комбинированный поиск с фильтрами
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&keywords=AI&categories=technology&countries=us&languages=en
```

### Фильтрация источников

MediaStack поддерживает включение и исключение источников с помощью специального синтаксиса:

#### Синтаксис источников

```bash
# Включить только определенные источники
sources=cnn,bbc,reuters

# Исключить определенные источники (префикс "-")
sources=-tabloid1,-tabloid2

# Смешанный режим: включить одни, исключить другие
sources=cnn,bbc,-fox,-breitbart
```

#### Примеры фильтрации

```bash
# Только авторитетные источники
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&sources=cnn,bbc,reuters,ap

# Исключить таблоиды
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&sources=-dailymail,-thesun,-nypost

# Технологические источники
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&sources=techcrunch,wired,arstechnica&categories=technology
```

### Работа с датами

MediaStack поддерживает различные форматы дат:

#### Форматы дат

```bash
# Конкретная дата
date=2024-01-15

# Диапазон дат
date=2024-01-01,2024-01-31

# Только год и месяц (весь месяц)
date=2024-01

# Только год (весь год)
date=2024
```

#### Примеры с датами

```bash
# Новости за конкретный день
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&date=2024-01-15

# Новости за январь 2024
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&date=2024-01-01,2024-01-31

# Исторические новости о биткоине
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&keywords=bitcoin&date=2023-01-01,2023-12-31
```

### Поддерживаемые категории (7 категорий)

MediaStack поддерживает следующие категории:

- `business` - Бизнес и финансы
- `entertainment` - Развлечения
- `general` - Общие новости
- `health` - Здоровье и медицина
- `science` - Наука
- `sports` - Спорт
- `technology` - Технологии

### Тарифные планы и ограничения

#### Планы подписки

| План | Стоимость | Запросов/месяц | Исторические данные | Задержка | Особенности |
|------|-----------|----------------|---------------------|----------|-------------|
| **Free** | Бесплатно | 1,000 | Нет | 30 минут | Базовые функции |
| **Standard** | $9.99/месяц | 10,000 | Да | Реальное время | + Исторические данные |
| **Professional** | $49.99/месяц | 50,000 | Да | Реальное время | + Приоритетная поддержка |
| **Business** | $199.99/месяц | 250,000 | Да | Реальное время | + Выделенная поддержка |

#### Доступность функций по планам

| Функция | Free | Standard | Professional | Business |
|---------|------|----------|--------------|----------|
| **Live News API** | ✅ | ✅ | ✅ | ✅ |
| **Historical News API** | ❌ | ✅ | ✅ | ✅ |
| **Sources API** | ✅ | ✅ | ✅ | ✅ |
| **Реальное время** | ❌ | ✅ | ✅ | ✅ |
| **Расширенный поиск** | ✅ | ✅ | ✅ | ✅ |
| **Фильтрация источников** | ✅ | ✅ | ✅ | ✅ |
| **Приоритетная поддержка** | ❌ | ❌ | ✅ | ✅ |
| **Выделенная поддержка** | ❌ | ❌ | ❌ | ✅ |

#### Ограничения бесплатного плана

- **1,000 запросов в месяц** (~33 в день)
- **Задержка 30 минут** для новостей
- **Нет доступа к историческим данным**
- **Базовая поддержка**

#### Лимиты запросов

- **Rate Limit**: 1000 запросов в час для всех планов
- **Timeout**: 10 секунд на запрос
- **Максимальный размер ответа**: 10MB
- **Максимальная длина поискового запроса**: 500 символов

#### Статус коды ошибок

| Код | Описание | Причина | Решение |
|-----|----------|---------|---------|
| 200 | Успех | Запрос выполнен | - |
| 400 | Неверный запрос | Неправильные параметры | Проверьте параметры запроса |
| 401 | Неавторизован | Неверный Access Key | Проверьте ключ в .env |
| 403 | Запрещено | Функция недоступна на плане | Обновите план подписки |
| 429 | Превышен лимит | Слишком много запросов | Подождите или обновите план |
| 500 | Ошибка сервера | Внутренняя ошибка API | Повторите запрос позже |

#### Форматы данных

**Дата и время:**
- Формат: ISO 8601 (`YYYY-MM-DDTHH:MM:SS.000000Z`)
- Часовой пояс: UTC
- Примеры: `2024-01-15T10:30:00.000000Z`, `2024-01-15`

**Поля ответа статей:**
- `author` - автор статьи
- `title` - заголовок статьи
- `description` - описание статьи
- `url` - ссылка на оригинальную статью
- `source` - источник статьи
- `image` - ссылка на изображение
- `category` - категория статьи
- `language` - язык статьи
- `country` - страна источника
- `published_at` - дата и время публикации

**Поля ответа источников:**
- `name` - название источника
- `url` - официальный сайт источника
- `category` - категория источника
- `language` - язык источника
- `country` - страна источника

## Ограничения

### Бесплатный план

- 1,000 запросов в месяц
- Задержка 30 минут для новостей
- Нет доступа к историческим данным
- Ограничение по rate limit

### Технические ограничения

- Максимум 100 статей за запрос
- Некоторые источники могут быть недоступны
- Задержки в обновлении новостей на Free плане
- Ограничения по геолокации

## Обработка ошибок

Провайдер обрабатывает следующие типы ошибок:

1. **MediaStackAPIException** - Ошибки API
2. **RequestException** - Сетевые ошибки
3. **ValueError** - Ошибки валидации
4. **KeyError** - Ошибки структуры данных

Все ошибки логируются и возвращаются в стандартном формате.

## Примеры использования

### Получение новостей по рубрикам

```python
from src.services.news.fetcher_fabric import create_news_fetcher_from_config

# Создание fetcher'а
fetcher = create_news_fetcher_from_config("mediastack")

# Получение новостей
news = fetcher.fetch_news(["технологии", "спорт"])
print(f"Найдено {len(news)} новостей")
```

### Поиск новостей

```python
# Поиск по ключевым словам
search_results = fetcher.search_news(
    query="искусственный интеллект",
    language="en",
    limit=20
)

# Поиск с фильтрацией
filtered_results = fetcher.search_news(
    query="bitcoin",
    category="business",
    countries="us,gb",
    sources="cnn,bbc,-fox"
)
```

### Получение исторических новостей

```python
# Исторические новости (только Standard+ планы)
historical_news = fetcher.fetch_historical_news(
    date="2024-01-15",
    keywords="technology",
    limit=50
)

# Диапазон дат
range_news = fetcher.fetch_historical_news(
    date="2024-01-01,2024-01-31",
    categories="business,technology"
)
```

### Получение источников

```python
# Получение всех источников
sources = fetcher.get_sources()
print(f"Доступно {len(sources['data'])} источников")

# Фильтрация по категории и стране
tech_sources = fetcher.get_sources(
    category="technology", 
    countries="us",
    search="tech"
)
```

### Через Pipeline

```python
from src.services.news.pipeline import create_news_pipeline_orchestrator

# Создание pipeline с MediaStack
pipeline = create_news_pipeline_orchestrator(provider='mediastack')

# Запуск pipeline
result = pipeline.run_pipeline(
    query='bitcoin',
    categories=['business'],
    limit=10,
    language='en'
)
```

### Прямое использование Fetcher

```python
from src.services.news.fetchers.mediastack_com import MediaStackFetcher
from src.config import MediaStackSettings

# Создание настроек
settings = MediaStackSettings(
    access_key="your_access_key",
    enabled=True,
    priority=4
)

# Создание fetcher
fetcher = MediaStackFetcher(settings)

# Получение новостей
news = fetcher.fetch_news(
    query='technology',
    category='science',
    language='en',
    limit=20
)
```

## Стандартизация данных

Провайдер автоматически стандартизирует данные MediaStack под общий формат:

### Структура ответа MediaStack

#### Поля ответа для всех эндпоинтов

| Поле | Описание | Доступность |
|------|----------|-------------|
| `pagination` | Информация о пагинации | Все планы |
| `data` | Массив статей или источников | Все планы |

#### Поля статьи

| Поле | Описание | Доступность |
|------|----------|-------------|
| `author` | Автор статьи | Все планы |
| `title` | Заголовок статьи | Все планы |
| `description` | Описание статьи | Все планы |
| `url` | URL статьи | Все планы |
| `source` | Источник статьи | Все планы |
| `image` | URL изображения | Все планы |
| `category` | Категория статьи | Все планы |
| `language` | Язык статьи | Все планы |
| `country` | Страна источника | Все планы |
| `published_at` | Дата публикации | Все планы |

#### Пример структуры статьи

```json
{
    "pagination": {
        "limit": 25,
        "offset": 0,
        "count": 25,
        "total": 1000
    },
    "data": [
        {
            "author": "John Doe",
            "title": "Заголовок новостной статьи",
            "description": "Описание статьи...",
            "url": "https://example.com/article",
            "source": "Example News",
            "image": "https://example.com/image.jpg",
            "category": "technology",
            "language": "en",
            "country": "us",
            "published_at": "2024-01-15T10:30:00.000000Z"
        }
    ]
}
```

### Структура источника

```python
{
    "name": "Название источника",
    "url": "https://source.com",
    "category": "technology",
    "language": "en",
    "country": "us"
}
```

## Пагинация

MediaStack использует offset-based пагинацию для разбивки больших наборов результатов.

### Как работает пагинация

```bash
# Первая страница (по умолчанию)
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&limit=25&offset=0

# Вторая страница
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&limit=25&offset=25

# Третья страница
https://api.mediastack.com/v1/news?access_key=YOUR_KEY&limit=25&offset=50
```

### Пример работы с пагинацией в Python

```python
from src.services.news.fetchers.mediastack_com import MediaStackFetcher

fetcher = MediaStackFetcher(settings)
all_articles = []
offset = 0
limit = 25

while True:
    response = fetcher.fetch_news(
        query="bitcoin",
        limit=limit,
        offset=offset
    )
    
    if not response.get("data"):
        break
    
    all_articles.extend(response["data"])
    
    # Проверяем, есть ли еще данные
    pagination = response.get("pagination", {})
    if len(response["data"]) < limit:
        break
    
    offset += limit

print(f"Собрано {len(all_articles)} статей")
```

## Отладка

### Включение подробного логирования

```python
import logging
logging.getLogger("mediastack").setLevel(logging.DEBUG)
```

### Проверка конфигурации

```python
from src.config import get_news_providers_settings

settings = get_news_providers_settings()
print(settings.providers["mediastack"])
```

### Тестирование подключения

```python
fetcher = create_news_fetcher_from_config("mediastack")
health = fetcher.check_health()
print(f"Статус: {health['status']}")
```

## Полезные ссылки

### Официальные ресурсы
- [Официальная документация MediaStack](https://mediastack.com/documentation)
- [Регистрация и получение Access Key](https://mediastack.com/signup)
- [Тарифные планы и цены](https://mediastack.com/pricing)
- [Поддержка и контакты](https://mediastack.com/support)

### Справочники
- [Коды стран](https://mediastack.com/documentation#countries)
- [Коды языков](https://mediastack.com/documentation#languages)
- [Категории новостей](https://mediastack.com/documentation#categories)
- [Источники новостей](https://mediastack.com/documentation#sources)

## Сравнение с другими провайдерами

| Критерий | MediaStack | NewsData.io | NewsAPI.org | TheNewsAPI |
|----------|------------|-------------|-------------|------------|
| **Бесплатные запросы** | 1,000/месяц | 200/день | 1,000/месяц | 50/месяц |
| **Стоимость платного плана** | $9.99-199.99/месяц | $199.99-1299.99/месяц | $449/месяц | $9.99-199/месяц |
| **Количество источников** | 7,500+ | 84,770+ | 80,000+ | 50,000+ |
| **Поддерживаемые языки** | 13 | 89 | 14 | 50+ |
| **Поддерживаемые страны** | 50+ | 206 | 54 | 150+ |
| **Исторические данные** | Да (Standard+) | Да (Basic+) | Нет | Да (Standard+) |
| **Задержка данных** | 30 мин (Free), реальное время (Standard+) | Реальное время | Реальное время | Реальное время |
| **Расширенный поиск** | Да (AND/OR/NOT) | Да (AND/OR/NOT) | Да | Да |
| **Фильтрация источников** | Да (include/exclude) | Да | Да | Да |
| **Приоритет в проекте** | Низкий | Средний | Низкий | Высокий |

## Устранение неполадок

### Ошибка аутентификации

```
Error: 401 Unauthorized
```

**Решение**: Проверьте правильность Access Key в `.env` файле.

### Превышение лимитов

```
Error: 429 Too Many Requests
```

**Решение**: Дождитесь сброса лимитов или обновите план.

### Ошибка доступа к историческим данным

```
Error: 401 Unauthorized (Historical News)
```

**Решение**: Исторические данные доступны только на Standard+ планах.

### Пустые результаты

```
Warning: No articles found
```

**Возможные причины**:
- Слишком специфический запрос
- Неподдерживаемый язык/страна
- Отсутствие новостей по теме
- Неправильные параметры фильтрации

### Ошибки сети

```
Error: Connection timeout
```

**Решение**: Проверьте интернет соединение и статус API.

### Устранение неполадок

#### Проблема: "MEDIASTACK_API_KEY not found"
1. Проверьте наличие файла `.env` в корне проекта
2. Убедитесь, что Access Key указан правильно
3. Перезапустите скрипт

#### Проблема: Все запросы возвращают 401
- Проверьте правильность Access Key
- Убедитесь, что ключ активен на MediaStack
- Проверьте, что ключ не истек

#### Проблема: Ошибка 401 для исторических данных
- Исторические данные доступны только на Standard+ планах
- Обновите план подписки или используйте только Live News

#### Проблема: Ошибка 429 (Too Many Requests)
- Превышен лимит запросов (1,000/месяц на Free плане)
- Подождите до следующего месяца или обновите план
- Проверьте количество оставшихся запросов в личном кабинете

#### Проблема: Timeout ошибки
- Проверьте интернет-соединение
- Убедитесь, что нет блокировки файрвола
- Попробуйте позже (возможны проблемы с сервером)

#### Проблема: Пустые результаты поиска
- Попробуйте более общие ключевые слова
- Проверьте правильность параметров фильтрации
- Убедитесь, что новости по теме существуют
- Проверьте правильность синтаксиса источников

#### Проблема: Ошибки парсинга дат
- Убедитесь, что даты в формате YYYY-MM-DD
- Для диапазонов используйте формат YYYY-MM-DD,YYYY-MM-DD
- Проверьте, что даты не в будущем

#### Проблема: Неправильная фильтрация источников
- Используйте правильный синтаксис: `cnn,bbc` для включения
- Используйте префикс `-` для исключения: `-tabloid1,-tabloid2`
- Проверьте правильность названий источников 