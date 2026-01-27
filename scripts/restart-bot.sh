#!/bin/bash
echo "🔄 Перезапускаем бота..."
cd ~/pelikan-bot/pelikan-bot
docker compose restart bot
echo "✅ Готово!"
echo ""
echo "📋 Последние логи:"
docker compose logs bot --tail 20
