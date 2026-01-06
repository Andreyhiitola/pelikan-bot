# 🚀 Быстрый старт (Polling версия - БЕЗ домена!)

## Получение токена бота (2 минуты)

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота: `Пеликан Алаколь Бар`
   - Введите username: `pelikan_alakol_bot` (или другое доступное)
4. **Скопируйте токен** (формат: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Получение вашего Telegram ID (1 минута)

1. Откройте бота [@userinfobot](https://t.me/userinfobot)
2. Нажмите `/start`
3. Скопируйте ваш ID (число, например: `123456789`)

## Установка и запуск

### Вариант 1: Локально на компьютере (для теста)

**Windows:**
```powershell
# Скачайте и распакуйте проект
cd telegram_bot_pelican_alacol

# Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt

# Настройте конфигурацию
copy .env.example .env
notepad .env
# Укажите BOT_TOKEN и ADMIN_IDS

# Запустите бота
python bot.py
```

**Linux/macOS:**
```bash
cd telegram_bot_pelican_alacol

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
nano .env
# Укажите BOT_TOKEN и ADMIN_IDS

python bot.py
```

### Вариант 2: На VPS (автоматическая установка)

```bash
# 1. Подключитесь к VPS
ssh user@your-server-ip

# 2. Клонируйте репозиторий
git clone https://github.com/yourusername/telegram_bot_pelikan_alacol.git
cd telegram_bot_pelican_alacol

# 3. Запустите автоустановку
chmod +x scripts/install.sh
./scripts/install.sh

# Во время установки укажите:
# BOT_TOKEN=ваш_токен_от_botfather
# ADMIN_IDS=ваш_telegram_id
```

## Проверка работы

```bash
# Проверьте статус
sudo systemctl status pelikan-bot

# Посмотрите логи
sudo journalctl -u pelikan-bot -f

# Проверьте webhook endpoint
curl http://localhost:8080/health
```

## Интеграция с сайтом

Бот автоматически запускает встроенный webhook сервер на порту 8080.

### На вашем сайте используйте:

```javascript
// Для локальной разработки
const API_URL = 'http://localhost:8080/api/order';

// Для production (замените на IP вашего VPS)
const API_URL = 'http://123.45.67.89:8080/api/order';
```

### Откройте порт в файрволе:

```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

**Полный пример интеграции:** [examples/bar-integration.js](../examples/bar-integration.js)

## Тестирование

1. **Напишите боту в Telegram:**
   ```
   /start
   ```

2. **Отправьте тестовый заказ с сайта:**
   ```bash
   curl -X POST http://localhost:8080/api/order \
     -H "Content-Type: application/json" \
     -d '{
       "orderId": "test123",
       "name": "Тестовый пользователь",
       "room": "101",
       "telegram": "testuser",
       "items": [{"name": "Тестовое блюдо", "price": 1000, "quantity": 1}],
       "total": 1000,
       "timestamp": "2026-01-06 15:30"
     }'
   ```

3. **Проверьте, что:**
   - Бот прислал уведомление в Telegram
   - Заказ сохранился в БД
   - Webhook работает

## Обновление бота

```bash
cd ~/pelikan-bar-bot
./deploy.sh
```

## Команды управления

```bash
# Перезапуск
sudo systemctl restart pelikan-bot
sudo systemctl restart pelikan-webhook

# Остановка
sudo systemctl stop pelikan-bot
sudo systemctl stop pelikan-webhook

# Логи в реальном времени
sudo journalctl -u pelikan-bot -f

# Последние 100 строк логов
sudo journalctl -u pelikan-bot -n 100
```

## Что дальше?

1. ✅ Интегрируйте с сайтом (см. `bar-integration.js`)
2. ✅ Добавьте других администраторов в `ADMIN_IDS`
3. ✅ Настройте резервное копирование БД
4. ✅ Протестируйте все функции

## Частые проблемы

### Бот не отвечает
```bash
# Проверьте токен в .env
cat .env | grep BOT_TOKEN

# Перезапустите бота
sudo systemctl restart pelikan-bot

# Проверьте логи
sudo journalctl -u pelikan-bot -n 50
```

### Webhook не работает
```bash
# Проверьте, запущен ли сервер
sudo systemctl status pelikan-webhook

# Проверьте порт
curl http://localhost:8080/health

# Проверьте логи
sudo journalctl -u pelikan-webhook -f
```

### База данных заблокирована
```bash
# Остановите оба сервиса
sudo systemctl stop pelikan-bot pelikan-webhook

# Подождите 5 секунд
sleep 5

# Запустите снова
sudo systemctl start pelikan-bot pelikan-webhook
```

## Поддержка

📧 Email: support@pelikan-alakol.kz  
💬 Telegram: @pelikan_support  
🐙 GitHub: https://github.com/yourusername/pelikan-bar-bot/issues
