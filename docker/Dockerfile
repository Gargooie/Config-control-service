FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя приложения
RUN useradd --create-home --shell /bin/bash app

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY config_service ./config_service

# Устанавливаем права
RUN chown -R app:app /app
USER app

# Открываем порт
EXPOSE 8080

# Запускаем приложение
CMD ["python", "-m", "config_service.app"]
