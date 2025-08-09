#!/bin/bash

# Скрипт установки Telegram Price Bot на Ubuntu
# Запуск: chmod +x setup.sh && ./setup.sh

set -e

echo "========================================="
echo "  Установка Telegram Price Bot"
echo "========================================="

# Проверка, что скрипт запущен на Ubuntu
if ! command -v apt &> /dev/null; then
    echo "❌ Этот скрипт предназначен для Ubuntu/Debian"
    exit 1
fi

# Обновление системы
echo "📦 Обновление пакетов системы..."
sudo apt update

# Установка Python и pip
echo "🐍 Установка Python..."
sudo apt install -y python3 python3-pip python3-venv

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

# Установка зависимостей
echo "📦 Установка зависимостей Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
if [ ! -f .env ]; then
    echo "📝 Настройка конфигурации..."
    cp .env.example .env
    
    read -p "Введите токен бота от @BotFather: " bot_token
    sed -i "s/YOUR_BOT_TOKEN_HERE/$bot_token/" .env
    
    read -p "Введите ваш Telegram ID (можно узнать у @userinfobot): " admin_id
    sed -i "s/123456789,987654321/$admin_id/" .env
    
    if [ "$install_postgres" = "y" ]; then
        sed -i "s/DB_TYPE=sqlite/DB_TYPE=postgresql/" .env
        sed -i "s/# DB_USER=/DB_USER=/" .env
        sed -i "s/# DB_PASSWORD=/DB_PASSWORD=/" .env
        sed -i "s/# DB_HOST=/DB_HOST=/" .env
        sed -i "s/# DB_PORT=/DB_PORT=/" .env
        sed -i "s/# DB_NAME=/DB_NAME=/" .env
        
        sed -i "s/DB_USER=postgres/DB_USER=$db_user/" .env
        sed -i "s/DB_PASSWORD=your_password/DB_PASSWORD=$db_password/" .env
        sed -i "s/DB_NAME=telegram_price_bot/DB_NAME=$db_name/" .env
    fi
    
    echo "✅ Конфигурация создана"
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

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment="PATH=$WORK_DIR/venv/bin"
ExecStart=$WORK_DIR/venv/bin/python $WORK_DIR/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагрузка systemd
    sudo systemctl daemon-reload
    
    # Включение автозапуска
    sudo systemctl enable telegram-price-bot
    
    echo "✅ Systemd сервис создан"
    echo ""
    echo "Команды управления сервисом:"
    echo "  Запуск:       sudo systemctl start telegram-price-bot"
    echo "  Остановка:    sudo systemctl stop telegram-price-bot"
    echo "  Перезапуск:   sudo systemctl restart telegram-price-bot"
    echo "  Статус:       sudo systemctl status telegram-price-bot"
    echo "  Логи:         sudo journalctl -u telegram-price-bot -f"
fi

echo ""
echo "========================================="
echo "✅ Установка завершена!"
echo "========================================="
echo ""
echo "Для запуска бота:"
echo ""
echo "1. В режиме разработки:"
echo "   source venv/bin/activate"
echo "   python bot.py"
echo ""

if [ "$create_service" = "y" ]; then
    echo "2. Как системный сервис:"
    echo "   sudo systemctl start telegram-price-bot"
    echo ""
fi

echo "Не забудьте:"
echo "• Добавить бота в нужные чаты как администратора"
echo "• Проверить настройки в файле .env"
echo ""

read -p "Запустить бота сейчас? (y/n): " start_now
if [ "$start_now" = "y" ]; then
    if [ "$create_service" = "y" ]; then
        sudo systemctl start telegram-price-bot
        echo "✅ Бот запущен как сервис"
        echo "Проверить статус: sudo systemctl status telegram-price-bot"
    else
        echo "Запуск бота..."
        python bot.py
    fi
fi