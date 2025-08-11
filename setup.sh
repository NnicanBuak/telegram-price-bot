#!/bin/bash

# Скрипт установки Telegram Price Bot на Ubuntu
# Запуск: chmod +x setup.sh && ./setup.sh

set -e

echo "========================================="
echo "  Установка Telegram Price Bot v2.0"
echo "========================================="

# Проверка, что скрипт запущен на Ubuntu/Debian
if ! command -v apt &> /dev/null; then
    echo "❌ Этот скрипт предназначен для Ubuntu/Debian"
    exit 1
fi

# Обновление системы
echo "📦 Обновление пакетов системы..."
sudo apt update

# Установка системных зависимостей
echo "🔧 Установка системных зависимостей..."
sudo apt install -y python3 python3-pip python3-venv curl wget

# Создание структуры директорий
echo "📁 Создание структуры директорий..."
mkdir -p {data,db,logs,temp}

# Установка PostgreSQL (опционально)
read -p "Установить PostgreSQL? (y/n): " install_postgres
if [ "$install_postgres" = "y" ]; then
    echo "🐘 Установка PostgreSQL..."
    sudo apt install -y postgresql postgresql-contrib
    
    # Создание базы данных
    read -p "Введите имя базы данных (по умолчанию: telegram_price_bot): " db_name
    db_name=${db_name:-telegram_price_bot}
    
    read -p "Введите имя пользователя БД (по умолчанию: bot_user): " db_user
    db_user=${db_user:-bot_user}
    
    read -s -p "Введите пароль для пользователя БД: " db_password
    echo
    
    # Создание пользователя и базы данных
    sudo -u postgres psql <<EOF
CREATE USER $db_user WITH PASSWORD '$db_password';
CREATE DATABASE $db_name OWNER $db_user;
GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;
\\q
EOF
    
    echo "✅ PostgreSQL установлен и настроен"
    echo "База данных: $db_name"
    echo "Пользователь: $db_user"
fi

# Создание виртуального окружения
echo "📦 Создание виртуального окружения..."
python3 -m venv venv

# Активация виртуального окружения
source venv/bin/activate

# Проверка наличия requirements.txt
if [ ! -f requirements.txt ]; then
    echo "📦 Создание requirements.txt..."
    cat > requirements.txt << 'EOF'
# Telegram Bot Framework
aiogram==3.4.1

# Database
sqlalchemy[asyncio]==2.0.25
aiosqlite==0.19.0
asyncpg==0.29.0

# Configuration
python-dotenv==1.0.0

# System monitoring
psutil==5.9.7

# Development
black==23.12.1
isort==5.13.2
EOF
fi

# Установка зависимостей Python
echo "📦 Установка зависимостей Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
if [ ! -f .env ]; then
    echo "📝 Настройка конфигурации..."
    
    # Получение данных от пользователя
    read -p "Введите токен бота от @BotFather: " bot_token
    while [ -z "$bot_token" ]; do
        echo "❌ Токен бота обязателен!"
        read -p "Введите токен бота от @BotFather: " bot_token
    done
    
    read -p "Введите ваш Telegram ID (можно узнать у @userinfobot): " admin_id
    while [ -z "$admin_id" ]; do
        echo "❌ ID администратора обязателен!"
        read -p "Введите ваш Telegram ID: " admin_id
    done
    
    # Создание .env файла
    cat > .env << EOF
# =============================================================================
# TELEGRAM PRICE BOT - КОНФИГУРАЦИЯ
# =============================================================================

# Основные настройки (ОБЯЗАТЕЛЬНЫЕ)
BOT_TOKEN=$bot_token
ADMIN_IDS=$admin_id

# База данных
EOF

    if [ "$install_postgres" = "y" ]; then
        cat >> .env << EOF
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$db_name
DB_USER=$db_user
DB_PASSWORD=$db_password
EOF
    else
        cat >> .env << EOF
DB_TYPE=sqlite
DB_PATH=db/bot.db
EOF
    fi

    cat >> .env << EOF

# Файловая система
DATA_DIR=data
DB_DIR=db
LOG_DIR=logs
TEMP_DIR=temp

# Настройки рассылки
MAILING_DELAY=1.0
MAX_FILE_SIZE=20MB
MAX_MAILINGS_PER_HOUR=10

# Логирование
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5
CONSOLE_LOG=true

# Telegram
PARSE_MODE=HTML
DISABLE_WEB_PAGE_PREVIEW=true

# Безопасность
RATE_LIMIT_PER_MINUTE=20

# Развертывание
DEBUG=false
PORT=8080
HOST=0.0.0.0
EOF
    
    echo "✅ Конфигурация создана"
else
    echo "⚠️ Файл .env уже существует, пропускаем настройку"
fi

