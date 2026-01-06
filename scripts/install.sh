#!/bin/bash
# =============================================================================
# Скрипт первоначальной установки Telegram-бота "Пеликан Алаколь" на VPS
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

check_error() {
    if [ $? -ne 0 ]; then
        print_error "$1"
        exit 1
    fi
}

echo "=========================================="
echo "  Установка бота Пеликан Алаколь"
echo "  (Polling версия - БЕЗ домена!)"
echo "=========================================="
echo ""

# Настройки
REPO_URL="https://github.com/yourusername/telegram_bot_pelican_alacol.git"
INSTALL_DIR="$HOME/telegram_bot_pelican_alacol"
USERNAME=$(whoami)

# 1. Проверка системы
print_step "1/9 Проверка системы..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    print_info "ОС: $NAME $VERSION"
else
    print_error "Не удалось определить ОС"
    exit 1
fi

# 2. Обновление системы
print_step "2/9 Обновление системы..."
print_warning "Это может занять несколько минут..."
sudo apt update && sudo apt upgrade -y
check_error "Ошибка обновления системы"

# 3. Установка необходимых пакетов
print_step "3/9 Установка зависимостей..."
sudo apt install -y python3 python3-pip python3-venv git curl
check_error "Ошибка установки пакетов"

# Проверка версии Python
PYTHON_VERSION=$(python3 --version)
print_info "Python: $PYTHON_VERSION"

# 4. Клонирование репозитория
print_step "4/9 Клонирование репозитория..."
if [ -d "$INSTALL_DIR" ]; then
    print_warning "Директория $INSTALL_DIR уже существует"
    read -p "Удалить и клонировать заново? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
        check_error "Ошибка клонирования репозитория"
    fi
else
    git clone "$REPO_URL" "$INSTALL_DIR"
    check_error "Ошибка клонирования репозитория"
fi

cd "$INSTALL_DIR"
print_info "Репозиторий клонирован в $INSTALL_DIR"

# 5. Создание виртуального окружения
print_step "5/9 Создание виртуального окружения..."
python3 -m venv venv
check_error "Ошибка создания venv"

source venv/bin/activate
check_error "Ошибка активации venv"

# 6. Установка зависимостей Python
print_step "6/9 Установка Python зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt
check_error "Ошибка установки зависимостей"

deactivate

# 7. Настройка конфигурации
print_step "7/9 Настройка конфигурации..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp .env.example .env
    print_info "Создан файл .env"
    echo ""
    print_warning "ВАЖНО! Отредактируйте файл .env:"
    print_warning "  nano .env"
    echo ""
    print_warning "Укажите:"
    print_warning "  - BOT_TOKEN (получите у @BotFather)"
    print_warning "  - ADMIN_IDS (ваш Telegram ID)"
    echo ""
    read -p "Нажмите Enter, чтобы открыть редактор..."
    nano .env
fi

# 8. Установка systemd сервисов
print_step "8/9 Установка systemd сервисов..."

# Обновляем пути в файлах сервисов
sed -i "s|/home/youruser/pelikan-bar-bot|$INSTALL_DIR|g" pelikan-bot.service
sed -i "s|User=youruser|User=$USERNAME|g" pelikan-bot.service

sed -i "s|/home/youruser/pelikan-bar-bot|$INSTALL_DIR|g" pelikan-webhook.service
sed -i "s|User=youruser|User=$USERNAME|g" pelikan-webhook.service

# Копируем в systemd
sudo cp pelikan-bot.service /etc/systemd/system/
check_error "Ошибка копирования service файла"

# Перезагружаем systemd
sudo systemctl daemon-reload
check_error "Ошибка перезагрузки systemd"

# Включаем автозапуск
sudo systemctl enable pelikan-bot.service
check_error "Ошибка включения автозапуска"

print_info "Сервис установлен и включен для автозапуска"

# 9. Запуск сервиса
print_step "9/9 Запуск сервиса..."
sudo systemctl start pelikan-bot.service
sleep 2
if systemctl is-active --quiet pelikan-bot.service; then
    print_info "✓ pelikan-bot.service запущен"
else
    print_error "✗ pelikan-bot.service не запустился!"
    sudo systemctl status pelikan-bot.service --no-pager -l
fi

# Финал
echo ""
echo "=========================================="
print_info "✓ Установка завершена! 🎉"
echo "=========================================="
echo ""

print_info "Полезные команды:"
echo ""
echo "  Проверка статуса бота:"
echo "    sudo systemctl status pelikan-bot"
echo ""
echo "  Просмотр логов:"
echo "    sudo journalctl -u pelikan-bot -f"
echo ""
echo "  Перезапуск бота:"
echo "    sudo systemctl restart pelikan-bot"
echo ""
echo "  Развёртывание обновлений:"
echo "    cd $INSTALL_DIR && ./scripts/deploy.sh"
echo ""
echo "  Проверка webhook:"
echo "    curl http://localhost:8080/health"
echo ""

print_warning "Не забудьте:"
print_warning "1. Открыть порт 8080 в файрволе для webhook"
print_warning "   sudo ufw allow 8080/tcp"
print_warning "2. Обновить URL webhook на сайте"
print_warning "   http://your-server-ip:8080/api/order"
echo ""

print_info "Текущий статус сервиса:"
sudo systemctl status pelikan-bot --no-pager -l | head -n 10
