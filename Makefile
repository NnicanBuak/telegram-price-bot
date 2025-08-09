# Makefile для Telegram Price Bot с Poetry

.PHONY: help install install-dev test test-unit test-integration test-coverage lint format clean run setup check-env db-init

# Переменные
PYTHON := python3
POETRY := poetry
PYTEST := $(POETRY) run pytest
BLACK := $(POETRY) run black
ISORT := $(POETRY) run isort
FLAKE8 := $(POETRY) run flake8
MYPY := $(POETRY) run mypy

# Цвета для вывода
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

# Помощь (по умолчанию)
help:
	@echo "$(GREEN)Telegram Price Bot - Команды Make$(NC)"
	@echo ""
	@echo "$(YELLOW)Установка:$(NC)"
	@echo "  make install        - Установить зависимости через Poetry"
	@echo "  make install-dev    - Установить зависимости для разработки"
	@echo "  make setup          - Полная настройка проекта"
	@echo "  make update         - Обновить зависимости"
	@echo ""
	@echo "$(YELLOW)Тестирование:$(NC)"
	@echo "  make test           - Запустить все тесты"
	@echo "  make test-unit      - Запустить unit-тесты"
	@echo "  make test-integration - Запустить интеграционные тесты"
	@echo "  make test-coverage  - Запустить тесты с отчетом покрытия"
	@echo "  make test-watch     - Запустить тесты в режиме наблюдения"
	@echo ""
	@echo "$(YELLOW)Качество кода:$(NC)"
	@echo "  make lint           - Проверить код линтерами"
	@echo "  make format         - Отформатировать код"
	@echo "  make check          - Полная проверка кода"
	@echo "  make type-check     - Проверка типов"
	@echo ""
	@echo "$(YELLOW)База данных:$(NC)"
	@echo "  make db-init        - Инициализировать базу данных"
	@echo "  make db-reset       - Сбросить базу данных"
	@echo "  make db-migrate     - Создать миграции"
	@echo ""
	@echo "$(YELLOW)Запуск:$(NC)"
	@echo "  make run            - Запустить бота"
	@echo "  make run-dev        - Запустить в режиме разработки"
	@echo ""
	@echo "$(YELLOW)Утилиты:$(NC)"
	@echo "  make clean          - Очистить временные файлы"
	@echo "  make check-env      - Проверить переменные окружения"
	@echo "  make shell          - Запустить Poetry shell"

# Проверка установки Poetry
check-poetry:
	@which poetry > /dev/null || (echo "$(RED)Poetry не установлен. Установите: curl -sSL https://install.python-poetry.org | python3 -$(NC)" && exit 1)

# Установка зависимостей
install: check-poetry
	@echo "$(GREEN)Установка зависимостей через Poetry...$(NC)"
	$(POETRY) install --no-dev
	@echo "$(GREEN)✓ Зависимости установлены$(NC)"

install-dev: check-poetry
	@echo "$(GREEN)Установка зависимостей для разработки...$(NC)"
	$(POETRY) install
	@echo "$(GREEN)✓ Зависимости для разработки установлены$(NC)"

# Обновление зависимостей
update: check-poetry
	@echo "$(GREEN)Обновление зависимостей...$(NC)"
	$(POETRY) update
	@echo "$(GREEN)✓ Зависимости обновлены$(NC)"

# Полная настройка проекта
setup: install-dev check-env
	@echo "$(GREEN)Настройка pre-commit хуков...$(NC)"
	$(POETRY) run pre-commit install
	@echo "$(GREEN)✓ Проект настроен$(NC)"

# Проверка переменных окружения
check-env:
	@echo "$(GREEN)Проверка конфигурации...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Создание .env файла из примера...$(NC)"; \
		cp .env.example .env; \
		echo "$(RED)⚠ Заполните .env файл вашими данными!$(NC)"; \
		exit 1; \
	fi
	@$(POETRY) run python -c "from src.core.config import Config; c = Config(); print('✓ Конфигурация корректна')"

# Тестирование
test:
	@echo "$(GREEN)Запуск всех тестов...$(NC)"
	$(PYTEST) tests/ -v

test-unit:
	@echo "$(GREEN)Запуск unit-тестов...$(NC)"
	$(PYTEST) tests/unit/ -v

test-integration:
	@echo "$(GREEN)Запуск интеграционных тестов...$(NC)"
	$(PYTEST) tests/integration/ -v

test-coverage:
	@echo "$(GREEN)Запуск тестов с покрытием...$(NC)"
	$(PYTEST) tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Отчет о покрытии: htmlcov/index.html$(NC)"

test-watch:
	@echo "$(GREEN)Запуск тестов в режиме наблюдения...$(NC)"
	$(POETRY) run ptw tests/ -- -v

test-specific:
	@echo "$(GREEN)Запуск специфичного теста...$(NC)"
	$(PYTEST) tests/ -v -k "$(TEST)"

