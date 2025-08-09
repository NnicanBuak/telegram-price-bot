# 📮 Telegram Price Bot - Бот для рассылки прайс-листов

[![Tests](https://github.com/NnicanBuak/telegram-price-bot/workflows/Tests%20and%20Linting/badge.svg)](https://github.com/NnicanBuak/telegram-price-bot/actions)
[![Coverage](https://codecov.io/gh/NnicanBuak/telegram-price-bot/branch/main/graph/badge.svg)](https://codecov.io/gh/NnicanBuak/telegram-price-bot)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Простой и надежный Telegram бот для рассылки прайс-листов по группам чатов с возможностью сохранения шаблонов сообщений, расширяемой системой меню и полным тестовым покрытием.

## ✨ Возможности

- 📋 **Шаблоны сообщений** - создание и сохранение шаблонов с текстом и файлами
- 👥 **Группы чатов** - объединение чатов в группы для удобной рассылки
- 📎 **Поддержка файлов** - прикрепление документов и изображений к шаблонам
- 📊 **История рассылок** - просмотр статистики отправленных рассылок
- 🔐 **Контроль доступа** - только администраторы могут управлять ботом
- 💾 **Два типа БД** - поддержка SQLite и PostgreSQL
- 🎨 **Расширяемая система меню** - легко добавлять новые функции
- 🧪 **Полное тестирование** - unit и интеграционные тесты
- 🔄 **CI/CD** - автоматическая проверка кода

## 🚀 Быстрый старт

### Использование Makefile (рекомендуется)

```bash
# Клонировать репозиторий
git clone https://github.com/NnicanBuak/telegram-price-bot.git
cd telegram-price-bot

# Полная установка и настройка
make setup

# Или пошагово:
make install       # Установить зависимости
make check-env     # Проверить конфигурацию
make test          # Запустить тесты
make run           # Запустить бота
```

### Вариант 1: Автоматическая установка на Ubuntu

```bash
# Клонировать репозиторий
git clone https://github.com/NnicanBuak/telegram-price-bot.git
cd telegram-price-bot

# Сделать скрипт исполняемым и запустить
chmod +x setup.sh
./setup.sh
```

Скрипт автоматически:
- Установит Python и зависимости
- Предложит установить PostgreSQL
- Создаст виртуальное окружение
- Настроит конфигурацию
- Создаст systemd сервис для автозапуска

### Вариант 2: Ручная установка

#### 1. Подготовка окружения

```bash
# Установка Python (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

#### 2. Создание бота в Telegram

1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Выберите имя и username для бота
4. Сохраните полученный токен

#### 3. Настройка конфигурации

```bash
# Скопировать пример конфигурации
cp .env.example .env

# Отредактировать файл .env
nano .env  # или любой другой редактор
```

Обязательные параметры в `.env`:
```bash
BOT_TOKEN=YOUR_BOT_TOKEN_HERE  # Токен от @BotFather
ADMIN_IDS=123456789             # Ваш Telegram ID (узнать у @userinfobot)
```

#### 4. Запуск бота

```bash
python bot.py
```

## 📖 Использование

### Основные команды

- `/start` - Главное меню бота
- `/help` - Справка по командам
- `/templates` - Управление шаблонами
- `/groups` - Управление группами чатов
- `/mailing` - Создать рассылку
- `/history` - История рассылок
- `/id` - Получить ID текущего чата (работает в группах)

### Пошаговая инструкция

#### 1. Добавление бота в чаты

1. Добавьте бота в нужные чаты/группы
2. Сделайте бота администратором (для возможности отправки сообщений)
3. В каждом чате отправьте команду `/id` чтобы получить ID чата

#### 2. Создание шаблона

1. Отправьте `/start` боту в личные сообщения
2. Нажмите "📋 Шаблоны"
3. Нажмите "➕ Создать новый"
4. Введите название шаблона (например: "Прайс-лист Ноябрь 2024")
5. Введите текст сообщения (поддерживается HTML разметка)
6. При необходимости прикрепите файл

#### 3. Создание группы чатов

1. В главном меню нажмите "👥 Группы чатов"
2. Нажмите "➕ Создать новую"
3. Введите название группы (например: "Оптовые клиенты")
4. Введите ID чатов через запятую

#### 4. Отправка рассылки

1. В главном меню нажмите "📮 Создать рассылку"
2. Выберите шаблон из списка
3. Выберите группы чатов для рассылки
4. Подтвердите отправку

## 🗄️ База данных

### SQLite (по умолчанию)

Простой вариант, не требует установки дополнительного ПО:
```bash
DB_TYPE=sqlite
DB_PATH=bot_database.db
```

### PostgreSQL

Для продакшена рекомендуется PostgreSQL:

```bash
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Создание базы данных
sudo -u postgres createdb telegram_price_bot
sudo -u postgres createuser bot_user -P

# Настройка в .env
DB_TYPE=postgresql
DB_USER=bot_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=telegram_price_bot
```

## 🔧 Развертывание на сервере

### Использование systemd (рекомендуется)

1. Создайте файл сервиса:

```bash
sudo nano /etc/systemd/system/telegram-price-bot.service
```

2. Добавьте конфигурацию:

```ini
[Unit]
Description=Telegram Price Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/telegram-price-bot
Environment="PATH=/path/to/telegram-price-bot/venv/bin"
ExecStart=/path/to/telegram-price-bot/venv/bin/python /path/to/telegram-price-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Управление сервисом:

```bash
# Перезагрузка конфигурации
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable telegram-price-bot

# Запуск
sudo systemctl start telegram-price-bot

# Статус
sudo systemctl status telegram-price-bot

# Логи
sudo journalctl -u telegram-price-bot -f
```

### Использование screen/tmux

Альтернативный вариант для быстрого запуска:

```bash
# Установка screen
sudo apt install screen

# Создание новой сессии
screen -S price-bot

# Запуск бота
cd /path/to/telegram-price-bot
source venv/bin/activate
python bot.py

# Отключение от сессии: Ctrl+A, затем D
# Подключение к сессии: screen -r price-bot
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
make test

# Только unit-тесты
make test-unit

# Интеграционные тесты
make test-integration

# С отчетом о покрытии
make test-coverage

# Конкретный тест
make test-specific TEST=TestDatabase::test_create_template
```

### Структура тестов

```
tests/
├── test_bot.py         # Основные тесты бота
├── test_database.py    # Тесты базы данных
├── test_menu.py        # Тесты системы меню
├── test_integration.py # Интеграционные тесты
└── fixtures/           # Тестовые данные
```

### Проверка качества кода

```bash
# Линтинг
make lint

# Форматирование
make format

# Полная проверка
make check
```

### CI/CD

Проект настроен для автоматического тестирования через GitHub Actions:
- Тесты запускаются при каждом push и pull request
- Поддержка Python 3.8-3.12
- Автоматическая проверка линтерами
- Отчет о покрытии кода
- Проверка безопасности зависимостей

## 📝 HTML разметка в сообщениях

Бот поддерживает HTML разметку в тексте шаблонов:

```html
<b>Жирный текст</b>
<i>Курсив</i>
<u>Подчеркнутый</u>
<s>Зачеркнутый</s>
<code>Моноширинный</code>
<a href="https://example.com">Ссылка</a>
```

Пример шаблона:
```html
<b>🎯 СПЕЦИАЛЬНОЕ ПРЕДЛОЖЕНИЕ!</b>

<i>Только до конца месяца:</i>
• Товар 1 - <s>1000₽</s> <b>800₽</b>
• Товар 2 - <s>2000₽</s> <b>1500₽</b>

📞 Заказ: <code>+7 (999) 123-45-67</code>
🌐 Сайт: <a href="https://example.com">example.com</a>
```

## 🛠️ Решение проблем

### Бот не отвечает

1. Проверьте правильность токена в `.env`
2. Убедитесь, что ваш ID есть в `ADMIN_IDS`
3. Проверьте логи: `python bot.py` или `sudo journalctl -u telegram-price-bot -f`

### Ошибка отправки в чат

1. Убедитесь, что бот добавлен в чат
2. Проверьте, что бот является администратором
3. Проверьте правильность ID чата

### База данных не создается

1. Проверьте права на запись в директории (для SQLite)
2. Проверьте подключение к PostgreSQL (если используется)
3. Убедитесь, что пользователь БД имеет права на создание таблиц

## 🎨 Расширяемая система меню

Бот использует гибкую систему меню, которую легко расширять:

### Добавление нового пункта меню

```python
from menu_system import MenuItem, MenuManager

# В файле bot.py или отдельном модуле
def setup_custom_menu(menu_manager: MenuManager):
    # Добавить пункт в главное меню
    main_menu = menu_manager.menus["main"]
    main_menu.add_item(MenuItem(
        id="custom_feature",
        text="Моя функция",
        icon="✨",
        callback_data="custom_action",
        admin_only=True
    ))
    
    # Создать подменю
    custom_menu = Menu(
        id="custom",
        title="✨ <b>Моя функция</b>",
        description="Описание функции",
        back_to="main"
    )
    menu_manager.register_menu(custom_menu)
```

### Динамические меню

```python
# Создание меню из данных БД
templates = await db.get_templates()
items = [
    {
        'id': f'template_{t.id}',
        'text': t.name,
        'icon': '📄',
        'callback_data': f'select_{t.id}'
    }
    for t in templates
]

menu_manager.add_dynamic_menu(
    menu_id="templates_list",
    title="Выберите шаблон",
    items=items
)
```

### Экспорт/импорт конфигурации меню

```python
# Экспорт текущей конфигурации
config_json = menu_manager.export_menu_config()
with open('menu_config.json', 'w') as f:
    f.write(config_json)

# Импорт конфигурации
with open('menu_config.json', 'r') as f:
    menu_manager.import_menu_config(f.read())
```

## 📊 Структура проекта

```
telegram-price-bot/
├── bot.py              # Основной файл бота
├── database.py         # Работа с базой данных  
├── config.py           # Конфигурация
├── menu_system.py      # Расширяемая система меню
├── requirements.txt    # Основные зависимости
├── requirements-dev.txt # Зависимости для разработки
├── Makefile           # Автоматизация задач
├── pytest.ini         # Конфигурация тестов
├── .coveragerc        # Настройки покрытия кода
├── .pre-commit-config.yaml # Хуки pre-commit
├── .env.example       # Пример конфигурации
├── .env               # Ваша конфигурация (не в git)
├── setup.sh           # Скрипт автоустановки
├── README.md          # Документация
├── QUICK_START.md     # Быстрый старт
├── tests/             # Тесты
│   ├── test_bot.py    # Тесты бота
│   ├── test_database.py
│   ├── test_menu.py
│   └── fixtures/
├── .github/           
│   └── workflows/     
│       └── tests.yml  # CI/CD конфигурация
└── bot_database.db    # База данных SQLite (создается автоматически)
```

## 🔒 Безопасность

- Никогда не публикуйте файл `.env` с реальными данными
- Используйте сложные пароли для PostgreSQL
- Регулярно делайте резервные копии базы данных
- Ограничивайте список администраторов минимально необходимым

## 📄 Лицензия

MIT License - свободное использование для любых целей.

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:
1. Проверьте раздел "Решение проблем"
2. Изучите код - он хорошо документирован
3. Создайте Issue на GitHub

---

*Разработано с ❤️ для упрощения рассылок в Telegram*