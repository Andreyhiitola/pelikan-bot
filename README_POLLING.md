# 🍽 Telegram Bot - Система заказов бара "Пеликан Алаколь" (Polling версия)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.15-green.svg)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Telegram-бот для автоматизации приёма и управления заказами из бара. **Версия с polling** - не требует домена и SSL сертификата!

## ✨ Основные возможности

### Для клиентов
- ✅ Автоматическое подтверждение заказа
- 📊 Проверка статуса заказа в реальном времени
- 🔔 Уведомления об изменении статуса
- 🔐 Защита данных через верификацию

### Для администраторов
- 🆕 Мгновенные уведомления о новых заказах
- 📝 Управление статусами заказов
- 📋 Просмотр активных заказов
- 📊 Статистика и аналитика

## 🚀 Быстрый старт (БЕЗ ДОМЕНА!)

### Вариант 1: Запуск на VPS

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/telegram_bot_pelican_alacol.git
cd telegram_bot_pelican_alacol

# 2. Установите зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Настройте .env
cp .env.example .env
nano .env
# Укажите BOT_TOKEN и ADMIN_IDS

# 4. Запустите бота
python bot.py
```

### Вариант 2: Запуск локально (на компьютере)

```bash
# 1. Скачайте и распакуйте проект
# 2. Установите Python 3.8+

# Windows:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python bot.py

# Linux/Mac:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### Вариант 3: Автоматическая установка на VPS

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

## 📦 Что входит в проект

```
telegram_bot_pelican_alacol/
├── bot.py                          # Основной бот (polling + встроенный webhook)
├── requirements.txt                # Зависимости
├── .env.example                    # Пример конфигурации
│
├── scripts/                        # Скрипты установки
│   ├── install.sh                  # Автоматическая установка
│   ├── deploy.sh                   # Обновление
│   └── pelikan-bot.service         # Systemd сервис
│
├── docs/                           # Документация
│   ├── QUICKSTART.md               # Быстрый старт
│   └── SQL_COMMANDS.md             # SQL команды
│
└── examples/                       # Примеры
    ├── bar-integration.js          # JavaScript для сайта
    └── bar-checkout-example.html   # Пример формы
```

## 🔧 Настройка

### 1. Получите Telegram Bot Token

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

### 2. Узнайте свой Telegram ID

