#!/bin/bash

# Скрипт для запуска ShortlyBot

set -e

echo "🚀 Запуск ShortlyBot..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Скопируйте env.example в .env и заполните TELEGRAM_BOT_TOKEN"
    exit 1
fi

# Запускаем сервисы
docker-compose up -d

echo "✅ ShortlyBot запущен!"
echo "📊 RabbitMQ Management UI: http://localhost:15672"
echo "👤 Логин: admin, Пароль: password123"
echo ""
echo "📋 Полезные команды:"
echo "  docker-compose logs -f bot     # Просмотр логов бота"
echo "  docker-compose logs -f rabbitmq # Просмотр логов RabbitMQ"
echo "  docker-compose down            # Остановка сервисов"
echo "  docker-compose restart bot     # Перезапуск бота"
