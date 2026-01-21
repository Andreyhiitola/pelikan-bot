#!/bin/bash
cd ~/pelikan-bot/pelikan-bot
echo "🔄 Останавливаем контейнеры..."
docker compose down
echo "🚀 Запускаем контейнеры..."
docker compose up -d
echo "✅ Готово! Проверяем статус:"
docker ps
echo ""
echo "📋 Логи бота (Ctrl+C для выхода):"
docker compose logs -f bot
