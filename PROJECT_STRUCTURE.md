# 📁 Структура проекта
```
pelikan-hotel-bot/
├── .github/
│   └── workflows/
│       └── docker-publish.yml    # GitHub Actions для CI/CD
│
├── bot.py                         # Основной код бота
├── requirements.txt               # Python зависимости
│
├── Dockerfile                     # Docker образ
├── docker-compose.yml             # Docker Compose + Watchtower
├── .dockerignore                  # Исключения для Docker
│
├── .env.example                   # Шаблон переменных окружения
├── .gitignore                     # Git исключения
│
├── README.md                      # Главная документация
├── ROADMAP.md                     # План развития
├── GITHUB_SETUP.md                # Настройка GitHub Secrets
├── DEPLOYMENT_CHECKLIST.md        # Чеклист развёртывания
│
└── LICENSE                        # Лицензия

# Не в Git (создаются локально):
├── .env                           # Реальные переменные (не коммитится)
├── data/                          # База данных (volume)
│   └── orders.db
```

## Файлы

**Основные:**
- `bot.py` - код Telegram бота
- `requirements.txt` - Python зависимости

**Docker:**
- `Dockerfile` - образ для бота
- `docker-compose.yml` - оркестрация (бот + watchtower)
- `.dockerignore` - исключения при сборке

**Конфигурация:**
- `.env.example` - шаблон переменных
- `.gitignore` - исключения для Git

**Документация:**
- `README.md` - главная документация
- `ROADMAP.md` - план развития
- `GITHUB_SETUP.md` - настройка CI/CD
- `DEPLOYMENT_CHECKLIST.md` - чеклист для деплоя

**CI/CD:**
- `.github/workflows/docker-publish.yml` - автосборка

## Команды
```bash
# Локальная разработка
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py

# Docker локально
docker-compose up -d
docker-compose logs -f

# VPS развёртывание
git clone https://github.com/Andreyhiitola/pelikan-bot.git
cd pelikan-bot
nano .env  # Настроить
docker-compose up -d
```
