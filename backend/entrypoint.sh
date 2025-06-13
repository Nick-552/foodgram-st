#!/bin/bash

# Ждем доступности базы данных
echo "Waiting for database..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if nc -z db 5432; then
        echo "Database is ready!"
        break
    fi
    echo "Attempt $attempt of $max_attempts: Database is not ready yet..."
    attempt=$((attempt + 1))
    sleep 2
done

if [ $attempt -gt $max_attempts ]; then
    echo "Database is not available after $max_attempts attempts. Exiting..."
    exit 1
fi

# Применяем миграции
echo "Applying migrations..."
python manage.py migrate

# Отключаем очистку базы данных для сохранения данных
echo "Skipping database flush to preserve data..."
# python manage.py flush --no-input

# Создаем суперпользователя
echo "Creating superuser..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com

# Загружаем ингредиенты
echo "Loading ingredients..."
python manage.py load_ingredients

# Собираем статические файлы
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Запускаем gunicorn
echo "Starting gunicorn..."
gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 