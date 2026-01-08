# 🏨 Pelikan Alakol Hotel Bot

[![Docker](https://img.shields.io/docker/v/andreyhiitola/pelikan-bot?label=Docker&logo=docker)](https://hub.docker.com/r/andreyhiitola/pelikan-bot)
Telegram бот для отеля "Пеликан Алаколь"

## 🤖 Бот

[@Pelican_alacol_hotel_bot](https://t.me/Pelican_alacol_hotel_bot)

## 🚀 Быстрый старт

### Локально (Docker)
```bash
# Клонировать
git clone https://github.com/Andreyhiitola/pelikan-bot.git
cd pelikan-bot

# Настроить .env
cp .env.example .env
nano .env  # BOT_TOKEN и ADMIN_IDS

# Запустить
docker-compose up -d

# Логи
docker-compose logs -f bot
```

### На VPS
```bash
# 1. Установить Docker
curl -fsSL https://get.docker.com | sh

# 2. Клонировать
git clone https://github.com/Andreyhiitola/pelikan-bot.git
cd pelikan-bot

# 3. Настроить .env
nano .env

# 4. Запустить
docker-compose up -d

# ✅ Автообновление работает через Watchtower!
```

## ✨ Команды

**Гости:**
- `/bar` - Меню бара
- `/stolovaya` - Меню столовой
- `/booking` - Бронирование
- `/transfer` - Трансфер
- `/activities` - Экскурсии
- `/info` - Информация

**Админы:**
- `/orders` - Активные заказы
- `/stats` - Статистика
- `/update <id> <статус>` - Изменить статус

## 🛠️ Технологии

- Python 3.11
- aiogram 3.7+
- Docker + Watchtower
- SQLite

## 🔄 Автообновление

`git push` → GitHub Actions → Docker Hub → Watchtower → Обновлён!

## 📞 Контакты

- Website: https://pelikan-alakol.kz
- GitHub: [@Andreyhiitola](https://github.com/Andreyhiitola)
