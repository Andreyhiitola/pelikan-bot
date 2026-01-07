# 🚀 Развёртывание на VPS

## Информация о VPS

**Нужно знать:**
- IP адрес: _____________
- SSH пользователь: root / ubuntu / другой
- SSH порт: 22 (обычно)
- ОС: Ubuntu / Debian / CentOS

---

## Шаг 1: Подключение к VPS
```bash
# Подключиться
ssh user@YOUR_VPS_IP

# Или с указанием порта
ssh -p 22 user@YOUR_VPS_IP

# Если нужен ключ
ssh -i ~/.ssh/id_rsa user@YOUR_VPS_IP
```

---

## Шаг 2: Подготовка VPS
```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить необходимое
sudo apt install -y git curl wget nano

# Установить Docker
curl -fsSL https://get.docker.com | sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниться (или выполнить)
newgrp docker

# Проверить Docker
docker --version
docker-compose --version
```

---

## Шаг 3: Клонировать проект
```bash
# Перейти в домашнюю директорию
cd ~

# Клонировать
git clone https://github.com/Andreyhiitola/pelikan-bot.git

# Перейти в проект
cd pelikan-bot

# Проверить файлы
ls -la
```

---

## Шаг 4: Настроить .env
```bash
# Создать .env
nano .env
```

**Вставить:**
```bash
# Telegram Bot Token
BOT_TOKEN=8403481827:AAFS7...

# Admin Telegram IDs (через запятую)
ADMIN_IDS=31310268

# Database
DB_FILE=/app/data/orders.db

# URLs (пока без HTTPS)
WEBHOOK_URL=http://YOUR_VPS_IP:8080/api/order
WEBAPP_URL=https://pelikan-alakol-site-v2.pages.dev
```

**Сохранить:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

## Шаг 5: Запустить бота
```bash
# Создать директорию для БД
mkdir -p data

# Запустить Docker Compose
docker-compose up -d

# Проверить что запустилось
docker-compose ps

# Должно показать:
# pelikan-bot   Up
# watchtower    Up
```

---

## Шаг 6: Проверить логи
```bash
# Посмотреть логи бота
docker-compose logs -f bot

# Должно быть примерно так:
# INFO:__main__:Бот запущен и готов к работе
# INFO:aiogram.dispatcher:Start polling

# Выйти из логов: Ctrl+C
```

---

## Шаг 7: Тестирование бота

**В Telegram:**
1. Открыть: @Pelican_alacol_hotel_bot
2. Отправить: `/start`
3. Должен ответить приветствием!
4. Проверить: `/bar`, `/stolovaya`, `/info`

✅ **Бот работает!**

---

## Шаг 8: Настроить Nginx (для HTTPS в будущем)
```bash
# Установить Nginx
sudo apt install -y nginx

# Установить Certbot
sudo apt install -y certbot python3-certbot-nginx

# Создать конфиг
sudo nano /etc/nginx/sites-available/pelikan-bot
```

**Пока базовая конфигурация (без домена):**
```nginx
server {
    listen 80;
    server_name YOUR_VPS_IP;

    location /api/ {
        proxy_pass http://localhost:8080/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /health {
        proxy_pass http://localhost:8080/health;
    }
}
```
```bash
# Активировать конфиг
sudo ln -s /etc/nginx/sites-available/pelikan-bot /etc/nginx/sites-enabled/

# Проверить синтаксис
sudo nginx -t

# Перезапустить Nginx
sudo systemctl restart nginx

# Включить автозапуск
sudo systemctl enable nginx
```

---

## Шаг 9: Открыть порты (если firewall активен)
```bash
# Проверить firewall
sudo ufw status

# Если активен, открыть порты:
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (для будущего)
sudo ufw allow 8080/tcp  # Bot webhook (временно)

# Перезагрузить
sudo ufw reload
```

---

## Шаг 10: Проверка webhook endpoint
```bash
# На VPS
curl http://localhost:8080/health

# С локальной машины
curl http://YOUR_VPS_IP:8080/health

# Должно вернуть: {"status":"ok"}
```

---

## Управление ботом
```bash
# Остановить
docker-compose down

# Запустить
docker-compose up -d

# Перезапустить
docker-compose restart

# Логи
docker-compose logs -f bot

# Обновить (pull новая версия)
git pull
docker-compose pull
docker-compose up -d

# Статус
docker-compose ps

# Статистика ресурсов
docker stats pelikan-bot
```

---

## Автообновление через Watchtower

**Watchtower уже работает!**
```bash
# Проверить логи Watchtower
docker-compose logs -f watchtower

# Watchtower автоматически:
# - Проверяет Docker Hub каждые 5 минут
# - Скачивает новый образ если есть
# - Перезапускает контейнер
# - Удаляет старый образ
```

**Workflow обновления:**
```
Локально → git push → 
GitHub Actions → Docker Hub → 
Watchtower → Обновлён! (автоматически)
```

---

## Troubleshooting

### Бот не отвечает
```bash
# Проверить что контейнер запущен
docker-compose ps

# Посмотреть логи
docker-compose logs bot

# Перезапустить
docker-compose restart bot
```

### Ошибка "port already in use"
```bash
# Проверить что занимает порт 8080
sudo lsof -i :8080

# Или
sudo netstat -tulpn | grep 8080

# Остановить процесс
sudo kill -9 <PID>
```

### База данных не создаётся
```bash
# Проверить volume
docker-compose down
rm -rf data/
mkdir -p data
docker-compose up -d
```

### GitHub Actions не собирает образ
```bash
# Проверить что Secrets добавлены:
# GitHub → Settings → Secrets → Actions
# - DOCKERHUB_USERNAME
# - DOCKERHUB_TOKEN
```

---

## Резервное копирование
```bash
# Backup базы данных
cp data/orders.db data/orders.db.backup_$(date +%Y%m%d)

# Или автоматически (crontab)
crontab -e

# Добавить:
0 2 * * * cp ~/pelikan-bot/data/orders.db ~/pelikan-bot/data/orders.db.backup_$(date +\%Y\%m\%d)

# Backup каждый день в 2:00
```

---

## Мониторинг
```bash
# Использование ресурсов
docker stats

# Логи в реальном времени
docker-compose logs -f

# Последние 100 строк
docker-compose logs --tail=100

# Размер логов
du -sh /var/lib/docker/containers/*/
```
