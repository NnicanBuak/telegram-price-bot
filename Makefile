# Makefile для Telegram Price Bot

.PHONY: help install install-dev test test-unit test-integration test-coverage lint format clean run setup check-env db-init

# Переменные
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
ISORT := $(PYTHON) -m isort
FLAKE8 := $(PYTHON) -m flake8
MYPY := $(PYTHON) -m mypy

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
	@echo "  make install        - Установить основные зависимости"
	@echo "  make install-dev    - Установить зависимости для разработки"
	@echo "  make setup          - Полная настройка проекта"
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
	@echo ""
	@echo "$(YELLOW)База данных:$(NC)"
	@echo "  make db-init        - Инициализировать базу данных"
	@echo "  make db-migrate     - Создать миграции"
	@echo "  make db-upgrade     - Применить миграции"
	@echo ""
	@echo "$(YELLOW)Запуск:$(NC)"
	@echo "  make run            - Запустить бота"
	@echo "  make run-dev        - Запустить в режиме разработки"
	@echo "  make run-test       - Запустить тестовый прогон"
	@echo ""
	@echo "$(YELLOW)Утилиты:$(NC)"
	@echo "  make clean          - Очистить временные файлы"
	@echo "  make check-env      - Проверить переменные окружения"
	@echo "  make docs           - Сгенерировать документацию"

# Установка зависимостей
install:
	@echo "$(GREEN)Установка основных зависимостей...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Зависимости установлены$(NC)"

install-dev:
	@echo "$(GREEN)Установка зависимостей для разработки...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✓ Зависимости для разработки установлены$(NC)"

# Полная настройка проекта
setup: install-dev check-env db-init
	@echo "$(GREEN)Настройка pre-commit хуков...$(NC)"
	pre-commit install
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
	@$(PYTHON) -c "from config import Config; c = Config(); print('✓ Конфигурация корректна')"

# Тестирование
test:
	@echo "$(GREEN)Запуск всех тестов...$(NC)"
	$(PYTEST) tests/ -v

test-unit:
	@echo "$(GREEN)Запуск unit-тестов...$(NC)"
	$(PYTEST) tests/ -v -m unit

test-integration:
	@echo "$(GREEN)Запуск интеграционных тестов...$(NC)"
	$(PYTEST) tests/ -v -m integration

test-coverage:
	@echo "$(GREEN)Запуск тестов с покрытием...$(NC)"
	$(PYTEST) tests/ --cov=. --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Отчет о покрытии: htmlcov/index.html$(NC)"

test-watch:
	@echo "$(GREEN)Запуск тестов в режиме наблюдения...$(NC)"
	$(PYTHON) -m pytest_watch tests/ -v

test-specific:
	@echo "$(GREEN)Запуск специфичного теста...$(NC)"
	$(PYTEST) tests/test_bot.py::$(TEST) -v -s

# Качество кода
lint:
	@echo "$(GREEN)Проверка кода линтерами...$(NC)"
	@echo "Проверка flake8..."
	$(FLAKE8) . --count --select=E9,F63,F7,F82 --show-source --statistics
	$(FLAKE8) . --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics
	@echo "Проверка типов mypy..."
	$(MYPY) bot.py database.py config.py menu_system.py --ignore-missing-imports
	@echo "$(GREEN)✓ Проверка завершена$(NC)"

format:
	@echo "$(GREEN)Форматирование кода...$(NC)"
	$(BLACK) .
	$(ISORT) .
	@echo "$(GREEN)✓ Код отформатирован$(NC)"

check: lint test
	@echo "$(GREEN)✓ Все проверки пройдены$(NC)"

# База данных
db-init:
	@echo "$(GREEN)Инициализация базы данных...$(NC)"
	$(PYTHON) -c "import asyncio; from database import Database; from config import Config; \
		async def init(): \
			db = Database(Config().database_url); \
			await db.init_db(); \
			print('✓ База данных инициализирована'); \
		asyncio.run(init())"

db-reset:
	@echo "$(YELLOW)Сброс базы данных...$(NC)"
	rm -f bot_database.db
	make db-init

# Запуск
run:
	@echo "$(GREEN)Запуск бота...$(NC)"
	$(PYTHON) bot.py

run-dev:
	@echo "$(GREEN)Запуск в режиме разработки с автоперезагрузкой...$(NC)"
	watchmedo auto-restart -d . -p "*.py" -R -- $(PYTHON) bot.py

run-test:
	@echo "$(GREEN)Запуск тестового прогона...$(NC)"
	$(PYTHON) test_bot.py

# Документация
docs:
	@echo "$(GREEN)Генерация документации...$(NC)"
	cd docs && $(PYTHON) -m sphinx . _build/html
	@echo "$(GREEN)✓ Документация: docs/_build/html/index.html$(NC)"

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
	@echo "$(GREEN)✓ Очистка завершена$(NC)"

# Docker команды (если понадобится в будущем)
docker-build:
	@echo "$(GREEN)Сборка Docker образа...$(NC)"
	docker build -t telegram-price-bot .

docker-run:
	@echo "$(GREEN)Запуск в Docker...$(NC)"
	docker run --env-file .env telegram-price-bot

# Деплой
deploy-check:
	@echo "$(GREEN)Проверка готовности к деплою...$(NC)"
	make check
	@echo "$(GREEN)✓ Готово к деплою$(NC)"

# Бэкап
backup:
	@echo "$(GREEN)Создание резервной копии...$(NC)"
	mkdir -p backups
	cp bot_database.db backups/bot_database_$(shell date +%Y%m%d_%H%M%S).db 2>/dev/null || true
	tar -czf backups/backup_$(shell date +%Y%m%d_%H%M%S).tar.gz \
		--exclude=venv --exclude=__pycache__ --exclude=.git \
		--exclude=htmlcov --exclude=.pytest_cache \
		.
	@echo "$(GREEN)✓ Резервная копия создана в backups/$(NC)"

# Статистика кода
stats:
	@echo "$(GREEN)Статистика проекта:$(NC)"
	@echo "Строк кода Python:"
	@find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" | xargs wc -l | tail -1
	@echo ""
	@echo "Количество тестов:"
	@$(PYTEST) --collect-only -q 2>/dev/null | tail -1
	@echo ""
	@echo "Файлы проекта:"
	@find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" | wc -l

# Установка хуков git
install-hooks:
	@echo "$(GREEN)Установка Git хуков...$(NC)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Git хуки установлены$(NC)"

# Проверка безопасности
security:
	@echo "$(GREEN)Проверка безопасности зависимостей...$(NC)"
	$(PIP) install safety
	safety check
	@echo "$(GREEN)✓ Проверка безопасности завершена$(NC)"

.DEFAULT_GOAL := help