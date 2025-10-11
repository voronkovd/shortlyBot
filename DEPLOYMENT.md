# 🚀 Руководство по развертыванию ShortlyBot

## 📋 Быстрый старт

### 1. Подготовка окружения
```bash
# Клонирование репозитория
git clone <repository-url>
cd shortlyBot

# Создание .env файла
cp env.example .env
# Отредактируйте .env и добавьте ваш TELEGRAM_BOT_TOKEN
```

### 2. Запуск с Docker
```bash
# Сборка и запуск
docker-compose up -d --build

# Проверка статуса
docker-compose ps
```

### 3. Проверка работы
- **RabbitMQ Management UI**: http://localhost:15672 (admin/password123)
- **Логи бота**: `docker-compose logs -f bot`
- **Статистика**: просматривайте в RabbitMQ UI

## 🐳 Docker конфигурация

### Основные сервисы
- **bot**: Telegram бот (порт не экспонируется)
- **rabbitmq**: Message broker (порты 5672, 15672)

### Переменные окружения
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=password123
RABBITMQ_VHOST=/
```

## 🔧 Управление сервисами

### Основные команды
```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск бота
docker-compose restart bot

# Просмотр логов
docker-compose logs -f bot
docker-compose logs -f rabbitmq

# Статус сервисов
docker-compose ps
```

### Скрипты автоматизации
```bash
# Сборка образа
./scripts/build.sh

# Запуск сервисов
./scripts/start.sh

# Остановка сервисов
./scripts/stop.sh

# Режим разработки (только RabbitMQ)
./scripts/dev.sh
```

## 📊 Мониторинг

### Health Checks
```bash
# Проверка бота
docker-compose exec bot python -c "import requests; print('Bot is healthy')"

# Проверка RabbitMQ
docker-compose exec rabbitmq rabbitmq-diagnostics ping
```

### Логи и отладка
```bash
# Логи в реальном времени
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f bot
docker-compose logs -f rabbitmq

# Вход в контейнер бота
docker-compose exec bot bash
```

## 🔒 Безопасность

### Рекомендации для продакшена
1. **Измените пароли RabbitMQ**:
   ```env
   RABBITMQ_DEFAULT_PASS=your_secure_password
   ```

2. **Используйте секреты Docker**:
   ```bash
   echo "your_bot_token" | docker secret create telegram_bot_token -
   ```

3. **Ограничьте сетевой доступ**:
   - Уберите порты RabbitMQ из внешнего доступа
   - Используйте reverse proxy для веб-интерфейса

4. **Регулярные обновления**:
   ```bash
   docker-compose pull
   docker-compose up -d --build
   ```

## 📈 Масштабирование

### Горизонтальное масштабирование
```yaml
# docker-compose.override.yml
services:
  bot:
    deploy:
      replicas: 3
```

### Мониторинг ресурсов
```bash
# Использование ресурсов
docker stats

# Мониторинг очередей RabbitMQ
# Используйте веб-интерфейс: http://localhost:15672
```

## 🛠️ Разработка

### Локальная разработка
```bash
# Запуск только RabbitMQ
./scripts/dev.sh

# Запуск бота локально
source venv/bin/activate
python main.py
```

### Тестирование
```bash
# Запуск тестов
python -m pytest tests/ -v

# Тесты с покрытием
python -m pytest tests/ --cov=providers --cov=analytics --cov=handlers --cov=commands
```

## 🚨 Устранение неполадок

### Частые проблемы

#### Бот не запускается
```bash
# Проверьте токен
docker-compose logs bot

# Проверьте подключение к RabbitMQ
docker-compose exec bot python -c "import pika; print('RabbitMQ connection OK')"
```

#### RabbitMQ недоступен
```bash
# Перезапуск RabbitMQ
docker-compose restart rabbitmq

# Проверка статуса
docker-compose exec rabbitmq rabbitmq-diagnostics status
```

#### Проблемы с сетью
```bash
# Пересоздание сети
docker-compose down
docker network prune
docker-compose up -d
```

### Логи и диагностика
```bash
# Подробные логи
docker-compose logs --tail=100 bot

# Системные ресурсы
docker system df
docker system prune  # Очистка неиспользуемых ресурсов
```

## 📚 Дополнительные ресурсы

- [Docker Compose документация](https://docs.docker.com/compose/)
- [RabbitMQ Management UI](https://www.rabbitmq.com/management.html)
- [Python Telegram Bot](https://python-telegram-bot.readthedocs.io/)
- [yt-dlp документация](https://github.com/yt-dlp/yt-dlp)
