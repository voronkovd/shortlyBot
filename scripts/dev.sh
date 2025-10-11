#!/bin/bash

# Скрипт для запуска только RabbitMQ в режиме разработки

set -e

echo "🔧 Запуск RabbitMQ для разработки..."

# Запускаем только RabbitMQ
docker-compose -f docker-compose.dev.yml up -d

echo "✅ RabbitMQ запущен для разработки!"
echo "📊 RabbitMQ Management UI: http://localhost:15672"
echo "👤 Логин: admin, Пароль: password123"
echo ""
echo "🐍 Теперь можете запустить бота локально:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "📋 Полезные команды:"
echo "  docker-compose -f docker-compose.dev.yml logs -f rabbitmq"
echo "  docker-compose -f docker-compose.dev.yml down"
