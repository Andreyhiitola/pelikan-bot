# ✅ Deployment Checklist

## Локальная подготовка

- [x] Dockerfile создан
- [x] docker-compose.yml создан
- [x] .dockerignore настроен
- [x] GitHub Actions workflow создан
- [x] README.md обновлён
- [ ] .env файл настроен локально
- [ ] Локальное тестирование: `docker-compose up`
- [ ] Проверка логов: `docker-compose logs -f`

## GitHub

- [ ] Код запушен в main
- [ ] Docker Hub аккаунт создан
- [ ] GitHub Secrets добавлены:
  - [ ] DOCKERHUB_USERNAME
  - [ ] DOCKERHUB_TOKEN
- [ ] GitHub Actions запустился успешно
- [ ] Образ появился на Docker Hub

## VPS

- [ ] VPS получен
- [ ] Docker установлен
- [ ] .env файл создан на VPS
- [ ] docker-compose.yml загружен
- [ ] `docker-compose up -d` выполнен
- [ ] Бот отправил уведомление админам
- [ ] Watchtower работает: `docker logs watchtower`

## Тестирование

- [ ] `/start` работает
- [ ] `/bar` показывает меню
- [ ] Тестовый заказ создаётся
- [ ] Админы получают уведомления
- [ ] `/orders` показывает заказы
- [ ] Автообновление работает (тест: изменить код → push → ждать 5 мин)

## Документация

- [x] README.md
- [x] DOCKER_DEPLOY.md
- [x] GITHUB_SETUP.md
- [x] DEPLOYMENT_CHECKLIST.md
