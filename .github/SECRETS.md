# Секреты для GitHub Actions

Для успешной работы CI/CD pipeline необходимо добавить следующие секреты в настройках репозитория GitHub (Settings -> Secrets and variables -> Actions -> New repository secret):

## Для сборки и публикации образов Docker

- `DOCKER_USERNAME` - логин от Docker Hub
- `DOCKER_PASSWORD` - пароль или токен от Docker Hub
