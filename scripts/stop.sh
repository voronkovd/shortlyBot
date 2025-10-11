#!/bin/bash

# Скрипт для остановки ShortlyBot

set -e

echo "🛑 Остановка ShortlyBot..."

# Останавливаем сервисы
docker-compose down

echo "✅ ShortlyBot остановлен!"
echo ""
echo "💡 Для полной очистки (включая данные):"
echo "  docker-compose down -v"
