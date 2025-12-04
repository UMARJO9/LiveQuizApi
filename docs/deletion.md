# LiveQuiz API — Deleting Topics and Questions

This document explains how deletions work and what to expect in responses. Deletions are authenticated operations and intended for the resource owner.

## 1. Delete Topic
- Endpoint: DELETE `/api/topics/<id>/`
- Current path in this build: DELETE `/api/quizzes/<id>/`

Behavior:
- Deleting a topic removes the topic and cascades to all of its questions and their answer options (database `on_delete=CASCADE`).

Example response (JSON):
```json
{
  "success": true,
  "code": 200,
  "message": "Topic deleted",
  "result": null
}
```

## 2. Delete Question
- Endpoint: DELETE `/api/questions/<id>/`
- Current path in this build: DELETE `/api/questions/<id>/delete/`

Behavior:
- Deleting a question automatically removes all associated answer options via cascade.

Example response (JSON):
```json
{
  "success": true,
  "code": 200,
  "message": "Question deleted",
  "result": null
}
```

## 3. Safety Notes
- Ownership: Endpoints are authenticated. Topic listing is restricted to the authenticated user’s own topics. Creation of questions verifies that the topic’s `teacher` matches the current user. Deletion operations are intended for owners.
- Not found: If a topic or question does not exist (or is not accessible), the API returns a 404.

Example error responses (JSON):

Topic not found:
```json
{
  "success": false,
  "code": 404,
  "message": "Topic not found",
  "result": null
}
```

Question not found:
```json
{
  "success": false,
  "code": 404,
  "message": "Question not found",
  "result": null
}
```

