# RabbitMQ Setup для ShortlyBot

## Быстрый старт

### Запуск RabbitMQ
```bash
docker-compose up -d
```

### Остановка RabbitMQ
```bash
docker-compose down
```

### Просмотр логов
```bash
docker-compose logs -f rabbitmq
```

## Доступ к RabbitMQ

### AMQP порт
- **Порт**: 5672
- **Хост**: localhost
- **Пользователь**: admin
- **Пароль**: password123

### Веб-интерфейс управления
- **URL**: http://localhost:15672
- **Логин**: admin
- **Пароль**: password123

## Переменные окружения

Добавьте в ваш `.env` файл:
```env
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=password123
RABBITMQ_VHOST=/
```

## Полезные команды

### Проверка статуса
```bash
docker-compose ps
```

### Перезапуск
```bash
docker-compose restart rabbitmq
```

### Очистка данных (осторожно!)
```bash
docker-compose down -v
```

## Мониторинг

Веб-интерфейс предоставляет:
- Статистику очередей
- Мониторинг соединений
- Управление пользователями
- Просмотр сообщений
- Настройки виртуальных хостов
