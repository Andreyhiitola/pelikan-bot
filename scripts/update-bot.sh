#!/bin/bash
echo "📥 Получаем обновления из GitHub..."
cd ~/pelikan-bot/pelikan-bot
git pull

echo ""
echo "🔄 Перезапускаем бота..."
docker compose restart bot

echo ""
echo "✅ Обновление завершено!"
echo ""
echo "📋 Логи:"
docker compose logs bot --tail 20
