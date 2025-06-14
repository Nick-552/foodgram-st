#!/bin/bash

echo "Waiting for database..."
python db_check.py

echo "Making migrations..."
python manage.py makemigrations api

echo "Applying migrations..."
python manage.py migrate

echo "Creating superuser..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com

echo "Loading ingredients..."
python manage.py load_ingredients

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 