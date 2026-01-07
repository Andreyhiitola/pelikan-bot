# 🔐 Настройка GitHub Secrets

## Зачем это нужно?

**GitHub Actions будет автоматически:**
1. При `git push` в main
2. Собирать Docker образ
3. Пушить на Docker Hub
4. Watchtower на VPS подхватит обновление

**Workflow:**
```
Локально → git push → 
GitHub Actions → Docker Hub → 
Watchtower (VPS) → Бот обновлён!
```

---

## Шаг 1: Создать Docker Hub аккаунт

### 1.1 Регистрация (если нет аккаунта)

**Зайти на:** https://hub.docker.com/signup

**Заполнить:**
- Docker ID: `andreyhiitola` (или ваш username)
- Email: ваш email
- Password: надёжный пароль

**Подтвердить email**

### 1.2 Создать Access Token

**После входа:**

1. Нажать на аватар → **Account Settings**
2. Слева выбрать **Security**
3. Кнопка **New Access Token**

**Заполнить:**
- Access Token Description: `github-actions-pelikan-bot`
- Access permissions: **Read, Write, Delete**

4. Нажать **Generate**
5. **СКОПИРОВАТЬ ТОКЕН!** (показывается один раз)
```
Пример токена:
dckr_pat_AbCdEf1234567890XyZ...
```

⚠️ **ВАЖНО:** Сохраните токен! Он больше не покажется!

---

## Шаг 2: Добавить Secrets в GitHub

### 2.1 Открыть настройки репозитория

**Перейти:**
```
https://github.com/Andreyhiitola/pelikan-bot/settings/secrets/actions
```

**Или вручную:**
1. GitHub → ваш репозиторий `pelikan-bot`
2. Settings (вверху справа)
3. Слева: Secrets and variables → Actions
4. Вкладка: **Secrets**

### 2.2 Добавить DOCKERHUB_USERNAME

1. Кнопка **New repository secret**
2. **Name:** `DOCKERHUB_USERNAME`
3. **Secret:** `andreyhiitola` (ваш Docker Hub username)
4. **Add secret**

### 2.3 Добавить DOCKERHUB_TOKEN

1. Кнопка **New repository secret**
2. **Name:** `DOCKERHUB_TOKEN`
3. **Secret:** вставить скопированный токен
```
   dckr_pat_AbCdEf1234567890XyZ...
```
4. **Add secret**

---

## Шаг 3: Проверка Secrets

**Должно быть 2 секрета:**

| Name | Value (скрыто) |
|------|----------------|
| DOCKERHUB_USERNAME | ••••••••••••• |
| DOCKERHUB_TOKEN | ••••••••••••• |

✅ **Secrets настроены!**

---

## Шаг 4: Проверить GitHub Actions workflow

**Файл уже создан:** `.github/workflows/docker-publish.yml`

**Проверить его наличие:**
```bash
cat .github/workflows/docker-publish.yml
```

**Должен содержать:**
```yaml
env:
  REGISTRY: docker.io
  IMAGE_NAME: andreyhiitola/pelikan-bot

jobs:
  build-and-push:
    steps:
      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
```

---

## Шаг 5: Протестировать автосборку

### 5.1 Сделать тестовый коммит
```bash
cd ~/Desktop/pelikan-hotel-bot

# Создать тестовый файл
echo "# Test CI/CD" >> TEST.md

# Коммит
git add TEST.md
git commit -m "test: Trigger Docker build"

# Push
git push origin main
```

### 5.2 Проверить GitHub Actions

**Открыть:**
```
https://github.com/Andreyhiitola/pelikan-bot/actions
```

**Должен запуститься workflow:**
- 🟡 Жёлтый кружок = строится
- 🟢 Зелёная галочка = успех!
- 🔴 Красный крестик = ошибка

**Кликнуть на workflow → посмотреть логи**

### 5.3 Проверить Docker Hub

**Открыть:**
```
https://hub.docker.com/r/andreyhiitola/pelikan-bot/tags
```

**Должен появиться образ:**
- Tag: `latest`
- Pushed: несколько секунд/минут назад

✅ **Автосборка работает!**

---

## Что происходит при push?
```
1. Вы: git push origin main
   ↓
2. GitHub: Обнаружил push
   ↓
3. GitHub Actions: Запустил workflow
   ├─ Checkout кода
   ├─ Setup Docker Buildx
   ├─ Login в Docker Hub (используя secrets)
   ├─ Build образа
   └─ Push на Docker Hub
   ↓
4. Docker Hub: Образ загружен
   Tag: andreyhiitola/pelikan-bot:latest
   ↓
5. Watchtower на VPS (каждые 5 минут):
   ├─ Проверяет Docker Hub
   ├─ Обнаружил новый образ
   ├─ Скачал
   ├─ Остановил старый контейнер
   ├─ Запустил новый
   └─ Удалил старый образ
   ↓
6. Бот обновлён! 🎉
```

---

## Troubleshooting

### ❌ Ошибка: "Error: Username and password required"

**Причина:** Secrets не настроены или неправильно названы

**Решение:**
1. Проверить что есть оба секрета
2. Названия точно: `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN`
3. Значения корректны

### ❌ Ошибка: "denied: requested access to the resource is denied"

**Причина:** Неправильный токен или недостаточно прав

**Решение:**
1. Создать новый Access Token
2. Права: Read, Write, Delete
3. Обновить `DOCKERHUB_TOKEN` в Secrets

### ❌ Ошибка: "repository does not exist"

**Причина:** Образ с таким именем не существует на Docker Hub

**Решение:**
1. Docker Hub → Create Repository
2. Name: `pelikan-bot`
3. Visibility: Public
4. Create

### ⚠️ Workflow не запускается

**Причина:** Неправильный путь к workflow файлу

**Проверить:**
```bash
ls -la .github/workflows/
# Должен быть: docker-publish.yml
```

### 🐌 Сборка долгая (5-10 минут)

**Это нормально при первой сборке!**
- Скачиваются все слои
- Устанавливаются зависимости
- Следующие сборки будут быстрее (кэш)

---

## Полезные команды

### Проверить статус Actions
```bash
# В браузере
https://github.com/Andreyhiitola/pelikan-bot/actions

# Или через GitHub CLI
gh run list
gh run view <run-id>
```

### Посмотреть образы на Docker Hub
```bash
# В браузере
https://hub.docker.com/r/andreyhiitola/pelikan-bot

# Или через CLI
docker search andreyhiitola/pelikan-bot
```

### Проверить что Watchtower работает
```bash
# На VPS
docker-compose logs watchtower

# Должно быть примерно:
# time="..." level=info msg="Checking for updates"
# time="..." level=info msg="Found new image"
# time="..." level=info msg="Stopping container"
# time="..." level=info msg="Starting container"
```

---

## Итого - что настроили

✅ Docker Hub аккаунт
✅ Access Token создан
✅ GitHub Secrets добавлены
✅ GitHub Actions workflow работает
✅ Автосборка при push
✅ Автодеплой через Watchtower

**Результат:**
```
git push → 5 минут → бот обновлён на VPS!
```

Без SSH, без ручного деплоя, полностью автоматически! 🚀
