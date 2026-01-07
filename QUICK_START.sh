#!/bin/bash
# Быстрый старт на VPS

echo "🚀 Установка Docker..."
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

echo "📦 Клонирование проекта..."
cd ~
git clone https://github.com/Andreyhiitola/pelikan-bot.git
cd pelikan-bot

echo "⚙️ Создание .env..."
cat > .env << 'EOF'
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_IDS=YOUR_TELEGRAM_ID
DB_FILE=/app/data/orders.db
WEBHOOK_URL=http://YOUR_VPS_IP:8080/api/order
WEBAPP_URL=https://pelikan-alakol-site-v2.pages.dev
EOF

echo "📝 Отредактируйте .env файл:"
echo "nano .env"
echo ""
echo "Затем запустите:"
echo "docker-compose up -d"