# Проверка конфигурации
echo "🔍 Проверка конфигурации..."
if python src/config.py; then
    echo "✅ Конфигурация корректна"
else
    echo "❌ Ошибка в конфигурации, проверьте файл .env"
    exit 1
fi

# Создание systemd сервиса
read -p "Создать systemd сервис для автозапуска? (y/n): " create_service
if [ "$create_service" = "y" ]; then
    echo "⚙️ Создание systemd сервиса..."
    
    SERVICE_FILE="/etc/systemd/system/telegram-price-bot.service"
    WORK_DIR=$(pwd)
    USER=$(whoami)
    
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Telegram Price Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$WORK_DIR
Environment="PATH=$WORK_DIR/venv/bin"
ExecStart=$WORK_DIR/venv/bin/python $WORK_DIR/src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$WORK_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагрузка systemd
    sudo systemctl daemon-reload
    
    # Включение автозапуска
    sudo systemctl enable telegram-price-bot
    
    echo "✅ Systemd сервис создан"
fi

# Создание скрипта запуска
echo "📝 Создание скриптов управления..."

cat > start.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python src/main.py
EOF

cat > stop.sh << 'EOF'
#!/bin/bash
if [ -f telegram-price-bot.pid ]; then
    kill $(cat telegram-price-bot.pid)
    rm telegram-price-bot.pid
    echo "Бот остановлен"
else
    echo "PID файл не найден"
fi
EOF

cat > status.sh << 'EOF'
#!/bin/bash
if [ "$create_service" = "y" ]; then
    sudo systemctl status telegram-price-bot
else
    if [ -f telegram-price-bot.pid ]; then
        echo "Бот запущен (PID: $(cat telegram-price-bot.pid))"
    else
        echo "Бот не запущен"
    fi
fi
EOF

chmod +x start.sh stop.sh status.sh

# Создание .gitignore
echo "📝 Создание .gitignore..."
cat > .gitignore << 'EOF'
# Конфигурация
.env
.env.local

# База данных
db/
*.db
*.sqlite

# Логи
logs/
*.log

# Временные файлы
temp/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.pytest_cache/

# Виртуальное окружение
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Системные файлы
.DS_Store
Thumbs.db

# PID файлы
*.pid
EOF

echo ""
echo "========================================="
echo "✅ Установка завершена!"
echo "========================================="
echo ""
echo "📂 Структура проекта:"
echo "├── src/          - исходный код"
echo "├── data/         - пользовательские данные"
echo "├── db/           - база данных"
echo "├── logs/         - файлы логов"
echo "├── temp/         - временные файлы"
echo "├── venv/         - виртуальное окружение"
echo "└── .env          - конфигурация"
echo ""
echo "🚀 Для запуска бота:"
echo ""

if [ "$create_service" = "y" ]; then
    echo "1. Как системный сервис:"
    echo "   sudo systemctl start telegram-price-bot    # Запуск"
    echo "   sudo systemctl stop telegram-price-bot     # Остановка"
    echo "   sudo systemctl restart telegram-price-bot  # Перезапуск"
    echo "   sudo systemctl status telegram-price-bot   # Статус"
    echo "   sudo journalctl -u telegram-price-bot -f   # Логи"
    echo ""
    echo "2. В режиме разработки:"
    echo "   ./start.sh"
    echo ""
else
    echo "1. В режиме разработки:"
    echo "   ./start.sh"
    echo ""
    echo "2. Вручную:"
    echo "   source venv/bin/activate"
    echo "   python src/main.py"
    echo ""
fi

echo "📋 Полезные команды:"
echo "• ./status.sh          - проверить статус"
echo "• ./stop.sh            - остановить бота"
echo "• python src/config.py - проверить конфигурацию"
echo ""
echo "📝 Важно:"
echo "• Добавьте бота в нужные чаты как администратора"
echo "• Проверьте настройки в файле .env"
echo "• Используйте команду /id в чатах для получения их ID"
echo "• Логи сохраняются в папку logs/"
echo ""

# Проверка прав доступа
echo "🔐 Установка прав доступа..."
chmod 600 .env  # Только владелец может читать конфигурацию
chmod 755 {data,db,logs,temp}  # Папки доступны для записи
chmod +x src/main.py

read -p "Запустить бота сейчас? (y/n): " start_now
if [ "$start_now" = "y" ]; then
    if [ "$create_service" = "y" ]; then
        echo "🚀 Запуск бота как сервис..."
        sudo systemctl start telegram-price-bot
        sleep 3
        sudo systemctl status telegram-price-bot
    else
        echo "🚀 Запуск бота..."
        ./start.sh
    fi
fi

echo ""
echo "✅ Готово! Бот установлен и настроен."
echo "📞 При проблемах проверьте логи в папке logs/"