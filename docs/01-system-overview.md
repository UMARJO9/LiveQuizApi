# 1. System Overview

[← Back to Index](./README.md)

---

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

---

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

---

## 1.3 Django Applications

| App | Purpose | Models | Status |
|-----|---------|--------|--------|
| **users** | User authentication and profile management | User | Active |
| **quizzes** | Quiz content management (topics, questions, options) | Topic, Question, AnswerOption | Active |
| **live** | Placeholder for future live session persistence | None | Empty |

---

## 1.4 Main Functional Domains

### 1.4.1 User Management (users app)

**Location:** `users/`

**Responsibilities:**
- Custom user model with email-based authentication
- JWT token generation and validation
- Profile fields: first_name, last_name, specialty

**Key Files:**
- `models.py` - User model with UserManager
- `views.py` - LoginAPIView
- `serializers.py` - LoginSerializer

### 1.4.2 Quiz Content Management (quizzes app)

**Location:** `quizzes/`

**Responsibilities:**
- **Topics**: Quiz containers owned by teachers
- **Questions**: Multiple-choice questions with ordering
- **Answer Options**: Exactly 4 options per question, at least 1 correct

**Key Files:**
- `models.py` - Topic, Question, AnswerOption
- `views.py` - CRUD views for all models
- `serializers.py` - Validation and serialization

### 1.4.3 Live Quiz Sessions (sockets module)

**Location:** `sockets/`

**Responsibilities:**
- Real-time quiz hosting via Socket.IO
- Session management with 4-character codes (e.g., "AB12")
- Question delivery with countdown timers
- Answer collection and scoring
- Leaderboard with tie support

**Key Files:**
- `server.py` - Main event handlers (872 lines)
- `managers/sessions.py` - SessionManager
- `managers/questions.py` - QuestionManager
- `managers/ranking.py` - RankingManager
- `utils/time.py` - TimeUtils

---

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

**Why this pattern?**
- Django ORM is synchronous
- Socket.IO server runs on asyncio event loop
- `asyncio.to_thread()` runs sync code in a thread pool
- Prevents blocking other socket events during DB queries

---

## 1.6 File Structure

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
├── docs/                    # Documentation
├── manage.py
├── requirements.txt
└── README.md
```

---

[Next: API Documentation →](./02-api-documentation.md)
