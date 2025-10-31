# Используем официальный образ PostgreSQL
FROM postgres:16-alpine

# Устанавливаем переменные окружения
ENV POSTGRES_DB=mydatabase
ENV POSTGRES_USER=myuser
ENV POSTGRES_PASSWORD=mypassword

# Копируем SQL скрипты для инициализации (если нужны)
#COPY init-scripts/ /docker-entrypoint-initdb.d/

# Создаем директорию для данных (опционально)
RUN mkdir -p /var/lib/postgresql/data

# Открываем порт PostgreSQL
EXPOSE 5432

# Команда запуска (уже определена в базовом образе)
CMD ["postgres"]