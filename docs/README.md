# LiveQuizApi - Technical Documentation

**Version:** 1.0.0
**Generated:** December 2025
**System Type:** Real-time Quiz Platform (Kahoot-like)

---

## Documentation Index

| Document | Description |
|----------|-------------|
| [1. System Overview](./01-system-overview.md) | Architecture, tech stack, apps, high-level flows |
| [2. API Documentation](./02-api-documentation.md) | REST endpoints, request/response schemas |
| [3. Database Schema](./03-database-schema.md) | Models, fields, relationships, migrations |
| [4. Socket.IO Events](./04-socket-events.md) | Real-time events, payloads, flows |
| [5. Cross-Cutting Concerns](./05-cross-cutting-concerns.md) | Auth, config, security, performance |

---

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL
- Node.js (for frontend)

### Installation

```bash
# Clone repository
git clone https://github.com/UMARJO9/LiveQuizApi.git
cd LiveQuizApi

# Install dependencies
pip install -r requirements.txt

# Configure database
# Edit backend/settings.py with your PostgreSQL credentials

# Run migrations
python manage.py migrate

# Create superuser
python scripts/create_user.py

# Start server
uvicorn backend.asgi:application --host 0.0.0.0 --port 8000
```

### Accessing the System

| URL | Description |
|-----|-------------|
| http://localhost:8000/api/docs/ | Swagger UI |
| http://localhost:8000/api/schema/ | OpenAPI JSON |
| ws://localhost:8000/socket.io/ | Socket.IO endpoint |

---

## System Summary

### What is LiveQuizApi?

LiveQuizApi is a real-time quiz platform similar to Kahoot. Teachers create quizzes with multiple-choice questions, then host live sessions where students join using a 4-character code and answer questions in real-time.

### Key Features

- **JWT Authentication** - Secure teacher login
- **Quiz Management** - CRUD operations for topics, questions, options
- **Live Sessions** - Real-time quiz hosting via Socket.IO
- **Auto-timing** - Configurable question timers with auto-close
- **Scoring** - 20 points per correct answer
- **Leaderboards** - Rankings with tie support

### Architecture Overview

```
┌─────────────┐     ┌─────────────┐
│   Teacher   │     │   Students  │
│   Client    │     │   Clients   │
└──────┬──────┘     └──────┬──────┘
       │ HTTP/WS           │ WS
       └─────────┬─────────┘
                 │
        ┌────────▼────────┐
        │   ASGI Server   │
        │    (uvicorn)    │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐  ┌─────▼─────┐  ┌───▼───┐
│ Django│  │ Socket.IO │  │In-Mem │
│  REST │  │  Server   │  │Sessions│
└───┬───┘  └─────┬─────┘  └───────┘
    │            │
    └─────┬──────┘
          │
   ┌──────▼──────┐
   │ PostgreSQL  │
   └─────────────┘
```

---

## API Quick Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/auth/login/ | No | User login |
| GET | /api/quizzes/ | JWT | List topics |
| POST | /api/quizzes/ | JWT | Create topic |
| GET | /api/quizzes/{id}/ | JWT | Get topic |
| PUT | /api/quizzes/{id}/ | JWT | Update topic |
| DELETE | /api/quizzes/{id}/ | JWT | Delete topic |
| POST | /api/topics/{id}/questions/ | JWT | Create question |
| PATCH | /api/questions/{id}/ | JWT | Update question |
| DELETE | /api/questions/{id}/delete/ | JWT | Delete question |

---

## Socket Events Quick Reference

### Client → Server

| Event | Sender | Description |
|-------|--------|-------------|
| `teacher:create_session` | Teacher | Create quiz session |
| `teacher:start_session` | Teacher | Start quiz |
| `teacher:next_question` | Teacher | Next question |
| `teacher:finish_session` | Teacher | End quiz |
| `student:join` | Student | Join session |
| `student:answer` | Student | Submit answer |

### Server → Client

| Event | Recipients | Description |
|-------|------------|-------------|
| `teacher:session_created` | Teacher | Session ready with code |
| `session:question` | Students | New question |
| `answer_result` | Student | Score after question |
| `quiz_finished` | All | Final results |

---

## File Structure

```
LiveQuizApi/
├── backend/           # Django config
├── users/             # User model & auth
├── quizzes/           # Topics, questions, options
├── live/              # (placeholder)
├── sockets/           # Socket.IO server
│   ├── server.py      # Event handlers
│   └── managers/      # Session, Question, Ranking
├── docs/              # This documentation
├── requirements.txt
└── manage.py
```

---

## Contributing

1. Create feature branch from `main`
2. Make changes with tests
3. Submit pull request

## License

[Add license information]
