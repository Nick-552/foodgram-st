FROM python:3.9-slim

WORKDIR /app

# Устанавливаем netcat
RUN apt-get update && apt-get install -y \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

# Используем entrypoint.sh для запуска
ENTRYPOINT ["bash", "entrypoint.sh"] 