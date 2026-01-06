# 📦 Инструкция по загрузке проекта на GitHub

## Шаг 1: Создание репозитория на GitHub

1. Перейдите на [github.com](https://github.com)
2. Нажмите кнопку "New repository" (или "+")
3. Заполните данные:
   - **Repository name:** `telegram_bot_pelican_alacol`
   - **Description:** `Telegram bot для системы заказов бара "Пеликан Алаколь"`
   - **Visibility:** Public или Private
   - ❌ НЕ добавляйте README, .gitignore, license (они уже есть в проекте)
4. Нажмите "Create repository"

## Шаг 2: Инициализация Git и загрузка проекта

### Вариант A: Через командную строку

```bash
# Перейдите в директорию проекта
cd telegram_bot_pelican_alacol

# Инициализируйте git репозиторий
git init

# Добавьте все файлы
git add .

# Создайте первый коммит
git commit -m "Initial commit: Telegram bot для бара Пеликан Алаколь"

# Добавьте удалённый репозиторий (замените yourusername на ваш username)
git remote add origin https://github.com/yourusername/telegram_bot_pelican_alacol.git

# Переименуйте ветку в main (если нужно)
git branch -M main

# Загрузите на GitHub
git push -u origin main
```

### Вариант B: Через GitHub Desktop

1. Откройте GitHub Desktop
2. File → Add Local Repository
3. Выберите папку `telegram_bot_pelican_alacol`
4. Создайте коммит с сообщением "Initial commit"
5. Publish repository на GitHub

## Шаг 3: Настройка репозитория на GitHub

### Добавление описания и тегов

1. Перейдите в настройки репозитория (Settings)
2. В разделе "About" добавьте:
   - **Description:** `Telegram bot для автоматизации заказов бара с веб-интеграцией`
   - **Website:** `https://pelikan-alakol.kz`
   - **Topics (tags):** 
     - `telegram-bot`
     - `aiogram`
     - `python`
     - `webhook`
     - `restaurant`
     - `order-management`
     - `sqlite`

### Защита основной ветки

1. Settings → Branches
2. Add branch protection rule
3. Branch name pattern: `main`
4. Включите:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging

### Настройка GitHub Actions (опционально)

Создайте файл `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest tests/
```

## Шаг 4: Создание Releases

1. Перейдите на вкладку "Releases"
2. Нажмите "Create a new release"
3. Заполните:
   - **Tag version:** `v1.0.0`
   - **Release title:** `v1.0.0 - Первый релиз`
   - **Description:** Скопируйте из CHANGELOG.md
4. Нажмите "Publish release"

## Шаг 5: Настройка Secrets для CI/CD

Если планируете автоматический деплой:

1. Settings → Secrets and variables → Actions
2. Добавьте secrets:
   - `BOT_TOKEN` - токен бота
   - `VPS_HOST` - IP адрес VPS
   - `VPS_USER` - пользователь VPS
   - `VPS_SSH_KEY` - приватный SSH ключ

## Шаг 6: Добавление README badges

Добавьте в начало README.md:

```markdown
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.15-green.svg)](https://docs.aiogram.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/release/yourusername/telegram_bot_pelikan_alacol.svg)](https://github.com/yourusername/telegram_bot_pelikan_alacol/releases)
```

## Шаг 7: Создание Issues templates

Создайте `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug report
about: Сообщить об ошибке
---

**Описание бага**
Краткое описание проблемы.

**Как воспроизвести**
1. Перейти в '...'
2. Нажать на '...'
3. Увидеть ошибку

**Ожидаемое поведение**
Что должно было произойти.

**Скриншоты**
Если применимо, добавьте скриншоты.

**Окружение:**
 - ОС: [например, Ubuntu 22.04]
 - Python версия: [например, 3.10]
 - Версия бота: [например, 1.0.0]
```

## Шаг 8: GitHub Pages для документации (опционально)

1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` / folder: `/docs`
4. Save

Документация будет доступна по адресу:
`https://yourusername.github.io/telegram_bot_pelikan_alacol/`

## Команды для работы с Git

### Базовые команды

```bash
# Проверить статус
git status

# Добавить изменения
git add .

# Создать коммит
git commit -m "Описание изменений"

# Загрузить на GitHub
git push

# Получить изменения с GitHub
git pull

# Создать новую ветку
git checkout -b feature/new-feature

# Переключиться на ветку
git checkout main

# Слить ветку
git merge feature/new-feature
```

### Работа с .env

**ВАЖНО!** Файл `.env` с реальными токенами НЕ должен попадать в Git!

Проверьте `.gitignore`:
```
.env
.env.local
*.db
```

## Webhook для автоматического деплоя

Создайте webhook на GitHub для автоматического деплоя при push:

1. Settings → Webhooks → Add webhook
2. **Payload URL:** `https://bar.pelikan-alakol.kz/api/github-webhook`
3. **Content type:** `application/json`
4. **Secret:** (ваш секретный ключ)
5. **Events:** Just the `push` event
6. **Active:** ✅

Добавьте обработчик в `webhook_server.py`:

```python
async def handle_github_webhook(request):
    # Валидация подписи
    signature = request.headers.get('X-Hub-Signature-256')
    # Запуск deploy.sh
    subprocess.run(['./scripts/deploy.sh'])
    return web.json_response({"status": "ok"})
```

## Структура коммитов

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: добавлена команда /orders для админов
fix: исправлена ошибка с подключением к БД
docs: обновлена документация установки
style: форматирование кода
refactor: рефакторинг webhook сервера
test: добавлены тесты для bot.py
chore: обновлены зависимости
```

## Checklist перед загрузкой

- [ ] Удалены реальные токены и пароли из кода
- [ ] .env файл добавлен в .gitignore
- [ ] Обновлён README с правильными ссылками
- [ ] Проверена работа всех скриптов
- [ ] Добавлена лицензия MIT
- [ ] Создан .gitignore
- [ ] Написаны комментарии в коде
- [ ] Документация актуальна
- [ ] Все файлы в правильной кодировке (UTF-8)

## Полезные ссылки

- [GitHub Docs](https://docs.github.com/)
- [Git Book](https://git-scm.com/book/ru/v2)
- [Markdown Guide](https://www.markdownguide.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Готово!** Теперь ваш проект на GitHub и готов к использованию! 🚀