# Качество кода
lint:
	@echo "$(GREEN)Проверка кода линтерами...$(NC)"
	@echo "Проверка flake8..."
	$(FLAKE8) src tests --max-line-length=88 --extend-ignore=E203,W503
	@echo "$(GREEN)✓ Проверка завершена$(NC)"

format:
	@echo "$(GREEN)Форматирование кода...$(NC)"
	$(BLACK) src tests
	$(ISORT) src tests
	@echo "$(GREEN)✓ Код отформатирован$(NC)"

type-check:
	@echo "$(GREEN)Проверка типов...$(NC)"
	$(MYPY) src --ignore-missing-imports
	@echo "$(GREEN)✓ Проверка типов завершена$(NC)"

check: format lint type-check test
	@echo "$(GREEN)✓ Все проверки пройдены$(NC)"

# База данных
db-init:
	@echo "$(GREEN)Инициализация базы данных...$(NC)"
	$(POETRY) run python -c "import asyncio; from src.core.config import Config; from src.database.session import Database; \
		async def init(): \
			config = Config(); \
			db = Database(config.database.url); \
			await db.init_db(); \
			print('✓ База данных инициализирована'); \
		asyncio.run(init())"

db-reset:
	@echo "$(YELLOW)Сброс базы данных...$(NC)"
	rm -f bot_database.db
	$(MAKE) db-init

db-migrate:
	@echo "$(GREEN)Создание миграций...$(NC)"
	$(POETRY) run python scripts/migrate.py

# Запуск
run:
	@echo "$(GREEN)Запуск бота...$(NC)"
	$(POETRY) run python src/main.py

run-dev:
	@echo "$(GREEN)Запуск в режиме разработки...$(NC)"
	$(POETRY) run watchdog -p "src/*.py" -R -- python src/main.py

# Poetry shell
shell:
	@echo "$(GREEN)Запуск Poetry shell...$(NC)"
	$(POETRY) shell

# Очистка
clean:
	@echo "$(GREEN)Очистка временных файлов...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info/
	@echo "$(GREEN)✓ Очистка завершена$(NC)"

# Docker команды
docker-build:
	@echo "$(GREEN)Сборка Docker образа...$(NC)"
	docker build -t telegram-price-bot .

docker-run:
	@echo "$(GREEN)Запуск в Docker...$(NC)"
	docker run --env-file .env telegram-price-bot

# Poetry команды
poetry-lock:
	@echo "$(GREEN)Обновление poetry.lock...$(NC)"
	$(POETRY) lock

poetry-export:
	@echo "$(GREEN)Экспорт зависимостей...$(NC)"
	$(POETRY) export -f requirements.txt --output requirements.txt
	$(POETRY) export -f requirements.txt --dev --output requirements-dev.txt

# Проверка безопасности
security:
	@echo "$(GREEN)Проверка безопасности зависимостей...$(NC)"
	$(POETRY) run safety check
	$(POETRY) run bandit -r src/
	@echo "$(GREEN)✓ Проверка безопасности завершена$(NC)"

# Бэкап
backup:
	@echo "$(GREEN)Создание резервной копии...$(NC)"
	mkdir -p backups
	cp bot_database.db backups/bot_database_$(shell date +%Y%m%d_%H%M%S).db 2>/dev/null || true
	tar -czf backups/backup_$(shell date +%Y%m%d_%H%M%S).tar.gz \
		--exclude=.git --exclude=__pycache__ --exclude=.pytest_cache \
		--exclude=htmlcov --exclude=.venv --exclude=dist --exclude=build \
		.
	@echo "$(GREEN)✓ Резервная копия создана в backups/$(NC)"

# Статистика кода
stats:
	@echo "$(GREEN)Статистика проекта:$(NC)"
	@echo "Строк кода Python:"
	@find src -name "*.py" | xargs wc -l | tail -1
	@echo ""
	@echo "Количество тестов:"
	@$(PYTEST) --collect-only -q 2>/dev/null | tail -1 || echo "Нет тестов"
	@echo ""
	@echo "Файлы проекта:"
	@find src -name "*.py" | wc -l

# Документация
docs:
	@echo "$(GREEN)Генерация документации...$(NC)"
	$(POETRY) run sphinx-build -b html docs docs/_build/html
	@echo "$(GREEN)✓ Документация: docs/_build/html/index.html$(NC)"

# Установка хуков git
install-hooks:
	@echo "$(GREEN)Установка Git хуков...$(NC)"
	$(POETRY) run pre-commit install
	$(POETRY) run pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Git хуки установлены$(NC)"

# Проверка готовности к релизу
release-check:
	@echo "$(GREEN)Проверка готовности к релизу...$(NC)"
	$(MAKE) check
	$(MAKE) security
	@echo "$(GREEN)✓ Готово к релизу$(NC)"

.DEFAULT_GOAL := help