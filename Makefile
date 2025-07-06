# /Makefile

.PHONY: help install run test lint format docker-build docker-run clean

help: ## Показать справку по командам
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	poetry install

run: ## Запустить приложение
	poetry run python src/run.py

test: ## Запустить тесты
	poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

lint: ## Проверить код линтерами
	poetry run ruff check src/ tests/
	poetry run mypy src/
	poetry run flake8 src/ tests/

format: ## Форматировать код
	poetry run ruff format src/ tests/
	poetry run black src/ tests/

docker-build: ## Собрать Docker образ
	docker build -t coffee-grinder:latest .

docker-run: ## Запустить Docker контейнер
	docker run --rm -it --env-file .env coffee-grinder:latest

pre-commit-install: ## Установить pre-commit хуки
	poetry run pre-commit install

pre-commit-run: ## Запустить pre-commit для всех файлов
	poetry run pre-commit run --all-files

clean: ## Очистить временные файлы
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

update-deps: ## Обновить зависимости
	poetry update

lock: ## Обновить poetry.lock
	poetry lock --no-update 