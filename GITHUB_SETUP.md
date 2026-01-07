# 🔐 Настройка GitHub Secrets для Docker Hub

## Шаги:

1. **Создать Docker Hub аккаунт** (если нет)
   - Зайти на https://hub.docker.com
   - Sign Up

2. **Создать Access Token**
   - Account Settings → Security → New Access Token
   - Name: `github-actions`
   - Permissions: Read, Write, Delete
   - Copy token (показывается один раз!)

3. **Добавить в GitHub Secrets**
   - Открыть https://github.com/Andreyhiitola/pelikan-bot/settings/secrets/actions
   - New repository secret:
     - Name: `DOCKERHUB_USERNAME`
     - Value: `andreyhiitola`
   - New repository secret:
     - Name: `DOCKERHUB_TOKEN`
     - Value: `<ваш_токен>`

4. **Проверка**
   - Сделать commit и push
   - Открыть Actions tab
   - Должна запуститься сборка
   - После успеха → образ на hub.docker.com/r/andreyhiitola/pelikan-bot
