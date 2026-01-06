# 🍽 Telegram-бот системы заказов бара "Пеликан Алаколь"

Telegram-бот для приёма и управления заказами из бара. Работает совместно с веб-сайтом заказов.

## 📋 Возможности

### Для клиентов:
- ✅ Получение подтверждения заказа
- 📊 Проверка статуса заказа по номеру
- 🔔 Уведомления об изменении статуса
- 🔐 Защита данных через верификацию по номеру комнаты

### Для администраторов:
- 🆕 Уведомления о новых заказах
- 📝 Управление статусами заказов
- 📋 Просмотр списка активных заказов
- 📊 Статистика по заказам

## 🏗 Архитектура

Проект состоит из двух компонентов:

1. **Telegram Bot** (`bot.py`) - основной бот для взаимодействия с пользователями
2. **Webhook Server** (`webhook_server.py`) - принимает заказы с веб-сайта

```
Website (bar.html)
      ↓
   [POST /api/order]
      ↓
Webhook Server (port 8080)
      ↓
   save_order()
      ↓
    Database (SQLite)
      ↓
Telegram Bot → Уведомления пользователям
```

## 🚀 Установка на VPS

### Предварительные требования

- Ubuntu 20.04+ / Debian 11+
- Python 3.8+
- Git
- Sudo права
- Telegram Bot Token (получите у [@BotFather](https://t.me/BotFather))

### Быстрая установка

1. **Клонируйте репозиторий:**
```bash
cd ~
git clone https://github.com/yourusername/pelikan-bar-bot.git
cd pelikan-bar-bot
```

2. **Запустите скрипт установки:**
```bash
chmod +x install.sh
./install.sh
```

3. **Настройте конфигурацию:**
```bash
nano .env
```

Заполните:
```env
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=your_telegram_id,another_admin_id
DB_FILE=orders.db
WEBHOOK_PORT=8080
WEBHOOK_PATH=/api/order
```

4. **Запустите сервисы:**
```bash
sudo systemctl start pelikan-bot
sudo systemctl start pelikan-webhook
```

### Ручная установка

<details>
<summary>Развернуть инструкцию</summary>

1. **Обновите систему:**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Установите зависимости:**
```bash
sudo apt install -y python3 python3-pip python3-venv git
```

3. **Клонируйте репозиторий:**
```bash
cd ~
git clone https://github.com/yourusername/pelikan-bar-bot.git
cd pelikan-bar-bot
```

4. **Создайте виртуальное окружение:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

5. **Настройте конфигурацию:**
```bash
cp .env.example .env
nano .env
```

6. **Настройте systemd сервисы:**
```bash
# Отредактируйте пути в файлах сервисов
sudo nano pelikan-bot.service
sudo nano pelikan-webhook.service

# Скопируйте в systemd
sudo cp pelikan-bot.service /etc/systemd/system/
sudo cp pelikan-webhook.service /etc/systemd/system/

# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable pelikan-bot
sudo systemctl enable pelikan-webhook

# Запустите сервисы
sudo systemctl start pelikan-bot
sudo systemctl start pelikan-webhook
```

</details>

## 🔧 Настройка Nginx

1. **Установите Nginx:**
```bash
sudo apt install nginx
```

2. **Скопируйте конфигурацию:**
```bash
sudo cp nginx-pelikan-bar.conf /etc/nginx/sites-available/pelikan-bar
sudo ln -s /etc/nginx/sites-available/pelikan-bar /etc/nginx/sites-enabled/
```

3. **Получите SSL сертификат:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d bar.pelikan-alakol.kz
```

4. **Проверьте и перезапустите Nginx:**
```bash
sudo nginx -t
sudo systemctl restart nginx
```

## 📱 Использование

### Команды для пользователей:

- `/start` - начать работу с ботом
- `/status <order_id>` - проверить статус заказа
- `/help` - помощь

### Команды для администраторов:

- `/update <order_id> <status>` - изменить статус заказа
  - Статусы: `принят`, `готовится`, `готов`, `выдан`
- `/orders` - список активных заказов
- `/stats` - статистика заказов

### Примеры:

```
/status 1736172000
→ Укажите номер комнаты: 205
→ Показывается статус заказа

/update 1736172000 готов
→ Статус изменён, клиент получает уведомление
```

## 🔄 Развёртывание обновлений

### Автоматическое развёртывание:

```bash
cd ~/pelikan-bar-bot
./deploy.sh
```

Скрипт автоматически:
- Получает изменения из Git
- Обновляет зависимости (если нужно)
- Перезапускает сервисы
- Показывает статус

### GitHub Webhook (опционально):

<details>
<summary>Настройка автоматического деплоя при push</summary>

1. **Создайте webhook endpoint** (добавьте в `webhook_server.py`):
```python
async def handle_github_webhook(request):
    # Валидация GitHub signature
    # Запуск ./deploy.sh
    pass
```

2. **В настройках GitHub репозитория:**
   - Settings → Webhooks → Add webhook
   - Payload URL: `https://bar.pelikan-alakol.kz/api/deploy`
   - Content type: `application/json`
   - Secret: (ваш секретный ключ)
   - Events: `Just the push event`

</details>

## 📊 Мониторинг

### Просмотр логов:

```bash
# Логи бота
sudo journalctl -u pelikan-bot -f

# Логи webhook сервера
sudo journalctl -u pelikan-webhook -f

# Последние 100 строк
sudo journalctl -u pelikan-bot -n 100
```

### Статус сервисов:

```bash
# Проверка статуса
sudo systemctl status pelikan-bot
sudo systemctl status pelikan-webhook

# Перезапуск
sudo systemctl restart pelikan-bot
sudo systemctl restart pelikan-webhook

# Остановка
sudo systemctl stop pelikan-bot
sudo systemctl stop pelikan-webhook
```

## 🗄 База данных

SQLite база данных хранится в файле `orders.db`

### Структура таблицы `orders`:

```sql
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    client_name TEXT,
    room TEXT,
    telegram TEXT,
    items TEXT,           -- JSON array
    total INTEGER,
    status TEXT,          -- принят, готовится, готов, выдан
    timestamp TEXT,
    created_at TIMESTAMP
);
```

### Резервное копирование:

```bash
# Создать бэкап
cp orders.db orders-backup-$(date +%Y%m%d).db

# Автоматический бэкап (добавьте в crontab)
0 3 * * * cp /home/youruser/pelikan-bar-bot/orders.db /home/youruser/backups/orders-$(date +\%Y\%m\%d).db
```

## 🔐 Безопасность

- ✅ Верификация клиентов по номеру комнаты
- ✅ Доступ к админ-командам только для указанных ID
- ✅ HTTPS для webhook
- ✅ Валидация входящих данных
- ✅ Логирование всех операций

## 🛠 Troubleshooting

### Бот не получает заказы с сайта

1. Проверьте webhook сервер:
```bash
curl http://localhost:8080/health
```

2. Проверьте логи:
```bash
sudo journalctl -u pelikan-webhook -f
```

3. Проверьте Nginx:
```bash
sudo nginx -t
curl https://bar.pelikan-alakol.kz/health
```

### Бот не отправляет уведомления

1. Проверьте токен бота в `.env`
2. Проверьте ADMIN_IDS
3. Убедитесь, что пользователи начали чат с ботом (`/start`)

### База данных заблокирована

```bash
# Проверьте, нет ли других процессов использующих БД
lsof orders.db

# Перезапустите сервисы
sudo systemctl restart pelikan-bot
sudo systemctl restart pelikan-webhook
```

## 📝 API Webhook

### POST /api/order

Принимает заказы с сайта.

**Request:**
```json
{
  "orderId": "1736172000",
  "name": "Иван Иванов",
  "room": "205",
  "telegram": "username",
  "items": [
    {
      "name": "Пицца Пепперони",
      "price": 3500,
      "quantity": 1
    }
  ],
  "total": 3500,
  "timestamp": "2026-01-06 15:30"
}
```

**Response:**
```json
{
  "status": "ok",
  "order_id": "1736172000"
}
```

### GET /health

Проверка здоровья сервера.

**Response:**
```json
{
  "status": "ok",
  "service": "pelikan-bar-webhook"
}
```

## 📄 Структура проекта

```
pelikan-bar-bot/
├── bot.py                      # Основной бот
├── webhook_server.py           # Webhook сервер
├── requirements.txt            # Python зависимости
├── .env.example                # Пример конфигурации
├── .env                        # Конфигурация (не в Git)
├── orders.db                   # База данных (не в Git)
├── install.sh                  # Скрипт установки
├── deploy.sh                   # Скрипт деплоя
├── pelikan-bot.service         # Systemd сервис бота
├── pelikan-webhook.service     # Systemd сервис webhook
├── nginx-pelikan-bar.conf      # Конфигурация Nginx
└── README.md                   # Документация
```

## 🤝 Интеграция с сайтом

На сайте (`bar.html`) используйте следующий код для отправки заказа:

```javascript
async function sendOrder(orderData) {
    try {
        const response = await fetch('https://bar.pelikan-alakol.kz/api/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                orderId: Date.now().toString(),
                name: orderData.name,
                room: orderData.room,
                telegram: orderData.telegram,
                items: orderData.items,
                total: orderData.total,
                timestamp: new Date().toLocaleString('ru-RU')
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'ok') {
            alert(`Заказ #${result.order_id} принят!`);
        }
    } catch (error) {
        console.error('Ошибка отправки заказа:', error);
        alert('Ошибка при оформлении заказа');
    }
}
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u pelikan-bot -n 100`
2. Проверьте статус: `sudo systemctl status pelikan-bot`
3. Создайте Issue в GitHub репозитории

## 📜 Лицензия

MIT License

## 🎯 TODO

- [ ] Добавить поддержку нескольких языков
- [ ] Панель администратора (web)
- [ ] Экспорт статистики в Excel
- [ ] Интеграция с платёжными системами
- [ ] Push-уведомления для веб-версии
- [ ] Графики и аналитика заказов

---

Сделано с ❤️ для бара "Пеликан Алаколь"
