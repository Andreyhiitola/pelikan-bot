#!/bin/bash
echo "=== 📊 Статус Pelikan Bot ==="
echo ""
echo "🐳 Docker контейнеры:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "💾 Последние бэкапы:"
ls -lth ~/backups/*.db 2>/dev/null | head -5
echo ""
echo "📁 Использование диска:"
df -h / | tail -1
echo ""
echo "🔍 Процессы бота:"
docker compose ps
