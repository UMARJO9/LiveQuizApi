# LiveQuiz API — Working With Topics

> Note: In the current build, the Topics endpoints are exposed under `/api/quizzes/` in the backend URLs. This documentation uses the canonical path `/api/topics/`. If you receive 404s, use `/api/quizzes/` as a drop‑in replacement for the same operations until `/api/topics/` is added as an alias.

## 1. Create Topic
- Endpoint: POST `/api/topics/`
- Required fields: `title`, `description`, `question_timer`

Example request (JSON):
```json
{
  "title": "Python 101",
  "description": "Introductory quiz covering Python basics",
  "question_timer": 30
}
```

Example response (JSON):
```json
{
  "success": true,
  "code": 201,
  "message": "Success",
  "result": {
    "id": 12,
    "title": "Python 101",
    "description": "Introductory quiz covering Python basics",
    "question_timer": 30,
    "questions": [],
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": "2025-01-01T12:00:00Z"
  }
}
```

## 2. Get All Topics
- Endpoint: GET `/api/topics/`

Returns only topics for the authenticated user. Each topic embeds a brief list of its questions (with answer options).

Example response (JSON):
```json
{
  "success": true,
  "code": 200,
  "message": "Success",
  "result": [
    {
      "id": 12,
      "title": "Python 101",
      "description": "Introductory quiz covering Python basics",
      "question_timer": 30,
      "questions": [
        {
          "id": 51,
          "text": "What is PEP 8?",
          "topic_id": 12,
          "options": [
            { "id": 201, "text": "Python style guide", "is_correct": true },
            { "id": 202, "text": "A web framework", "is_correct": false },
            { "id": 203, "text": "A package manager", "is_correct": false },
            { "id": 204, "text": "A debugger", "is_correct": false }
          ]
        }
      ],
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:05:00Z"
    }
  ]
}
```

## 3. Get Single Topic With Questions
- Endpoint: GET `/api/topics/<id>/`

Returns the full topic object, including nested questions and their answer options.

Structure of the topic object:
```json
{
  "success": true,
  "code": 200,
  "message": "Success",
  "result": {
    "id": 12,
    "title": "Python 101",
    "description": "Introductory quiz covering Python basics",
    "question_timer": 30,
    "questions": [
      {
        "id": 51,
        "text": "What is PEP 8?",
        "topic_id": 12,
        "options": [
          { "id": 201, "text": "Python style guide", "is_correct": true },
          { "id": 202, "text": "A web framework", "is_correct": false },
          { "id": 203, "text": "A package manager", "is_correct": false },
          { "id": 204, "text": "A debugger", "is_correct": false }
        ]
      }
    ],
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": "2025-01-01T12:05:00Z"
  }
}
```

## 4. Update Topic
- Endpoint: PUT `/api/topics/<id>/`

Example request (JSON):
```json
{
  "title": "Python 101 — Updated",
  "description": "Revised intro quiz",
  "question_timer": 45
}
```

Example response (JSON):
```json
{
  "success": true,
  "code": 200,
  "message": "Success",
  "result": {
    "id": 12,
    "title": "Python 101 — Updated",
    "description": "Revised intro quiz",
    "question_timer": 45,
    "questions": [
      { "id": 51, "text": "What is PEP 8?", "topic_id": 12, "options": [
        { "id": 201, "text": "Python style guide", "is_correct": true },
        { "id": 202, "text": "A web framework", "is_correct": false },
        { "id": 203, "text": "A package manager", "is_correct": false },
        { "id": 204, "text": "A debugger", "is_correct": false }
      ]}
    ],
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": "2025-01-01T12:10:00Z"
  }
}
```

## 5. Delete Topic
- Endpoint: DELETE `/api/topics/<id>/`

Expected response (JSON):
```json
{
  "success": true,
  "code": 200,
  "message": "Topic deleted",
  "result": null
}
```

