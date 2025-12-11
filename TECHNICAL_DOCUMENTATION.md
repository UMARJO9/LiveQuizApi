# LiveQuizApi - Technical Documentation

**Version:** 1.0.0
**Generated:** December 2025
**System Type:** Real-time Quiz Platform (Kahoot-like)

---

# Table of Contents

1. [System Overview](#1-system-overview)
2. [API Documentation](#2-api-documentation)
3. [Database Schema](#3-database-schema)
4. [Socket.IO Events](#4-socketio-events)
5. [Cross-Cutting Concerns](#5-cross-cutting-concerns)

---

# 1. System Overview

## 1.1 Architecture Summary

LiveQuizApi is a real-time quiz platform implementing Kahoot-like functionality. The system enables teachers to create quiz topics with questions, host live quiz sessions, and have students join and answer questions in real-time.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌─────────────────┐              ┌─────────────────┐           │
│  │  Teacher Client │              │  Student Client │           │
│  │  (Web/Mobile)   │              │  (Web/Mobile)   │           │
│  └────────┬────────┘              └────────┬────────┘           │
│           │                                │                     │
│           │  HTTP/REST                     │  WebSocket          │
│           │  + WebSocket                   │                     │
└───────────┼────────────────────────────────┼─────────────────────┘
            │                                │
            ▼                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ASGI APPLICATION                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    backend/asgi.py                       │    │
│  │  ┌──────────────────┐    ┌──────────────────────────┐   │    │
│  │  │  Django ASGI     │    │  Socket.IO AsyncServer   │   │    │
│  │  │  (HTTP requests) │    │  (WebSocket /socket.io/) │   │    │
│  │  └────────┬─────────┘    └───────────┬──────────────┘   │    │
│  └───────────┼──────────────────────────┼──────────────────┘    │
└──────────────┼──────────────────────────┼───────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────┐   ┌──────────────────────────────────┐
│   Django REST Framework  │   │      Socket.IO Server            │
│  ┌────────────────────┐  │   │  ┌────────────────────────────┐  │
│  │ users/views.py     │  │   │  │ sockets/server.py          │  │
│  │ - LoginAPIView     │  │   │  │ - Teacher event handlers   │  │
│  ├────────────────────┤  │   │  │ - Student event handlers   │  │
│  │ quizzes/views.py   │  │   │  │ - Timer management         │  │
│  │ - TopicCRUD        │  │   │  ├────────────────────────────┤  │
│  │ - QuestionCRUD     │  │   │  │ sockets/managers/          │  │
│  │ - OptionCRUD       │  │   │  │ - SessionManager           │  │
│  └────────────────────┘  │   │  │ - QuestionManager          │  │
└──────────┬───────────────┘   │  │ - RankingManager           │  │
           │                   │  └────────────────────────────┘  │
           │                   └──────────────┬───────────────────┘
           │                                  │
           ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
│  ┌─────────────────────────┐    ┌─────────────────────────────┐ │
│  │   PostgreSQL Database   │    │   In-Memory Session Store   │ │
│  │  ┌───────────────────┐  │    │  ┌───────────────────────┐  │ │
│  │  │ users_user        │  │    │  │ active_sessions{}     │  │ │
│  │  │ quizzes_topic     │  │    │  │ question_timers{}     │  │ │
│  │  │ quizzes_question  │  │    │  └───────────────────────┘  │ │
│  │  │ quizzes_answeroption│ │    └─────────────────────────────┘ │
│  │  └───────────────────┘  │                                    │
│  └─────────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────┘
```

## 1.2 Tech Stack

| Category | Technology | Version |
|----------|------------|---------|
| **Framework** | Django | 5.2.8 |
| **API** | Django REST Framework | 3.15.x |
| **Authentication** | djangorestframework-simplejwt | 5.5.1 |
| **Real-time** | python-socketio (AsyncServer) | 5.10+ |
| **Database** | PostgreSQL | - |
| **DB Driver** | psycopg2-binary | 2.9+ |
| **ASGI Server** | uvicorn | 0.27+ |
| **CORS** | django-cors-headers | 4.3+ |
| **Async HTTP** | aiohttp | 3.9+ |

## 1.3 Django Applications

| App | Purpose | Models | Status |
|-----|---------|--------|--------|
| **users** | User authentication and profile management | User | Active |
| **quizzes** | Quiz content management (topics, questions, options) | Topic, Question, AnswerOption | Active |
| **live** | Placeholder for future live session persistence | None | Empty |

## 1.4 Main Functional Domains

### 1.4.1 User Management (users app)
- Custom user model with email-based authentication
- JWT token generation and validation
- Profile fields: first_name, last_name, specialty

### 1.4.2 Quiz Content Management (quizzes app)
- **Topics**: Quiz containers owned by teachers
- **Questions**: Multiple-choice questions with ordering
- **Answer Options**: Exactly 4 options per question, at least 1 correct

### 1.4.3 Live Quiz Sessions (sockets module)
- Real-time quiz hosting via Socket.IO
- Session management with 4-character codes (e.g., "AB12")
- Question delivery with countdown timers
- Answer collection and scoring
- Leaderboard with tie support

## 1.5 High-Level Flows

### 1.5.1 API Request Lifecycle

```
Client Request
      │
      ▼
┌─────────────────┐
│  ASGI Router    │──── /socket.io/* ───► Socket.IO Handler
│  (asgi.py)      │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  Django URLs    │
│  (urls.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  DRF View       │────►│  Serializer     │
│  (APIView)      │     │  (validation)   │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Django ORM     │
│  (models)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL     │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ StandardResponse│
│ Mixin (wrapper) │
└────────┬────────┘
         │
         ▼
   JSON Response
   {success, code, message, result}
```

### 1.5.2 Socket Event Lifecycle

```
┌──────────────────────────────────────────────────────────────────┐
│                    QUIZ SESSION LIFECYCLE                         │
└──────────────────────────────────────────────────────────────────┘

PHASE 1: SESSION CREATION
─────────────────────────
Teacher                          Server                      Database
   │                               │                            │
   │── teacher:create_session ────►│                            │
   │   {topic_id}                  │                            │
   │                               │── load topic data ────────►│
   │                               │◄── topic + questions ──────│
   │                               │                            │
   │                               │ [Generate 4-char code]     │
   │                               │ [Store in active_sessions] │
   │                               │                            │
   │◄── teacher:session_created ───│                            │
   │    {session_id, code, topic}  │                            │

PHASE 2: WAITING FOR STUDENTS
─────────────────────────────
Student                          Server                      Teacher
   │                               │                            │
   │── student:join ──────────────►│                            │
   │   {session_id, name}          │                            │
   │                               │── session:state ──────────►│
   │◄── student:joined ────────────│   {students[]}             │

PHASE 3: QUIZ RUNNING
─────────────────────
Teacher                          Server                      Students
   │                               │                            │
   │── teacher:start_session ─────►│                            │
   │                               │── session:question ───────►│
   │                               │   {id, text, options, time}│
   │                               │                            │
   │                               │ [Start timer task]         │
   │                               │                            │
   │                               │◄── student:answer ─────────│
   │◄── session:answer_count ──────│    {option_id}             │
   │                               │                            │
   │                               │ [Timer expires OR all answered]
   │                               │                            │
   │                               │── answer_result ──────────►│
   │◄── session:ranking ───────────│   {correct, score}         │

PHASE 4: QUIZ FINISHED
──────────────────────
   │── teacher:next_question ─────►│  (repeat Phase 3)          │
   │        ...                    │                            │
   │                               │ [No more questions]        │
   │                               │                            │
   │◄── quiz_finished ─────────────│── quiz_finished ──────────►│
       {winners, scoreboard}           {winners, scoreboard}
```

### 1.5.3 Database Interaction Pattern

The Socket.IO server uses `asyncio.to_thread()` to execute synchronous Django ORM queries without blocking the async event loop:

```python
# Pattern used in sockets/managers/questions.py
async def load_question(question_id: int):
    return await asyncio.to_thread(_load_question_sync, question_id)

def _load_question_sync(question_id: int):
    # Synchronous Django ORM query
    return Question.objects.prefetch_related("options").get(id=question_id)
```

---

# 2. API Documentation

## 2.1 Response Format

All API responses are wrapped in a standardized envelope:

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
| success | boolean | true if HTTP status is 2xx |
| code | integer | HTTP status code |
| message | string | Human-readable message |
| result | any | Response payload (null for delete operations) |

---

## 2.2 Authentication Endpoints

### POST /api/auth/login/

Authenticate user and obtain JWT access token.

**Authentication:** None required

**Permission:** AllowAny

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

#### Business Rules
- Either `email` or `username` must be provided (not both required)
- Password is required
- Returns JWT access token valid for 30 days

#### Example

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "teacher@example.com", "password": "password123"}'
```

---

## 2.3 Topic Endpoints

### GET /api/quizzes/

List all topics owned by the authenticated user.

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

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

#### DB Relations
- Reads: Topic (filtered by teacher=request.user)
- Includes: Nested Question and AnswerOption via serializers

#### Example

```bash
curl -X GET http://localhost:8000/api/quizzes/ \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/quizzes/

Create a new topic (quiz).

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

#### Request Body

```json
{
  "title": "Geography Quiz",
  "description": "World capitals",
  "question_timer": 30
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| title | string | Yes | - | Topic title (max 255 chars) |
| description | string | No | null | Topic description |
| question_timer | integer | No | 20 | Seconds per question |

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

#### DB Relations
- Creates: Topic with teacher=request.user

---

### GET /api/quizzes/{id}/

Retrieve a specific topic by ID.

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | Topic ID |

#### Success Response (200)

```json
{
  "success": true,
  "code": 200,
  "message": "Success",
  "result": {
    "id": 1,
    "title": "Mathematics Quiz",
    "description": "Basic algebra questions",
    "question_timer": 20,
    "questions": [...],
    "created_at": "2025-12-01T10:00:00Z",
    "updated_at": "2025-12-01T10:00:00Z"
  }
}
```

---

### PUT /api/quizzes/{id}/

Full update of a topic.

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

#### Request Body

```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "question_timer": 25
}
```

#### Success Response (200)

Returns the updated topic object.

---

### PATCH /api/quizzes/{id}/

Partial update of a topic.

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

#### Request Body

```json
{
  "title": "New Title Only"
}
```

---

### DELETE /api/quizzes/{id}/

Delete a topic and all its questions/options (cascade).

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

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

---

## 2.4 Question Endpoints

### POST /api/topics/{topic_id}/questions/

Create a new question with answer options.

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

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
| text | string | Yes | Max 500 chars |
| options | array | Yes | Exactly 4 items |
| options[].text | string | Yes | Max 255 chars |
| options[].is_correct | boolean | Yes | At least 1 must be true |

#### Validation Rules
- Exactly 4 options must be provided
- At least 1 option must be marked as correct
- User must own the parent topic

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

#### Error Response (403)

```json
{
  "message": "You do not have permission to add questions to this topic."
}
```

---

### PATCH /api/questions/{id}/

Update an existing question and/or its options.

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

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
| topic_id | integer | Yes | Must match question's topic |
| text | string | No | New question text |
| options | array | No | Options to update |
| options[].id | integer | Yes (if updating) | Existing option ID |

#### Validation Rules
- `topic_id` must match the question's actual topic
- When updating options, all 4 must be provided
- Option IDs must belong to this question
- At least 1 option must be correct

#### Success Response (200)

Returns the updated question with options.

#### Error Response (400)

```json
{
  "message": "Option 99 does not belong to question 5."
}
```

---

### DELETE /api/questions/{id}/delete/

Delete a question and all its options (cascade).

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

#### Success Response (200)

```json
{
  "success": true,
  "code": 200,
  "message": "Question deleted",
  "result": null
}
```

---

## 2.5 Answer Option Endpoints

### DELETE /api/options/{id}/delete/

Delete a single answer option.

**Authentication:** Bearer JWT

**Permission:** IsAuthenticated

#### Success Response (200)

```json
{
  "success": true,
  "code": 200,
  "message": "Option deleted",
  "result": null
}
```

**Warning:** Deleting options may leave questions with fewer than 4 options, breaking quiz functionality.

---

## 2.6 Documentation Endpoints

### GET /api/schema/

Returns OpenAPI 3.0 schema as JSON.

### GET /api/docs/

Swagger UI for interactive API documentation.

---

# 3. Database Schema

## 3.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATABASE SCHEMA                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│    users_user       │
├─────────────────────┤
│ PK id              │
│    email (unique)   │
│    password         │
│    first_name       │
│    last_name        │
│    specialty        │
│    is_active        │
│    is_staff         │
│    is_superuser     │
│    last_login       │
└─────────┬───────────┘
          │
          │ 1:N (teacher)
          ▼
┌─────────────────────┐
│   quizzes_topic     │
├─────────────────────┤
│ PK id              │
│ FK teacher_id ──────┼───► users_user.id
│    title            │
│    description      │
│    question_timer   │
│    created_at       │
│    updated_at       │
└─────────┬───────────┘
          │
          │ 1:N (topic)
          ▼
┌─────────────────────┐
│  quizzes_question   │
├─────────────────────┤
│ PK id              │
│ FK topic_id ────────┼───► quizzes_topic.id
│    text             │
│    order_index      │
└─────────┬───────────┘
          │
          │ 1:N (question)
          ▼
┌─────────────────────┐
│ quizzes_answeroption│
├─────────────────────┤
│ PK id              │
│ FK question_id ─────┼───► quizzes_question.id
│    text             │
│    is_correct       │
└─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│    auth_group       │     │   auth_permission   │
├─────────────────────┤     ├─────────────────────┤
│ (Django built-in)   │     │ (Django built-in)   │
└─────────────────────┘     └─────────────────────┘
          │                           │
          └───────────┬───────────────┘
                      │ M:N
                      ▼
┌─────────────────────────────────────────────────┐
│              users_user_groups                   │
│              users_user_user_permissions         │
│              (Junction tables)                   │
└─────────────────────────────────────────────────┘
```

---

## 3.2 Model: User

**Table:** `users_user`

**Description:** Custom user model for teacher authentication. Uses email as the primary identifier instead of username.

### Fields

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| id | BigAutoField | Auto | Auto | PK | Primary key |
| email | EmailField | Yes | - | Unique, max 254 | User's email (login identifier) |
| password | CharField | Yes | - | max 128 | Hashed password |
| first_name | CharField | No | null | max 150 | User's first name |
| last_name | CharField | No | null | max 150 | User's last name |
| specialty | CharField | No | null | max 255 | Professional specialty |
| is_active | BooleanField | No | True | - | Account active status |
| is_staff | BooleanField | No | False | - | Django admin access |
| is_superuser | BooleanField | No | False | - | All permissions granted |
| last_login | DateTimeField | No | null | - | Last login timestamp |

### Relationships

| Relation | Type | Related Model | Related Name | On Delete |
|----------|------|---------------|--------------|-----------|
| groups | M:N | auth.Group | user_set | - |
| user_permissions | M:N | auth.Permission | user_set | - |
| topics | 1:N (reverse) | Topic | topics | CASCADE |

### Business Rules
- Email is the USERNAME_FIELD for authentication
- Password is hashed using Django's password hashers
- UserManager provides `create_user()` and `create_superuser()` methods

### Used in APIs
- POST /api/auth/login/ (authentication)

### Used in Socket Events
- Indirectly via Topic ownership validation

---

## 3.3 Model: Topic

**Table:** `quizzes_topic`

**Description:** Represents a quiz/topic container owned by a teacher. Contains configuration and metadata for quiz sessions.

### Fields

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| id | BigAutoField | Auto | Auto | PK | Primary key |
| teacher_id | BigIntegerField | Yes | - | FK | Owner user ID |
| title | CharField | Yes | - | max 255 | Quiz title |
| description | TextField | No | null | - | Quiz description |
| question_timer | IntegerField | No | 20 | - | Seconds per question |
| created_at | DateTimeField | Auto | now | auto_now_add | Creation timestamp |
| updated_at | DateTimeField | Auto | now | auto_now | Last update timestamp |

### Relationships

| Relation | Type | Related Model | Related Name | On Delete |
|----------|------|---------------|--------------|-----------|
| teacher | FK | User | topics | CASCADE |
| questions | 1:N (reverse) | Question | questions | CASCADE |

### Business Rules
- Deleting a topic cascades to all questions and options
- `question_timer` determines how long students have to answer each question
- Default timer is 20 seconds

### Used in APIs
- GET/POST /api/quizzes/
- GET/PUT/PATCH/DELETE /api/quizzes/{id}/

### Used in Socket Events
- `teacher:create_session` - loads topic data and question_timer

---

## 3.4 Model: Question

**Table:** `quizzes_question`

**Description:** Represents a multiple-choice question within a topic.

### Fields

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| id | BigAutoField | Auto | Auto | PK | Primary key |
| topic_id | BigIntegerField | Yes | - | FK | Parent topic ID |
| text | CharField | Yes | - | max 500 | Question text |
| order_index | IntegerField | No | 0 | - | Display order within topic |

### Relationships

| Relation | Type | Related Model | Related Name | On Delete |
|----------|------|---------------|--------------|-----------|
| topic | FK | Topic | questions | CASCADE |
| options | 1:N (reverse) | AnswerOption | options | CASCADE |

### Business Rules
- Questions are loaded ordered by `order_index` for quiz sessions
- During live sessions, question order is shuffled
- Must have exactly 4 options (enforced by serializer, not DB)

### Used in APIs
- POST /api/topics/{topic_id}/questions/
- PATCH /api/questions/{id}/
- DELETE /api/questions/{id}/delete/

### Used in Socket Events
- `teacher:create_session` - loads question IDs
- `session:question` - sends question to students

---

## 3.5 Model: AnswerOption

**Table:** `quizzes_answeroption`

**Description:** Represents an answer option for a question.

### Fields

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| id | BigAutoField | Auto | Auto | PK | Primary key |
| question_id | BigIntegerField | Yes | - | FK | Parent question ID |
| text | CharField | Yes | - | max 255 | Option text |
| is_correct | BooleanField | No | False | - | Correct answer flag |

### Relationships

| Relation | Type | Related Model | Related Name | On Delete |
|----------|------|---------------|--------------|-----------|
| question | FK | Question | options | CASCADE |

### Business Rules
- At least one option per question must have `is_correct=True` (enforced by serializer)
- Multiple options can be marked as correct (code handles `MultipleObjectsReturned`)
- Options are NOT shuffled during quiz sessions (sent in DB order)

### Used in APIs
- Created via POST /api/topics/{topic_id}/questions/
- Updated via PATCH /api/questions/{id}/
- DELETE /api/options/{id}/delete/

### Used in Socket Events
- `session:question` - options sent to students (without is_correct)
- `answer_result` - correct_option_id revealed after question closes

---

## 3.6 Migration History

### users app

| Migration | Description |
|-----------|-------------|
| 0001_initial | Create User model with email, password, is_active, is_staff, groups, permissions |
| 0002_add_profile_fields | Add first_name, last_name, specialty, role fields |
| 0003_remove_user_role | Remove role field (unused) |

### quizzes app

| Migration | Description |
|-----------|-------------|
| 0001_initial | Create Topic, Question, AnswerOption models with relationships |

---

# 4. Socket.IO Events

## 4.1 Server Configuration

```python
# sockets/server.py
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
)
```

**Path:** `/socket.io/`
**Namespace:** Default (`/`)
**Transport:** WebSocket with HTTP long-polling fallback

---

## 4.2 In-Memory Data Structures

### active_sessions

```python
# sockets/managers/sessions.py
active_sessions: dict[str, SessionData] = {}

class SessionData(TypedDict):
    session_id: str              # 4-char code (e.g., "AB12")
    topic_id: int                # FK to Topic
    teacher_sid: str             # Teacher's socket ID
    time_per_question: int       # Seconds per question
    question_queue: list[int]    # Remaining question IDs (shuffled)
    current_question: int | None # Current question ID
    current_correct_option: int | None  # Cached correct option ID
    question_started_at: datetime | None
    question_deadline: datetime | None
    answers: dict[str, int]      # {student_sid: option_id}
    students: dict[str, StudentData]  # {sid: {name, score}}
    stage: str                   # "waiting" | "running" | "finished"
```

### question_timers

```python
# sockets/server.py
question_timers: dict[str, asyncio.Task] = {}
# {session_id: Timer Task}
```

---

## 4.3 Connection Events

### Event: connect

**Direction:** Client → Server

**Description:** Fired when any client (teacher or student) connects to the Socket.IO server.

**Handler:** `sockets/server.py:337`

**Payload:** None (auth data optional)

```python
# Client connection with optional auth
sio.connect("http://server", auth={"token": "jwt_token"})
```

**Server Behavior:**
- Logs connection with socket ID
- Does NOT assign role (waits for join event)
- Auth token is logged but not validated

**Assumption:** JWT validation for socket connections is not implemented. Auth data is informational only.

---

### Event: disconnect

**Direction:** Client → Server (automatic)

**Description:** Fired when a client disconnects (intentionally or due to network issues).

**Handler:** `sockets/server.py:354`

**Server Behavior:**

For **Students**:
1. Finds session by student SID
2. Removes student from session
3. Emits `session:state` to teacher with updated student list

For **Teachers**:
1. Finds session by teacher SID
2. Emits `session:ended` to all students in room
3. Deletes session from `active_sessions`

---

## 4.4 Teacher Events

### Event: teacher:create_session

**Direction:** Client → Server

**Description:** Teacher creates a new quiz session for a topic.

**Handler:** `sockets/server.py:402`

#### Payload Schema

```json
{
  "topic_id": 1
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| topic_id | integer | Yes | ID of the topic to use |

#### Server Processing

1. Validate `topic_id` provided
2. Load topic from DB (title, description, question_timer)
3. Load all question IDs for topic (ordered by order_index)
4. Shuffle question IDs
5. Generate unique 4-character session code
6. Create session object in `active_sessions`
7. Add teacher to room `room_{session_id}`
8. Emit `teacher:session_created`

#### Emitted Events

**teacher:session_created** → Teacher only

```json
{
  "session_id": "AB12",
  "code": "AB12",
  "topic": {
    "id": 1,
    "title": "Mathematics Quiz",
    "description": "Basic algebra",
    "time_per_question": 20
  },
  "question_count": 10
}
```

#### Errors

```json
{"message": "topic_id is required"}
{"message": "Topic not found"}
{"message": "No questions found for topic"}
```

---

### Event: teacher:start_session

**Direction:** Client → Server

**Description:** Teacher starts the quiz, sending the first question to all students.

**Handler:** `sockets/server.py:471`

#### Payload Schema

```json
{
  "session_id": "AB12"
}
```

#### Server Processing

1. Validate session exists
2. Verify sender is the teacher
3. Check stage is "waiting"
4. Check at least 1 student joined
5. Set stage to "running"
6. Pop first question from queue
7. Call `send_question()` which:
   - Loads question + options from DB
   - Sets up session timing state
   - Caches correct_option_id
   - Emits `session:question` to room
   - Starts auto-close timer

#### Emitted Events

**session:started** → Teacher only

```json
{
  "session_id": "AB12"
}
```

**session:question** → All students (room)

```json
{
  "type": "question",
  "id": 5,
  "text": "What is 2 + 2?",
  "options": [
    {"id": 17, "text": "3"},
    {"id": 18, "text": "4"},
    {"id": 19, "text": "5"},
    {"id": 20, "text": "6"}
  ],
  "time": 20
}
```

**Note:** `is_correct` is NOT sent to students.

#### Errors

```json
{"message": "session_id is required"}
{"message": "Session not found"}
{"message": "Not authorized"}
{"message": "Session already started"}
{"message": "No students in session"}
{"message": "No questions available"}
```

---

### Event: teacher:next_question

**Direction:** Client → Server

**Description:** Teacher advances to the next question (closes current question first).

**Handler:** `sockets/server.py:532`

#### Payload Schema

```json
{
  "session_id": "AB12"
}
```

#### Server Processing

1. Validate session and teacher
2. Check stage is "running"
3. Call `close_question()` to process current question
4. If questions remain: send next question
5. If no questions: call `finish_session()`

#### Emitted Events (from close_question)

**session:answer_count** → Teacher

```json
{
  "answered": 8,
  "total": 10
}
```

**answer_result** → Each student individually

```json
{
  "type": "answer_result",
  "correct": true,
  "correct_option": 18,
  "your_answer": 18,
  "score_delta": 20,
  "score_total": 40
}
```

**session:question_closed** → Teacher + Room

```json
{
  "question_id": 5
}
```

**ranking** + **session:ranking** → Teacher

```json
{
  "type": "ranking",
  "players": [
    {"name": "Alice", "score": 60, "position": 1},
    {"name": "Bob", "score": 60, "position": 1},
    {"name": "Charlie", "score": 40, "position": 2}
  ]
}
```

---

### Event: teacher:finish_session

**Direction:** Client → Server

**Description:** Teacher manually ends the quiz early.

**Handler:** `sockets/server.py:583`

#### Payload Schema

```json
{
  "session_id": "AB12"
}
```

#### Server Processing

1. Validate session and teacher
2. If running, close current question
3. Call `finish_session()` to end quiz

#### Emitted Events

**quiz_finished** → Teacher + Room

```json
{
  "type": "quiz_finished",
  "winners": [
    {"name": "Alice", "score": 80},
    {"name": "Bob", "score": 80}
  ],
  "scoreboard": [
    {"name": "Alice", "score": 80, "position": 1},
    {"name": "Bob", "score": 80, "position": 1},
    {"name": "Charlie", "score": 60, "position": 2}
  ]
}
```

---

## 4.5 Student Events

### Event: student:join

**Direction:** Client → Server

**Description:** Student joins a quiz session using the 4-character code.

**Handler:** `sockets/server.py:625`

#### Payload Schema

```json
{
  "session_id": "AB12",
  "name": "Alice"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string | Yes | 4-char session code |
| name | string | Yes | Student's display name |

#### Validation Rules

- Session must exist
- Session stage must be "waiting" (cannot join after quiz started)
- Name must not be empty (whitespace trimmed)

#### Server Processing

1. Validate inputs
2. Check session exists and is waiting
3. Add student to session with score=0
4. Add student to room `room_{session_id}`
5. Confirm join to student
6. Notify teacher of updated student list

#### Emitted Events

**student:joined** → Student only

```json
{
  "session_id": "AB12",
  "name": "Alice",
  "message": "Successfully joined the quiz"
}
```

**session:state** → Teacher only

```json
{
  "students": [
    {"sid": "abc123", "name": "Alice", "score": 0},
    {"sid": "def456", "name": "Bob", "score": 0}
  ]
}
```

#### Errors

```json
{"message": "session_id is required"}
{"message": "name is required"}
{"message": "Session not found"}
{"message": "Cannot join - quiz already started"}
{"message": "Could not join session"}
```

---

### Event: student:answer

**Direction:** Client → Server

**Description:** Student submits an answer to the current question.

**Handler:** `sockets/server.py:702`

#### Payload Schema

```json
{
  "session_id": "AB12",
  "option_id": 18
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string | Yes | Session code |
| option_id | integer | Yes | Selected answer option ID |

#### Validation Rules

- Session must exist
- Student must be in this session
- Session stage must be "running"
- Question deadline must not be expired
- Student must not have already answered this question

#### Server Processing

1. Validate all conditions
2. Record answer in `session["answers"]`
3. Confirm to student
4. Update teacher with answer count
5. If all students answered, close question immediately

#### Emitted Events

**student:answer_received** → Student only

```json
{
  "message": "Answer received"
}
```

**session:answer_count** → Teacher only

```json
{
  "answered": 5,
  "total": 10
}
```

#### Auto-close Trigger

If `len(answers) == len(students)`, `close_question()` is called immediately (before timer expires).

#### Errors

```json
{"message": "session_id is required"}
{"message": "option_id is required"}
{"message": "Session not found"}
{"message": "Not in this session"}
{"message": "Cannot answer - time expired or quiz not running"}
{"message": "Already answered this question"}
{"message": "Could not record answer"}
```

---

### Event: student:leave

**Direction:** Client → Server

**Description:** Student voluntarily leaves the quiz session.

**Handler:** `sockets/server.py:793`

#### Payload Schema

```json
{
  "session_id": "AB12"
}
```

#### Server Processing

1. Validate session exists
2. Remove student from session
3. Leave room
4. Confirm to student
5. Notify teacher

#### Emitted Events

**student:left** → Student only

```json
{
  "message": "Left the quiz"
}
```

**session:state** → Teacher only

Updated student list.

---

## 4.6 Utility Events

### Event: get_session_state

**Direction:** Client → Server

**Description:** Request current session state (useful for reconnection or debugging).

**Handler:** `sockets/server.py:840`

#### Payload Schema

```json
{
  "session_id": "AB12"
}
```

#### Emitted Events

**session:state** → Requester only

```json
{
  "session_id": "AB12",
  "stage": "running",
  "students": [...],
  "current_question": 5,
  "questions_remaining": 7
}
```

---

## 4.7 Server-Emitted Events Summary

| Event | Recipients | When |
|-------|------------|------|
| `teacher:session_created` | Teacher | After session creation |
| `session:started` | Teacher | After quiz starts |
| `session:state` | Teacher | Student joins/leaves |
| `session:question` | Room (students) | New question delivered |
| `session:question_closed` | Teacher + Room | Question ends |
| `session:answer_count` | Teacher | Student answers |
| `session:ranking` | Teacher | After question closes |
| `session:timer_expired` | Teacher + Room | Timer runs out |
| `session:ended` | Room | Teacher disconnects |
| `student:joined` | Student | Join confirmed |
| `student:answer_received` | Student | Answer confirmed |
| `student:left` | Student | Leave confirmed |
| `answer_result` | Student | Individual result after question |
| `ranking` | Teacher | After question (legacy) |
| `quiz_finished` | Teacher + Room | Quiz ends |
| `error` | Sender | Validation failures |

---

## 4.8 Timer Mechanism

### Timer Creation

```python
# sockets/server.py:116
def start_question_timer(session_id: str, timeout: int) -> None:
    task = asyncio.create_task(question_timer_task(session_id, timeout))
    question_timers[session_id] = task
```

### Timer Task

```python
# sockets/server.py:63
async def question_timer_task(session_id: str, timeout: int) -> None:
    await asyncio.sleep(timeout)
    # Emit session:timer_expired
    # Call close_question(from_timer=True)
```

### Timer Cancellation

Timers are cancelled when:
- Teacher requests next question
- All students answer before timeout
- Teacher finishes session
- **NOT** when called from timer itself (`from_timer=True` flag)

---

## 4.9 Room Architecture

```
Room: room_{session_id}

Members:
├── Teacher (sid)
└── Students (sid1, sid2, sid3, ...)

Broadcast to room → All students receive
Emit to teacher_sid → Teacher only
Emit to student_sid → Specific student only
```

---

## 4.10 Scoring System

| Event | Points |
|-------|--------|
| Correct answer | +20 |
| Incorrect answer | 0 |
| No answer | 0 |

**Constant:** `QuestionManager.POINTS_CORRECT = 20`

---

# 5. Cross-Cutting Concerns

## 5.1 Authentication

### REST API Authentication

**Method:** JWT (JSON Web Token)

**Library:** djangorestframework-simplejwt

**Configuration:** `backend/settings.py:153-163`

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
```

**Token Usage:**
```
Authorization: Bearer <access_token>
```

**Token Lifetime:** 30 days

### Socket.IO Authentication

**Status:** NOT IMPLEMENTED

**Current Behavior:**
- Auth data is accepted during connection
- Token is logged but NOT validated
- Any client can emit events without authentication

**Assumption:** Socket authentication is planned but not yet implemented. The `auth` parameter in `connect()` is informational only.

---

## 5.2 Configuration

### Environment Variables

| Variable | Location | Description |
|----------|----------|-------------|
| DJANGO_SETTINGS_MODULE | asgi.py | Points to settings |

### Important Settings

| Setting | Value | File |
|---------|-------|------|
| SECRET_KEY | `django-insecure-...` | settings.py:24 |
| DEBUG | True | settings.py:27 |
| AUTH_USER_MODEL | "users.User" | settings.py:121 |
| APPEND_SLASH | False | settings.py:60 |

**Warning:** The SECRET_KEY is hardcoded and insecure. Should use environment variable in production.

### Database Configuration

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'live_quiz',
        'USER': 'postgres',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

**Warning:** Database credentials are hardcoded. Should use environment variables.

### CORS Configuration

```python
CORS_ALLOW_ALL_ORIGINS = True  # Development only!

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.43.20:5173",
    "http://192.168.43.20:5174",  # Note: missing comma causes concatenation bug
]

CORS_ALLOW_CREDENTIALS = True
```

**Bug:** Line 65-66 has missing comma, causing URL concatenation.

### Socket.IO CORS

```python
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    # ...
)
```

---

## 5.3 Error Handling

### REST API Errors

**Standard Response Wrapper:** `backend/responses.py`

All errors are wrapped in the standard envelope:

```json
{
  "success": false,
  "code": 400,
  "message": "Validation error message",
  "result": null
}
```

**DRF Exception Handling:** Default (not customized)

### Socket.IO Errors

All validation errors emit an `error` event:

```json
{
  "message": "Error description"
}
```

**Common Error Patterns:**
- Missing required fields
- Session not found
- Not authorized
- Invalid state transitions
- Duplicate actions (already answered)

---

## 5.4 Logging

### Socket.IO Logging

```python
sio = socketio.AsyncServer(
    logger=True,
    engineio_logger=True,
)
```

**Custom Logging:**
- `[CONNECT]` - Connection events
- `[DISCONNECT]` - Disconnection events
- `[TEACHER]` - Teacher actions
- `[STUDENT]` - Student actions
- `[TIMER]` - Timer events
- `[SESSION]` - Session state changes
- `[CLOSE_QUESTION]` - Question closing (verbose debug logs)
- `[SEND_QUESTION]` - Question delivery

All logs use `print()` with some using `flush=True` for immediate output.

---

## 5.5 Performance Considerations

### Database Query Optimization

**select_related / prefetch_related Usage:**

```python
# quizzes/views.py:100
question = Question.objects.select_related("topic").prefetch_related("options").get(pk=pk)

# sockets/managers/questions.py:70
question = Question.objects.prefetch_related("options").get(id=question_id)
```

### Async/Sync Bridge

Django ORM is synchronous. Socket.IO server uses `asyncio.to_thread()` to avoid blocking:

```python
# sockets/managers/questions.py
async def load_question(question_id: int):
    return await asyncio.to_thread(_load_question_sync, question_id)
```

### Caching

**Correct Option Caching:**

To avoid database query during timer expiration:
```python
# Cached in session during send_question()
session["current_correct_option"] = question_data.get("correct_option_id")

# Used in close_question() without DB query
correct_option_id = session.get("current_correct_option")
```

### Session Storage

Sessions are stored in-memory (`active_sessions` dict). This means:
- Fast access (no DB queries for session data)
- Data lost on server restart
- Single-server only (no horizontal scaling without Redis)

---

## 5.6 Security Considerations

### Identified Issues

1. **Hardcoded Secrets:** SECRET_KEY and DB password in settings.py
2. **No Socket Authentication:** Any client can emit teacher events
3. **No Rate Limiting:** No protection against event flooding
4. **Debug Mode:** DEBUG=True exposes detailed errors
5. **CORS Wildcard:** Socket.IO allows all origins

### Recommendations

1. Use environment variables for secrets
2. Implement JWT validation for Socket.IO connections
3. Add rate limiting for API and socket events
4. Disable DEBUG in production
5. Restrict CORS to specific origins

---

## 5.7 Testing

**Test Files Present:**
- `users/tests.py` (empty)
- `quizzes/tests.py` (empty)
- `live/tests.py` (empty)

**Assumption:** Unit tests are not yet implemented.

---

## 5.8 Deployment

### ASGI Server

**Recommended:** uvicorn

```bash
uvicorn backend.asgi:application --host 0.0.0.0 --port 8000
```

### ASGI Application Structure

```python
# backend/asgi.py
async def application(scope, receive, send):
    if scope["type"] == "http":
        if path.startswith("/socket.io"):
            await sio.handle_request(scope, receive, send)
        else:
            await django_asgi_app(scope, receive, send)
    elif scope["type"] == "websocket":
        await sio.handle_request(scope, receive, send)
```

---

# Appendix A: File Structure

```
LiveQuizApi/
├── backend/
│   ├── __init__.py
│   ├── settings.py          # Django configuration
│   ├── urls.py              # URL routing + OpenAPI schema
│   ├── asgi.py              # ASGI entry point
│   ├── wsgi.py              # WSGI entry point
│   └── responses.py         # StandardResponseMixin
├── users/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # User model
│   ├── views.py             # LoginAPIView
│   ├── serializers.py       # LoginSerializer
│   ├── admin.py
│   ├── tests.py
│   └── migrations/
├── quizzes/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # Topic, Question, AnswerOption
│   ├── views.py             # CRUD views
│   ├── serializers.py       # All serializers
│   ├── admin.py
│   ├── tests.py
│   └── migrations/
├── live/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # (empty)
│   ├── views.py             # (empty)
│   ├── admin.py
│   └── tests.py
├── sockets/
│   ├── __init__.py
│   ├── server.py            # Main Socket.IO server (872 lines)
│   ├── managers/
│   │   ├── __init__.py
│   │   ├── sessions.py      # SessionManager
│   │   ├── questions.py     # QuestionManager
│   │   └── ranking.py       # RankingManager
│   └── utils/
│       ├── __init__.py
│       └── time.py          # TimeUtils
├── scripts/
│   └── create_user.py       # CLI user creation
├── manage.py
├── requirements.txt
└── README.md
```

---

# Appendix B: Quick Reference

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/login/ | User login |
| GET | /api/quizzes/ | List topics |
| POST | /api/quizzes/ | Create topic |
| GET | /api/quizzes/{id}/ | Get topic |
| PUT | /api/quizzes/{id}/ | Update topic |
| PATCH | /api/quizzes/{id}/ | Partial update |
| DELETE | /api/quizzes/{id}/ | Delete topic |
| POST | /api/topics/{id}/questions/ | Create question |
| PATCH | /api/questions/{id}/ | Update question |
| DELETE | /api/questions/{id}/delete/ | Delete question |
| DELETE | /api/options/{id}/delete/ | Delete option |

## Socket Events (Client → Server)

| Event | Sender | Description |
|-------|--------|-------------|
| teacher:create_session | Teacher | Create quiz session |
| teacher:start_session | Teacher | Start quiz |
| teacher:next_question | Teacher | Next question |
| teacher:finish_session | Teacher | End quiz |
| student:join | Student | Join session |
| student:answer | Student | Submit answer |
| student:leave | Student | Leave session |
| get_session_state | Any | Get session info |

## Socket Events (Server → Client)

| Event | Recipients | Description |
|-------|------------|-------------|
| teacher:session_created | Teacher | Session ready |
| session:started | Teacher | Quiz started |
| session:state | Teacher | Student list update |
| session:question | Students | New question |
| session:question_closed | All | Question ended |
| session:answer_count | Teacher | Answer progress |
| session:ranking | Teacher | Leaderboard |
| session:timer_expired | All | Time's up |
| session:ended | Students | Teacher left |
| student:joined | Student | Join confirmed |
| student:answer_received | Student | Answer confirmed |
| answer_result | Student | Score result |
| quiz_finished | All | Final results |
| error | Sender | Error message |

---

*End of Technical Documentation*
