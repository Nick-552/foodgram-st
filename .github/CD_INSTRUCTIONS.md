# Инструкция по настройке непрерывной доставки (CD)

## Подготовка сервера

1. Установите Docker и Docker Compose:
   ```bash
   # Обновите пакеты
   sudo apt update
   
   # Установите необходимые зависимости
   sudo apt install -y curl gnupg2 software-properties-common apt-transport-https ca-certificates
   
   # Добавьте Docker GPG ключ
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
   
   # Добавьте репозиторий Docker
   sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
   
   # Обновите индекс пакетов
   sudo apt update
   
   # Установите Docker
   sudo apt install -y docker-ce
   
   # Установите Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.15.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. Создайте директорию для проекта:
   ```bash
   mkdir -p ~/foodgram/infra
   ```

3. Создайте пользователя для работы с GitHub Actions (необязательно):
   ```bash
   sudo adduser github
   sudo usermod -aG docker github
   sudo usermod -aG sudo github
   ```

## Настройка SSH доступа

1. Создайте SSH ключ на локальной машине:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com" -f ~/.ssh/foodgram_deploy
   ```

2. Добавьте публичный ключ на сервер:
   ```bash
   ssh-copy-id -i ~/.ssh/foodgram_deploy.pub user@your_server_ip
   ```

3. Проверьте подключение:
   ```bash
   ssh -i ~/.ssh/foodgram_deploy user@your_server_ip
   ```

## Добавление секретов в GitHub

1. Скопируйте содержимое приватного ключа:
   ```bash
   cat ~/.ssh/foodgram_deploy
   ```

2. Добавьте все необходимые секреты в GitHub, как описано в [SECRETS.md](SECRETS.md).

## Подготовка конфигурационных файлов

1. Скопируйте nginx.conf на сервер:
   ```bash
   scp -i ~/.ssh/foodgram_deploy infra/nginx.conf user@your_server_ip:~/foodgram/infra/
   ```

## Первый деплой

Первый деплой можно выполнить вручную, чтобы убедиться, что все работает:

1. Клонируйте репозиторий на сервер:
   ```bash
   ssh -i ~/.ssh/foodgram_deploy user@your_server_ip
   cd ~/foodgram
   git clone https://github.com/yourusername/foodgram-st.git .
   ```

2. Создайте файл .env:
   ```bash
   cd ~/foodgram/infra
   touch .env
   nano .env
   ```
   
   Добавьте в файл следующие переменные:
   ```
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=foodgram
   POSTGRES_USER=foodgram_user
   POSTGRES_PASSWORD=your_password
   DB_HOST=db
   DB_PORT=5432
   ```

3. Запустите проект:
   ```bash
   cd ~/foodgram/infra
   docker-compose up -d
   ```

4. Если все настроено правильно, то при следующем пуше в ветку main/master GitHub Actions автоматически выполнит деплой на сервер.

## Проверка работы CI/CD

1. Внесите какие-либо изменения в код
2. Отправьте изменения в репозиторий:
   ```bash
   git add .
   git commit -m "Test CI/CD"
   git push origin main
   ```
3. Проверьте вкладку Actions в GitHub репозитории
4. Убедитесь, что все шаги выполнились успешно и изменения были доставлены на сервер 