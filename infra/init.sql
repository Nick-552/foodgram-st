-- Создаем пользователя
CREATE USER foodgram_user WITH PASSWORD '12345678';

-- Создаем базу данных
CREATE DATABASE foodgram;

-- Даем права на базу данных
GRANT ALL PRIVILEGES ON DATABASE foodgram TO foodgram_user;

-- Подключаемся к базе данных
\c foodgram

-- Даем права на схему public
GRANT ALL ON SCHEMA public TO foodgram_user;

-- Даем права на все таблицы
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO foodgram_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO foodgram_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO foodgram_user; 