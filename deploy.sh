#!/bin/bash
set -e

echo "🔄 Начинаем обновление бота..."

cd ~/pelikan-bot

echo "📥 Получаем изменения из GitHub..."
git reset --hard HEAD
git pull origin main

echo "🛑 Останавливаем контейнеры..."
docker-compose down

echo "🗑️ Удаляем старый образ..."
docker rmi andreyhiitola/pelikan-bot:latest 2>/dev/null || true

echo "🔨 Пересборка образа..."
docker-compose build --no-cache

echo "🚀 Запускаем контейнеры..."
docker-compose up -d

echo "⏳ Ждём 5 секунд..."
sleep 5

echo "📋 Проверяем статус..."
docker-compose ps

echo ""
echo "✅ Обновление завершено!"
echo ""
echo "📊 Логи:"
docker-compose logs --tail=10 bot

echo ""
echo "Для просмотра логов: docker-compose logs -f bot"
