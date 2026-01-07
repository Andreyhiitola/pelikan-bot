# ✅ Чеклист настройки Secrets

## 1. Docker Hub

- [ ] Зайти на https://hub.docker.com
- [ ] Зарегистрироваться (если нет аккаунта)
- [ ] Подтвердить email
- [ ] Account Settings → Security → New Access Token
- [ ] Name: `github-actions-pelikan-bot`
- [ ] Permissions: Read, Write, Delete
- [ ] Generate → СКОПИРОВАТЬ ТОКЕН
- [ ] Сохранить токен в безопасное место

## 2. GitHub Secrets

- [ ] Открыть https://github.com/Andreyhiitola/pelikan-bot/settings/secrets/actions
- [ ] New repository secret
  - [ ] Name: `DOCKERHUB_USERNAME`
  - [ ] Value: `andreyhiitola`
- [ ] New repository secret
  - [ ] Name: `DOCKERHUB_TOKEN`
  - [ ] Value: (вставить токен)

## 3. Проверка

- [ ] Secrets отображаются в списке (2 штуки)
- [ ] Сделать тестовый коммит
- [ ] Push в main
- [ ] Открыть https://github.com/Andreyhiitola/pelikan-bot/actions
- [ ] Проверить что workflow запустился
- [ ] Дождаться зелёной галочки
- [ ] Открыть https://hub.docker.com/r/andreyhiitola/pelikan-bot/tags
- [ ] Проверить что образ появился

✅ Всё работает!
