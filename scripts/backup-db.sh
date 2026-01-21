#!/bin/bash
# Бэкап базы данных Pelikan Bot
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH=~/pelikan-bot/pelikan-bot/data/orders.db

# Создаём директорию для бэкапов
mkdir -p $BACKUP_DIR

# Копируем базу
if [ -f "$DB_PATH" ]; then
    cp $DB_PATH $BACKUP_DIR/orders_$DATE.db
    echo "✅ Backup created: orders_$DATE.db"
    
    # Удаляем бэкапы старше 30 дней
    find $BACKUP_DIR -name "orders_*.db" -mtime +30 -delete
    echo "🗑️ Old backups cleaned (>30 days)"
else
    echo "❌ Database not found: $DB_PATH"
fi
