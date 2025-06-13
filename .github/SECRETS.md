# Секреты для GitHub Actions

Для успешной работы CI/CD pipeline необходимо добавить следующие секреты в настройках репозитория GitHub (Settings -> Secrets and variables -> Actions -> New repository secret):

## Для сборки и публикации образов Docker

- `DOCKER_USERNAME` - логин от Docker Hub
- `DOCKER_PASSWORD` - пароль или токен от Docker Hub

## Для деплоя на сервер

- `HOST` - IP-адрес сервера
- `USER` - имя пользователя на сервере
- `SSH_KEY` - приватный SSH-ключ для доступа к серверу
- `PASSPHRASE` - пароль от SSH-ключа (если есть)

## Переменные окружения для базы данных

- `DB_ENGINE` - движок БД (например, django.db.backends.postgresql)
- `DB_NAME` - имя базы данных (например, foodgram)
- `POSTGRES_USER` - имя пользователя PostgreSQL
- `POSTGRES_PASSWORD` - пароль пользователя PostgreSQL
- `DB_HOST` - хост для подключения к БД (например, db)
- `DB_PORT` - порт для подключения к БД (например, 5432)

## Инструкция по добавлению секретов

1. Перейдите в настройки репозитория на GitHub
2. Выберите "Settings" -> "Secrets and variables" -> "Actions"
3. Нажмите "New repository secret"
4. Введите имя секрета и его значение
5. Нажмите "Add secret"

## Подготовка сервера для деплоя

На сервере должны быть установлены:
- Docker
- Docker Compose

Также нужно создать директорию для проекта:
```bash
mkdir -p ~/foodgram/infra
```

Предварительно скопируйте файлы nginx.conf в директорию ~/foodgram/infra для успешного деплоя. 