1. Найдите [@userinfobot](https://t.me/userinfobot)
2. Нажмите `/start`
3. Скопируйте ваш ID (число)

### 3. Настройте .env файл

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DB_FILE=orders.db
WEBHOOK_PORT=8080
```

## 💻 Как работает

### Архитектура

```
Website (bar.html)
      ↓
   [POST http://your-server-ip:8080/api/order]
      ↓
Встроенный Webhook в bot.py
      ↓
    Database (SQLite)
      ↓
Telegram Bot → Уведомления
```

### Два режима работы одновременно:

1. **Polling** - бот получает сообщения от пользователей
2. **Webhook** - встроенный HTTP сервер принимает заказы с сайта

## 🌐 Интеграция с сайтом

На вашем сайте используйте:

```javascript
// Для локальной разработки
const API_URL = 'http://localhost:8080/api/order';

// Для production (замените на IP вашего сервера)
const API_URL = 'http://your-server-ip:8080/api/order';

async function sendOrder(orderData) {
    const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
    return await response.json();
}
```

**Полный пример:** [examples/bar-integration.js](examples/bar-integration.js)

## 📱 Команды бота

### Для клиентов:
```
/start - Начать работу
/status <order_id> - Проверить статус заказа
/help - Помощь
```

### Для администраторов:
```
/update <order_id> <status> - Изменить статус
/orders - Список активных заказов
/stats - Статистика
```

**Статусы:** `принят`, `готовится`, `готов`, `выдан`

## 🖥 Запуск на разных системах

### Ubuntu/Debian (VPS)

```bash
# Установка как сервис
sudo cp scripts/pelikan-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pelikan-bot
sudo systemctl start pelikan-bot

# Просмотр логов
sudo journalctl -u pelikan-bot -f
```

### Windows

```powershell
# Запуск в фоне
start pythonw bot.py

# Или через Task Scheduler для автозапуска
```

### macOS

```bash
# Использование launchd
cp scripts/com.pelikan.bot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pelikan.bot.plist
```

### Docker

```bash
docker build -t pelikan-bot .
docker run -d --name pelikan-bot \
  -e BOT_TOKEN=your_token \
  -e ADMIN_IDS=123456789 \
  -p 8080:8080 \
  pelikan-bot
```

## 🔌 Доступ к webhook с сайта

### Вариант 1: Локальная сеть

Если сайт и бот в одной сети:
```javascript
const API_URL = 'http://192.168.1.100:8080/api/order';
```

### Вариант 2: Внешний IP

Если бот на VPS с внешним IP:
```javascript
const API_URL = 'http://123.45.67.89:8080/api/order';
```

**Важно:** Откройте порт 8080 в файрволе:
```bash
sudo ufw allow 8080/tcp
```

### Вариант 3: Nginx proxy (рекомендуется)

Если у вас есть Nginx на сервере:

```nginx
location /api/order {
    proxy_pass http://127.0.0.1:8080/api/order;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 📊 Мониторинг

```bash
# Проверка работы
curl http://localhost:8080/health

# Просмотр логов (systemd)
sudo journalctl -u pelikan-bot -f

# Просмотр логов (обычный запуск)
tail -f bot.log
```

## 🛠 Решение проблем

### Бот не запускается

```bash
# Проверьте токен
cat .env | grep BOT_TOKEN

# Проверьте зависимости
pip install -r requirements.txt

# Запустите с выводом ошибок
python bot.py
```

### Webhook не принимает заказы

```bash
# Проверьте, что порт открыт
sudo netstat -tulpn | grep 8080

# Проверьте файрвол
sudo ufw status

# Откройте порт
sudo ufw allow 8080/tcp
```

### База данных заблокирована

```bash
# Остановите бота
sudo systemctl stop pelikan-bot  # или Ctrl+C

# Подождите 5 секунд
sleep 5

# Запустите снова
sudo systemctl start pelikan-bot  # или python bot.py
```

## 🔄 Обновление

```bash
cd ~/telegram_bot_pelican_alacol
git pull
pip install -r requirements.txt
sudo systemctl restart pelikan-bot
```

## 📖 Документация

- 🚀 [Быстрый старт](docs/QUICKSTART.md)
- 🗄️ [SQL команды](docs/SQL_COMMANDS.md)
- 💻 [Интеграция с сайтом](examples/bar-integration.js)

## ❓ FAQ

**Q: Нужен ли мне домен?**  
A: Нет! Эта версия работает без домена через polling.

**Q: Нужен ли SSL сертификат?**  
A: Нет! Не требуется для polling версии.

**Q: Могу ли я запустить на домашнем компьютере?**  
A: Да! Просто запустите `python bot.py` и держите компьютер включенным.

**Q: Как подключить сайт к боту?**  
A: Укажите IP адрес вашего сервера в JavaScript: `http://your-ip:8080/api/order`

**Q: Как открыть доступ извне?**  
A: Откройте порт 8080 в настройках роутера (port forwarding) и файрволе.

## 📄 Лицензия

MIT License - подробности в [LICENSE](LICENSE)

## 📞 Поддержка

- 💬 Telegram: [@pelikan_support](https://t.me/pelikan_support)
- 📧 Email: support@pelikan-alakol.kz
- 🐙 GitHub: [Issues](https://github.com/yourusername/telegram_bot_pelikan_alacol/issues)

---

<p align="center">
  <b>Работает БЕЗ домена и SSL! 🎉</b><br>
  Сделано с ❤️ для бара "Пеликан Алаколь"
</p>
