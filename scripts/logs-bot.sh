#!/bin/bash
echo "📋 Логи бота (Ctrl+C для выхода):"
cd ~/pelikan-bot/pelikan-bot
docker compose logs -f bot
