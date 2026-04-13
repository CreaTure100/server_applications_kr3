# Серверные приложения на FastAPI

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:
	``` pip install -r requirements.txt ```

## Запуск

Каждое приложение запускается из своей папки
``` uvicorn main:app --reload --port 8000 ```

## Тесты

### Задание 6.1

Правильные данные
``` curl -u admin:secret123 http://localhost:8000/secret ```

Неправильные данные
``` curl -u admin:wrongpass http://localhost:8000/secret ```

### Задание 6.2

Регистрация
```
  curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "qwerty123"}'
```

Логин
``` curl -u alice:qwerty123 http://localhost:8000/login ```

### Задание 6.3

Создайте свой .env
```
MODE=DEV
DOCS_USER=user
DOCS_PASSWORD=123
```

DEV режим - доступ к документации с паролем
``` curl -u admin:secret123 http://localhost:8000/docs ```

PROD режим - измените MODE=PROD в .env и перезапустите
``` curl http://localhost:8000/docs ```

### Задание 6.4

Регистрация
```
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "qwerty123"}'
```

Логин (получить токен)
```
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "qwerty123"}'
```

Доступ к защищенному ресурсу (подставьте реальный токен)
```
curl -X GET http://localhost:8000/protected_resource \
  -H "Authorization: Bearer <your_token>"
```

### Задание 6.5

Регистрация (1 запрос в минуту)
```
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "qwerty123"}'
```

Быстрый повторный запрос вернёт 429 Too Many Requests

Логин (5 запросов в минуту)
Быстро выполните 5 раз запрос 

```
curl -X POST http://localhost:8000/login \
    -H "Content-Type: application/json" \
    -d '{"username": "alice", "password": "qwerty123"}'
```

6-й запрос вернёт 429

### Задание 7.1

Создание пользователей с разными ролями
```
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin1", "password": "admin123", "role": "admin"}'

curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "user123", "role": "user"}'

curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "guest1", "password": "guest123", "role": "guest"}'
```

Логин и получение токенов
```
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin1", "password": "admin123"}'
```

Доступ к admin_resource (только admin)
```
curl -X POST http://localhost:8000/admin_resource \
  -H "Authorization: Bearer <admin_token>"
```

Доступ к protected_resource (admin и user)
```
curl -X GET http://localhost:8000/protected_resource \
  -H "Authorization: Bearer <user_token>"
```

Гость не имеет доступа к protected_resource
```
curl -X GET http://localhost:8000/protected_resource \
  -H "Authorization: Bearer <guest_token>"
```

Вернёт 403 Forbidden


### Задание 8.1

Создание таблицы (один раз)
``` python create_db.py ```

Регистрация
```
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "password": "12345"}'
```

Повторная регистрация (ошибка)
```
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "password": "67890"}'
```

### Задание 8.2

Создание таблицы (один раз)
``` python create_db.py ```

CREATE - создание Todo
```
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs, bread"}'
```

READ - получение Todo по id
``` curl http://localhost:8000/todos/1 ```

READ ALL - получение всех Todo
``` curl http://localhost:8000/todos ```

UPDATE - обновление Todo
```
curl -X PUT http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs, bread, cheese", "completed": true}'
```

DELETE - удаление Todo
``` curl -X DELETE http://localhost:8000/todos/1 ```
