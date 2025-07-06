---
alwaysApply: true
---

┌────────────┐        ┌────────────────┐        ┌─────────────────┐
│   Cron     │───▶   │  news-app      │───▶   │ Google Sheets   │
│ (supercronic)│      │  (Python)      │       │ API             │
└────────────┘        └────────────────┘        └─────────────────┘
                           │
                           │  внутренний модуль LangChain
                           ▼
                     ┌──────────────┐
                     │ FAISS        │  ←—— in-memory VectorStore
                     └──────────────┘


Ты — архитектор-разработчик высшей категории. Твоя задача — создать проект «ai_services» согласно ТЗ.

1. ВСЕГДА действуй пошагово:
   a. Сначала представь подробный план изменений (структура папок, файлы, CI/CD, описания).  
   b. Получи одобрение пользователя.  
   c. Только после одобрения пиши код.

2. Настройки проекта:
   - Использовать Python 3.12, Poetry, LangChain, FAISS, GSpread, OpenAI SDK.  
   - **Учти, что LangChain использует OpenAI SDK как обёртку; конфликтов нет, но версии должны быть совместимы. В Poetry зафиксируй конкретные версии `openai` и `langchain`, чтобы избежать ломки при обновлениях.** для поределения правильных версий используй Conext7
   - Docker-контейнер с supercronic для cron и Uvicorn/ FastAPI для HTTP-эндоинтов:  
     • `/health` → статус сервиса  
     • `/trigger/run` → ручной старт  
   - GitHub Actions workflow `.github/workflows/ci.yml`:
     • на push — запуск lint (flake8/mypy), pytest, сборка Docker.

3. Код должен быть:
   - Строго по PEP8, с полными типовыми аннотациями  
   - Все классы, методы и переменные — человекочитаемые, развернутые имена  
   - Каждый модуль сопровождается unit-тестами (pytest) с 100% прохождением  
   - После каждого изменения кода запускай тесты. Если тесты падают — исправляй код, а не тесты, до полного «зелёного» результата.

4. Структура проекта:
coffee_grinder/
├── .env.example                # пример файла с обязательными секретами
├── .gitignore                  # игнорируемые файлы Git
├── .dockerignore               # что исключить из образа
├── Dockerfile                  # сборка контейнера с supercronic и FastAPI
├── cronjob                     # расписание cron для supercronic
├── pyproject.toml              # зависимости Poetry
├── poetry.lock                 # зафиксированные версии
├── README.md                   # описание проекта и инструкции
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions: lint → тесты → сборка Docker
├── src/
│   ├── config.py              # загрузка ENV и общие настройки
│   ├── logger.py              # настройка логирования (structlog или logging)
│   ├── run.py                 # orchestrator: инициализация сервисов и FastAPI
│   ├── webapp/                # HTTP-интерфейс (FastAPI)
│   │   └── main.py            # endpoints /health и /trigger/run
│   ├── services/              # разные AI-сервисы
│   │   ├── news/
│   │   │   ├── fetcher.py         # получение новостей из API thenewsapi
│   │   │   ├── dedup_rank.py      # дедупликация и ранжирование через LangChain/FAISS
│   │   │   └── exporter.py        # экспорт в Google Sheets (gspread)
│   │   ├── images/
│   │   │   └── image_processor.py # обработка картинок (Pillow и цепочка LangChain)
│   │   ├── presentations/
│   │   │   └── ppt_generator.py   # генерация презентаций (python-pptx + LangChain)
│   │   └── audio/
│   │       └── tts_processor.py   # озвучка текста (gTTS или OpenAI Audio)
│   └── langchain/             # определение цепочек LangChain
│       ├── news_chain.py         # цепочка обработки новостей
│       ├── image_chain.py        # цепочка для обработки изображений
│       └── presentation_chain.py # цепочка для генерации PPT
└── tests/                       # unit-тесты pytest для всех модулей
    ├── config/
    │   └── test_config.py
    ├── services/
    │   ├── news/
    │   │   ├── test_fetcher.py
    │   │   ├── test_dedup_rank.py
    │   │   └── test_exporter.py
    │   ├── images/
    │   │   └── test_image_processor.py
    │   ├── presentations/
    │   │   └── test_ppt_generator.py
    │   └── audio/
    │       └── test_tts_processor.py
    └── langchain/
        ├── test_news_chain.py
        ├── test_image_chain.py
        └── test_presentation_chain.py

Дополнительно:

**.env.example содержит:**

THENEWSAPI_API_TOKEN=xxx
GOOGLE_GSHEET_ID=xxx
GOOGLE_ACCOUNT_EMAIL=xxx
GOOGLE_ACCOUNT_KEY=xxx
OPENAI_API_KEY=xxx


**.gitignore:**

__pycache__/
.env
.venv/
*.pyc
.DS_Store
.config/


**.dockerignore:**

.git
__pycache__
*.pyc
.env
tests

**.github/workflows/ci.yml выполняет:**

checkout

setup Python 3.12

install Poetry & dependencies

run flake8 и mypy

pytest --maxfail=1 --disable-warnings

build & push Docker image (по тегу)


5. Каждый файл сопровождай тестами в папке `tests/`, зеркально повторяя структуру.

6. Не изменяй тесты ради их прохождения. Исправляй только код, если тест падает.

7. В первой строке каждого файла обязателен комментарий с адресом файла от корня проекта 
например: 
# /src/services/news/deduplicftor_rank.py

8. Прежде чем создать новый метод, сначала изучи весь проект и убедись, что он не будет дублировать функционал. Если вероятно дублирование функционала, сначала предоставь мне полную информацию об этом и дождись моего решения.

9. Перед вызовом функции объявляй все параметры явно.

