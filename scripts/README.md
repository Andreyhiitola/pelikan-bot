# VPS Management Scripts

Скрипты для управления Telegram ботом на VPS.

## Установка на новом VPS

После клонирования репозитория:
```bash
# Копируем скрипты
cp -r ~/pelikan-bot/pelikan-bot/scripts ~/scripts
chmod +x ~/scripts/*.sh

# Добавляем алиасы
cat >> ~/.bashrc << 'EOF'

# Pelikan Bot управление
alias bot-restart='~/scripts/restart-bot.sh'
alias bot-logs='~/scripts/logs-bot.sh'
alias bot-update='~/scripts/update-bot.sh'
alias bot-status='~/scripts/status-bot.sh'
alias bot-backups='~/scripts/list-backups.sh'
alias bot-backup='~/scripts/backup-db.sh'
alias bot-help='~/scripts/help-bot.sh'
EOF

source ~/.bashrc
```

## Настройка crontab
```bash
crontab -e
```

Добавьте:
```cron
# Бэкап базы данных каждый день в 3:00
0 3 * * * ~/scripts/backup-db.sh >> ~/backups/backup.log 2>&1

# Проверка бота каждые 5 минут
*/5 * * * * ~/scripts/check-bot.sh >> ~/monitor.log 2>&1
```

## Доступные команды

- `bot-status` - Статус системы
- `bot-logs` - Логи в реальном времени
- `bot-restart` - Перезапуск
- `bot-update` - Обновление с GitHub
- `bot-backup` - Создать бэкап
- `bot-backups` - Список бэкапов
- `bot-help` - Справка
