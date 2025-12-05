# LiveQuiz API Guide

Все ответы сервера теперь идут в едином формате:
```
{
  "success": true|false,
  "code": 200|401|404|...,
  "message": "описание",
  "result": {...} | [] | null
}
```

## Аутентификация
- Регистрация: `POST /api/register/`
  - Тело: `email`, `password`, `password2`, `first_name`, `last_name`, `specialty`
  - Ответ `201`: `result` содержит `access`, `refresh`, `user`
- Логин (JWT): `POST /api/login/` с `email`, `password`
  - Ответ `200`: `result.access`, `result.refresh`, `result.user`
- Обновление токена: `POST /api/refresh/` с `refresh`
  - Ответ `200`: `result.access`
- Передавайте `Authorization: Bearer <access>` для защищенных эндпоинтов.

## Сущности
- Quiz (тема/тест): принадлежит `teacher` (пользователь). Поля: `title`, `description`, `created_at`, `updated_at`.
- Question (вопрос): принадлежит `quiz`, поля: `text`, `order_index`, список `choices`.
- Choice (вариант): принадлежит `question`, поля: `text`, `is_correct`.

## CRUD темы (Quiz)
- Список/создание: `GET/POST /api/quizzes/` (auth)
  - `POST` тело: `title`, `description?`
  - Ответы: `result` — массив викторин или созданная викторина.
- Детали/обновление/удаление: `GET/PUT/PATCH/DELETE /api/quizzes/{id}/` (auth)
  - `PUT/PATCH` тело: те же поля, что при создании.
  - `DELETE` возвращает `result: null` и `code: 200` (если удалено) или `404` (если не найдено).

## Добавление вопросов к теме
- Создать вопрос: `POST /api/quizzes/{quiz_id}/questions/` (auth)
  - Тело: `text` (обяз.), `order_index?` (целое), `choices?` (список вариантов с `text`, `is_correct`).
  - Ответ `201`: `result` — созданный вопрос с вариантами.
- Удалить вопрос: `DELETE /api/questions/{id}/delete/` (auth)
  - Ответ `200`: `result: null` (или `404`, если не найден).

## Добавление вариантов ответа
- Создать вариант: `POST /api/questions/{question_id}/choices/` (auth)
  - Тело: `text` (обяз.), `is_correct` (bool, по умолчанию false).
  - Ответ `201`: `result` — созданный вариант.
- Удалить вариант: `DELETE /api/choices/{id}/delete/` (auth)
  - Ответ `200`: `result: null` (или `404`, если не найден).

## Модели и связи (внутри Django)
- `Quiz.teacher -> User (ForeignKey)`, `Quiz` имеет `questions` (related_name).
- `Question.quiz -> Quiz (ForeignKey)`, `Question` имеет `choices` (related_name).
- `Choice.question -> Question (ForeignKey)`.

## Примеры запросов/ответов
- Создать викторину:
```
POST /api/quizzes/
Authorization: Bearer <token>
{
  "title": "Python basics",
  "description": "Intro questions"
}
```
Ответ:
```
{
  "success": true,
  "code": 201,
  "message": "Success",
  "result": {
    "id": 1,
    "title": "Python basics",
    "description": "Intro questions",
    "questions": [],
    "created_at": "...",
    "updated_at": "..."
  }
}
```
- Добавить вопрос c вариантами:
```
POST /api/quizzes/1/questions/
Authorization: Bearer <token>
{
  "text": "What is PEP 8?",
  "order_index": 1,
  "choices": [
    {"text": "Style guide", "is_correct": true},
    {"text": "Web framework", "is_correct": false}
  ]
}
```
- Удалить вариант:
```
DELETE /api/choices/5/delete/
Authorization: Bearer <token>
```

## Где смотреть схему
- Swagger UI: `/api/docs/`
- JSON-схема OpenAPI: `/api/schema/` или `/openapi.json`

## Обновление вопроса (PATCH /api/questions/{id}/)
- Аутентификация: Bearer JWT
- Content-Type: application/json
- Обязательное поле в теле: `topic_id` (число) — для проверки принадлежности вопроса теме
- Необязательные поля: `text`, `options` (если переданы, ровно 4 варианта, каждый с существующим `id`)
- Валидация: среди `options` минимум один `is_correct: true`; каждый `options.id` должен принадлежать обновляемому вопросу

Пример запроса:
```
PATCH /api/questions/3/
Authorization: Bearer <token>
Content-Type: application/json

{
  "topic_id": 8,
  "text": "Какой цвет у неба?",
  "options": [
    { "id": 101, "text": "Синий",  "is_correct": true },
    { "id": 102, "text": "Зелёный", "is_correct": false },
    { "id": 103, "text": "Жёлтый",  "is_correct": false },
    { "id": 104, "text": "Красный", "is_correct": false }
  ]
}
```
