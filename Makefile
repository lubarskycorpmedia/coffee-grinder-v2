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

# Docker команды
docker-up: ## Запустить все контейнеры
	docker-compose up -d

docker-down: ## Остановить все контейнеры
	docker-compose down

docker-restart: ## Перезапустить все контейнеры
	docker-compose restart

docker-restart-frontend: ## Перезапустить только frontend
	docker-compose restart news-frontend

docker-restart-backend: ## Перезапустить только backend
	docker-compose restart news-backend

docker-rebuild: ## Пересобрать и запустить контейнеры
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

docker-rebuild-frontend: ## Пересобрать только frontend
	docker-compose down news-frontend
	docker-compose build --no-cache news-frontend
	docker-compose up -d news-frontend

docker-rebuild-backend: ## Пересобрать только backend
	docker-compose down news-backend
	docker-compose build --no-cache news-backend
	docker-compose up -d news-backend

docker-recreate: ## Пересоздать контейнеры с новой конфигурацией
	docker-compose up -d --force-recreate

docker-recreate-frontend: ## Пересоздать только frontend контейнер
	docker-compose up -d --force-recreate news-frontend

docker-logs: ## Показать логи всех контейнеров
	docker-compose logs -f

docker-logs-frontend: ## Показать логи frontend
	docker-compose logs -f news-frontend

docker-logs-backend: ## Показать логи backend
	docker-compose logs -f news-backend

# Жёсткая очистка Docker
docker-clean: ## Остановить контейнеры и удалить volumes
	docker-compose down -v --remove-orphans

docker-prune: ## Удалить все неиспользуемые Docker объекты
	docker system prune -a --volumes -f

docker-nuke: ## Жёсткая очистка: остановить всё, удалить images, volumes, networks
	docker-compose down -v --remove-orphans
	docker system prune -a --volumes -f
	docker network prune -f
	docker volume prune -f

docker-reset: ## Полный сброс: очистка + пересборка + запуск
	make docker-nuke
	docker-compose build --no-cache
	docker-compose up -d

status: ## Показать статус всех контейнеров
	docker-compose ps
	@echo "=== Nginx статус ==="
	cd /var/www/prod/b2bc && docker compose ps nginx 