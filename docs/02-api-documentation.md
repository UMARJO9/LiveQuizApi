# 2. API Documentation

[← Back to Index](./README.md) | [← System Overview](./01-system-overview.md)

---

## 2.1 Response Format

All API responses are wrapped in a standardized envelope by `StandardResponseMixin`:

```json
{
  "success": true,
  "code": 200,
  "message": "Success",
  "result": { /* actual data */ }
}
```

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | `true` if HTTP status is 2xx |
| code | integer | HTTP status code |
| message | string | Human-readable message |
| result | any | Response payload (`null` for delete operations) |

**Implementation:** `backend/responses.py`

---

## 2.2 Authentication

### JWT Configuration

| Setting | Value |
|---------|-------|
| Token Type | Access Token |
| Lifetime | 30 days |
| Algorithm | HS256 |
| Header | `Authorization: Bearer <token>` |

### Authenticated Requests

```bash
curl -X GET http://localhost:8000/api/quizzes/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

## 2.3 Authentication Endpoints

### POST /api/auth/login/

Authenticate user and obtain JWT access token.

| Property | Value |
|----------|-------|
| **Authentication** | None required |
| **Permission** | AllowAny |
| **Handler** | `users/views.py:11` |

#### Request Body

```json
{
  "email": "teacher@example.com",
  "password": "secretpassword"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string (email) | Either email or username | User's email address |
| username | string | Either email or username | Alternative to email |
| password | string | Yes | User's password |

#### Success Response (200)

```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "teacher@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "specialty": "Mathematics"
  }
}
```

#### Error Response (401)

```json
{
  "success": false,
  "message": "Invalid credentials"
}
```

#### Validation Rules
- Either `email` or `username` must be provided
- `password` is always required
- Returns 401 for invalid credentials (not 400)

#### Example

```bash
# Login with email
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "teacher@example.com", "password": "password123"}'

# Login with username (uses email as username)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "teacher@example.com", "password": "password123"}'
```

---

## 2.4 Topic Endpoints

### GET /api/quizzes/

List all topics owned by the authenticated user.

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:20` |

#### Query Parameters

None

#### Success Response (200)

```json
{
  "success": true,
  "code": 200,
  "message": "Success",
  "result": [
    {
      "id": 1,
      "title": "Mathematics Quiz",
      "description": "Basic algebra questions",
      "question_timer": 20,
      "questions": [
        {
          "id": 1,
          "text": "What is 2 + 2?",
          "topic_id": 1,
          "options": [
            {"id": 1, "text": "3", "is_correct": false},
            {"id": 2, "text": "4", "is_correct": true},
            {"id": 3, "text": "5", "is_correct": false},
            {"id": 4, "text": "6", "is_correct": false}
          ]
        }
      ],
      "created_at": "2025-12-01T10:00:00Z",
      "updated_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

#### Business Rules
- Only returns topics where `teacher=request.user`
- Includes nested questions and options
- Ordered by default Django ordering (id)

---

### POST /api/quizzes/

Create a new topic (quiz).

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:20` |

#### Request Body

```json
{
  "title": "Geography Quiz",
  "description": "World capitals",
  "question_timer": 30
}
```

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|-------------|
| title | string | Yes | - | max 255 chars |
| description | string | No | null | - |
| question_timer | integer | No | 20 | seconds per question |

#### Success Response (201)

```json
{
  "success": true,
  "code": 201,
  "message": "Success",
  "result": {
    "id": 2,
    "title": "Geography Quiz",
    "description": "World capitals",
    "question_timer": 30,
    "questions": [],
    "created_at": "2025-12-01T12:00:00Z",
    "updated_at": "2025-12-01T12:00:00Z"
  }
}
```

#### Business Rules
- Automatically sets `teacher=request.user`
- Questions array is empty on creation

---

### GET /api/quizzes/{id}/

Retrieve a specific topic by ID.

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:31` |

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Topic ID |

#### Success Response (200)

Same as single topic in list response.

#### Error Response (404)

```json
{
  "success": false,
  "code": 404,
  "message": "Not found.",
  "result": null
}
```

---

### PUT /api/quizzes/{id}/

Full update of a topic.

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:31` |

#### Request Body

```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "question_timer": 25
}
```

All fields are required for full update.

---

### PATCH /api/quizzes/{id}/

Partial update of a topic.

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:31` |

#### Request Body

```json
{
  "title": "New Title Only"
}
```

Only provided fields are updated.

---

### DELETE /api/quizzes/{id}/

Delete a topic and all its questions/options (cascade).

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:31` |

#### Success Response (200)

```json
{
  "success": true,
  "code": 200,
  "message": "Topic deleted",
  "result": null
}
```

#### Error Response (404)

```json
{
  "message": "Topic not found"
}
```

#### Business Rules
- Deleting a topic cascades to all questions and options
- No confirmation required

---

## 2.5 Question Endpoints

### POST /api/topics/{topic_id}/questions/

Create a new question with answer options.

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:47` |

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| topic_id | integer | Parent topic ID |

#### Request Body

```json
{
  "text": "What is the capital of France?",
  "options": [
    {"text": "London", "is_correct": false},
    {"text": "Paris", "is_correct": true},
    {"text": "Berlin", "is_correct": false},
    {"text": "Madrid", "is_correct": false}
  ]
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| text | string | Yes | max 500 chars |
| options | array | Yes | Exactly 4 items |
| options[].text | string | Yes | max 255 chars |
| options[].is_correct | boolean | Yes | At least 1 must be true |

#### Validation Rules

1. **Exactly 4 options** must be provided
2. **At least 1 option** must be marked as correct
3. User must own the parent topic (403 if not)

#### Success Response (201)

```json
{
  "success": true,
  "code": 201,
  "message": "Success",
  "result": {
    "id": 5,
    "text": "What is the capital of France?",
    "topic_id": 1,
    "options": [
      {"id": 17, "text": "London", "is_correct": false},
      {"id": 18, "text": "Paris", "is_correct": true},
      {"id": 19, "text": "Berlin", "is_correct": false},
      {"id": 20, "text": "Madrid", "is_correct": false}
    ]
  }
}
```

#### Error Responses

**400 - Validation Error:**
```json
{
  "success": false,
  "code": 400,
  "message": "Exactly four options are required.",
  "result": null
}
```

**403 - Permission Denied:**
```json
{
  "message": "You do not have permission to add questions to this topic."
}
```

**404 - Topic Not Found:**
```json
{
  "success": false,
  "code": 404,
  "message": "Not found.",
  "result": null
}
```

---

### PATCH /api/questions/{id}/

Update an existing question and/or its options.

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:95` |

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Question ID |

#### Request Body

```json
{
  "topic_id": 1,
  "text": "Updated question text",
  "options": [
    {"id": 17, "text": "Updated option 1", "is_correct": false},
    {"id": 18, "text": "Updated option 2", "is_correct": true},
    {"id": 19, "text": "Updated option 3", "is_correct": false},
    {"id": 20, "text": "Updated option 4", "is_correct": false}
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| topic_id | integer | Yes | Must match question's actual topic |
| text | string | No | New question text |
| options | array | No | Options to update |
| options[].id | integer | Yes (if updating) | Existing option ID |
| options[].text | string | No | New option text |
| options[].is_correct | boolean | No | New correct status |

#### Validation Rules

1. `topic_id` must match the question's actual topic (security check)
2. When updating options, all 4 must be provided
3. Option IDs must belong to this question
4. At least 1 option must be correct
5. User must own the topic

#### Success Response (200)

Returns the updated question with options.

#### Error Responses

**400 - Invalid Option:**
```json
{
  "message": "Option 99 does not belong to question 5."
}
```

**403 - Permission Denied:**
```json
{
  "message": "You do not have permission to update this question."
}
```

**404 - Question Not Found:**
```json
{
  "message": "Question not found"
}
```

**404 - Topic Mismatch:**
```json
{
  "message": "Question not found in this topic"
}
```

---

### DELETE /api/questions/{id}/delete/

Delete a question and all its options (cascade).

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:66` |

#### Success Response (200)

```json
{
  "success": true,
  "code": 200,
  "message": "Question deleted",
  "result": null
}
```

#### Error Response (404)

```json
{
  "message": "Question not found"
}
```

---

## 2.6 Answer Option Endpoints

### DELETE /api/options/{id}/delete/

Delete a single answer option.

| Property | Value |
|----------|-------|
| **Authentication** | Bearer JWT |
| **Permission** | IsAuthenticated |
| **Handler** | `quizzes/views.py:81` |

#### Success Response (200)

```json
{
  "success": true,
  "code": 200,
  "message": "Option deleted",
  "result": null
}
```

#### Warning

Deleting options may leave questions with fewer than 4 options, which will break quiz functionality. This endpoint should be used with caution.

---

## 2.7 Documentation Endpoints

### GET /api/schema/

Returns OpenAPI 3.0 schema as JSON.

| Property | Value |
|----------|-------|
| **Authentication** | None |
| **Handler** | `backend/urls.py:57` |

### GET /api/docs/

Swagger UI for interactive API documentation.

| Property | Value |
|----------|-------|
| **Authentication** | None |
| **Handler** | `backend/urls.py:530` |

---

## 2.8 URL Routing Notes

All endpoints support both trailing slash and no trailing slash:
- `/api/quizzes/` and `/api/quizzes` are equivalent
- This is configured via `APPEND_SLASH = False` in settings

---

## 2.9 Error Response Patterns

### Standard DRF Errors

```json
{
  "success": false,
  "code": 400,
  "message": "Error message from first field",
  "result": {
    "field_name": ["Error message"]
  }
}
```

### Custom View Errors

```json
{
  "message": "Custom error message"
}
```

### Authentication Errors

**401 - Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**401 - Invalid Token:**
```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid"
}
```

---

[Next: Database Schema →](./03-database-schema.md)
