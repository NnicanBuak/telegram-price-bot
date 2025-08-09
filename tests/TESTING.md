# 🧪 Руководство по тестированию

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [Структура тестов](#структура-тестов)
- [Запуск тестов](#запуск-тестов)
- [Написание тестов](#написание-тестов)
- [Покрытие кода](#покрытие-кода)
- [CI/CD](#cicd)
- [Отладка тестов](#отладка-тестов)

## 🚀 Быстрый старт

### Установка зависимостей для тестирования

```bash
# Установить все зависимости разработки
pip install -r requirements-dev.txt

# Или через make
make install-dev
```

### Запуск всех тестов

```bash
# Простой запуск
pytest

# Через make
make test

# С подробным выводом
pytest -v

# С отчетом о покрытии
make test-coverage
```

## 📁 Структура тестов

```
tests/
├── __init__.py
├── conftest.py           # Общие фикстуры
├── test_bot.py          # Тесты основного функционала бота
├── test_database.py     # Тесты базы данных
├── test_menu_system.py  # Тесты системы меню
├── test_integration.py  # Интеграционные тесты
└── fixtures/            # Тестовые данные
    ├── templates.json
    └── mock_data.py
```

## 🎯 Запуск тестов

### Все тесты

```bash
# Базовый запуск
pytest

# С подробностями
pytest -v

# С выводом print() statements
pytest -s

# Параллельный запуск
pytest -n auto
```

### Конкретные тесты

```bash
# Только unit-тесты
pytest -m unit

# Только интеграционные
pytest -m integration

# Конкретный файл
pytest tests/test_database.py

# Конкретный класс
pytest tests/test_database.py::TestTemplateOperations

# Конкретный тест
pytest tests/test_database.py::TestTemplateOperations::test_create_template

# По паттерну имени
pytest -k "template"
```

### Использование Make

```bash
# Все тесты
make test

# Unit-тесты
make test-unit

# Интеграционные тесты
make test-integration

# С покрытием
make test-coverage

# В режиме наблюдения
make test-watch

# Конкретный тест
make test-specific TEST=TestDatabase::test_create_template
```

## 📊 Покрытие кода

### Генерация отчета

```bash
# Запуск с покрытием
pytest --cov=. --cov-report=term-missing --cov-report=html

# Или через make
make test-coverage
```

### Просмотр отчета

```bash
# В терминале - показывает пропущенные строки
pytest --cov=. --cov-report=term-missing

# HTML отчет - открыть в браузере
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Цели покрытия

- **Минимум**: 70% покрытия
- **Рекомендуется**: 85% покрытия
- **Идеально**: 95%+ покрытия

## ✍️ Написание тестов

### Структура теста

```python
import pytest
from unittest.mock import MagicMock, AsyncMock

class TestFeatureName:
    """Тесты для функциональности X"""
    
    @pytest.fixture
    def setup_data(self):
        """Подготовка данных для тестов"""
        return {"key": "value"}
    
    def test_sync_function(self, setup_data):
        """Тест синхронной функции"""
        result = sync_function(setup_data)
        assert result == expected_value
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Тест асинхронной функции"""
        result = await async_function()
        assert result is not None
```

### Фикстуры

```python
# conftest.py
import pytest
from database import Database

@pytest.fixture
async def test_db():
    """Тестовая база данных"""
    db = Database("sqlite:///:memory:")
    await db.init_db()
    yield db
    # Очистка после теста

@pytest.fixture
def mock_bot():
    """Мок Telegram бота"""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot
```

### Моки и патчи

```python
from unittest.mock import patch, MagicMock

@patch('module.external_api')
def test_with_mock(mock_api):
    """Тест с мокированием внешнего API"""
    mock_api.return_value = {"status": "ok"}
    result = function_using_api()
    assert result["status"] == "ok"
    mock_api.assert_called_once()
```

### Асинхронные тесты

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_operation():
    """Тест асинхронной операции"""
    result = await async_function()
    assert result is not None

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Тест параллельных операций"""
    tasks = [async_function(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 10
```

## 🏷️ Маркеры тестов

### Доступные маркеры

```python
# Пометка unit-теста
@pytest.mark.unit
def test_unit_function():
    pass

# Пометка интеграционного теста
@pytest.mark.integration
async def test_integration():
    pass

# Медленный тест
@pytest.mark.slow
def test_slow_operation():
    pass

# Тест базы данных
@pytest.mark.database
async def test_database_operation():
    pass

# Пропуск теста
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

# Условный пропуск
@pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9+")
def test_modern_feature():
    pass
```

### Запуск по маркерам

```bash
# Только unit-тесты
pytest -m unit

# Все кроме медленных
pytest -m "not slow"

# Unit И database тесты
pytest -m "unit and database"

# Unit ИЛИ integration
pytest -m "unit or integration"
```

## 🔧 Конфигурация

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -ra
    --strict-markers
    --tb=short
    --cov=.
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    database: Database tests
asyncio_mode = auto
```

### .coveragerc

```ini
[run]
source = .
omit = 
    */tests/*
    */venv/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
precision = 2
```

## 🐛 Отладка тестов

### Вывод дополнительной информации

```bash
# Показать print() выводы
pytest -s

# Подробный вывод
pytest -vv

# Показать локальные переменные при ошибке
pytest -l

# Остановиться на первой ошибке
pytest -x

# Запустить отладчик при ошибке
pytest --pdb
```

### Использование отладчика

```python
def test_with_debugger():
    """Тест с точкой останова"""
    import pdb; pdb.set_trace()  # Точка останова
    result = complex_function()
    assert result == expected
```

### Логирование в тестах

```python
import logging

def test_with_logging(caplog):
    """Тест с проверкой логов"""
    with caplog.at_level(logging.INFO):
        function_that_logs()
    
    assert "Expected message" in caplog.text
    assert caplog.records[0].levelname == "INFO"
```

## 🔄 CI/CD

### GitHub Actions

Тесты автоматически запускаются при:
- Push в main или develop ветки
- Создании Pull Request
- По расписанию (ежедневно)

### Локальная проверка перед коммитом

```bash
# Установить pre-commit хуки
pre-commit install

# Запустить проверки вручную
pre-commit run --all-files

# Или через make
make check
```

### Проверка как в CI

```bash
# Запустить все проверки как в CI
make check
make test-coverage
make security
```

## 📈 Метрики качества

### Минимальные требования

- ✅ Все тесты проходят
- ✅ Покрытие кода > 70%
- ✅ Нет критических уязвимостей
- ✅ Код соответствует стилю (black, flake8)
- ✅ Типы проверены (mypy)

### Команды проверки

```bash
# Полная проверка
make check

# Только линтеры
make lint

# Только форматирование
make format

# Проверка безопасности
make security
```

## 🎓 Лучшие практики

### 1. Изолированность тестов

```python
# ✅ Хорошо - тест изолирован
async def test_isolated(test_db):
    await test_db.create_template("Test", "Text")
    templates = await test_db.get_templates()
    assert len(templates) == 1

# ❌ Плохо - зависит от других тестов
async def test_dependent(test_db):
    # Предполагает, что уже есть данные
    templates = await test_db.get_templates()
    assert len(templates) > 0
```

### 2. Понятные имена

```python
# ✅ Хорошо
def test_create_template_with_file_returns_template_with_file_id():
    pass

# ❌ Плохо
def test_1():
    pass
```

### 3. Arrange-Act-Assert

```python
def test_template_creation():
    # Arrange - подготовка
    name = "Test Template"
    text = "Test Text"
    
    # Act - действие
    template = create_template(name, text)
    
    # Assert - проверка
    assert template.name == name
    assert template.text == text
```

### 4. Один тест - одна проверка

```python
# ✅ Хорошо - отдельные тесты
def test_template_has_name():
    template = create_template("Name", "Text")
    assert template.name == "Name"

def test_template_has_text():
    template = create_template("Name", "Text")
    assert template.text == "Text"

# ❌ Плохо - много проверок
def test_template():
    template = create_template("Name", "Text")
    assert template.name == "Name"
    assert template.text == "Text"
    assert template.created_at is not None
    # ... еще 10 проверок
```

## 🆘 Решение проблем

### ImportError при запуске тестов

```bash
# Установить пакет в режиме разработки
pip install -e .

# Или добавить путь
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Async тесты не запускаются

```bash
# Установить pytest-asyncio
pip install pytest-asyncio

# Проверить маркер
@pytest.mark.asyncio  # Должен быть над async тестом
```

### Медленные тесты

```bash
# Найти медленные тесты
pytest --durations=10

# Запустить параллельно
pip install pytest-xdist
pytest -n auto
```

### Случайные падения тестов

```bash
# Запустить с фиксированным seed
pytest --randomly-seed=1234

# Отключить случайный порядок
pytest -p no:randomly
```

## 📚 Дополнительные ресурсы

- [Pytest документация](https://docs.pytest.org/)
- [Pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Python Testing 101](https://realpython.com/python-testing/)

---

💡 **Совет**: Запускайте тесты перед каждым коммитом с помощью `make check`!