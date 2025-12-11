# 5. Cross-Cutting Concerns

[← Back to Index](./README.md) | [← Socket.IO Events](./04-socket-events.md)

---

## 5.1 Authentication

### REST API Authentication

**Method:** JWT (JSON Web Token)

**Library:** djangorestframework-simplejwt 5.5.1

**Location:** `backend/settings.py:144-163`

#### Configuration

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

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

#### Token Usage

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Token Properties

| Property | Value |
|----------|-------|
| Type | Access Token |
| Lifetime | 30 days |
| Algorithm | HS256 |
| Signing Key | Django SECRET_KEY |

### Socket.IO Authentication

**Status:** NOT IMPLEMENTED

**Current Behavior:**
```javascript
// Client sends auth data
const socket = io("http://localhost:8000", {
    auth: { token: "jwt_token" }
});
```

```python
# Server logs but does NOT validate
@sio.event
async def connect(sid, environ, auth=None):
    if auth:
        print(f"Auth data received: {auth.get('token', 'N/A')[:20]}...")
```

**Security Risk:** Any client can emit teacher events without authentication.

**Recommendation:** Implement JWT validation in `connect` handler and store user info in socket session.

---

## 5.2 Configuration

### Settings Location

`backend/settings.py`

### Critical Settings

| Setting | Value | Security Note |
|---------|-------|---------------|
| SECRET_KEY | Hardcoded | Use env var in production |
| DEBUG | True | Set False in production |
| ALLOWED_HOSTS | [] | Configure for production |
| AUTH_USER_MODEL | "users.User" | Custom user model |
| APPEND_SLASH | False | URL trailing slash optional |

### Database Configuration

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'live_quiz',
        'USER': 'postgres',
        'PASSWORD': '123456',  # HARDCODED - use env var!
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

### CORS Configuration

**Location:** `backend/settings.py:58-68`

```python
CORS_ALLOW_ALL_ORIGINS = True  # Development only!

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.43.20:5173"  # BUG: Missing comma
    "http://192.168.43.20:5174"  # Concatenated with above!
]

CORS_ALLOW_CREDENTIALS = True
```

**Bug:** Lines 65-66 have a missing comma, causing URL concatenation:
```python
"http://192.168.43.20:5173http://192.168.43.20:5174"
```

### Socket.IO CORS

```python
sio = socketio.AsyncServer(
    cors_allowed_origins="*",  # All origins allowed
)
```

### Installed Apps

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'users',
    'quizzes',
    'live',
]
```

### Middleware

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]
```

---

## 5.3 Error Handling

### REST API Errors

**Standard Response Wrapper:** `backend/responses.py`

All responses wrapped in:
```json
{
  "success": false,
  "code": 400,
  "message": "Error message",
  "result": null
}
```

**Message Extraction Logic:**
```python
def _extract_message(data, success):
    # Try keys: "message", "detail", "error"
    # Fall back to "Success" or "Error"
```

### DRF Exception Handling

Default DRF exception handler is used (not customized).

Common error formats:
```json
// Validation error
{"field_name": ["Error message"]}

// Authentication error
{"detail": "Authentication credentials were not provided."}

// Permission error
{"detail": "You do not have permission to perform this action."}
```

### Socket.IO Errors

All errors emit `error` event to sender:

```python
await sio.emit("error", {"message": "Error description"}, to=sid)
```

**Common Error Patterns:**

| Error | Event/Endpoint |
|-------|----------------|
| `"topic_id is required"` | teacher:create_session |
| `"Session not found"` | All session events |
| `"Not authorized"` | Teacher events (SID mismatch) |
| `"Cannot join - quiz already started"` | student:join |
| `"Already answered this question"` | student:answer |
| `"Cannot answer - time expired..."` | student:answer |

---

## 5.4 Logging

### Socket.IO Server Logging

```python
sio = socketio.AsyncServer(
    logger=True,
    engineio_logger=True,
)
```

### Custom Log Prefixes

| Prefix | Description |
|--------|-------------|
| `[CONNECT]` | Connection events |
| `[DISCONNECT]` | Disconnection events |
| `[TEACHER]` | Teacher actions |
| `[STUDENT]` | Student actions |
| `[TIMER]` | Timer start/cancel/expire |
| `[SESSION]` | Session state changes |
| `[CLOSE_QUESTION]` | Question closing (verbose) |
| `[SEND_QUESTION]` | Question delivery |

### Example Log Output

```
[CONNECT] Client connected: abc123
[TEACHER] Create session request from abc123: {'topic_id': 1}
[TEACHER] Session created: AB12
[STUDENT] Join request from def456: {'session_id': 'AB12', 'name': 'Alice'}
[STUDENT] Alice joined session AB12
[TEACHER] Start session request from abc123
[TIMER] Started 20s timer for session AB12
[STUDENT] Answer from def456: {'session_id': 'AB12', 'option_id': 18}
[STUDENT] Answer recorded: 1/1
[SESSION] All students answered, closing question
[CLOSE_QUESTION] Starting close_question for session AB12
[CLOSE_QUESTION] Done!
```

### Flush for Debug

Some critical logs use `flush=True`:
```python
print(f"[CLOSE_QUESTION] Starting...", flush=True)
```

---

## 5.5 Performance Considerations

### Database Query Optimization

**select_related Usage:**

```python
# quizzes/views.py:100
question = Question.objects.select_related("topic").prefetch_related("options").get(pk=pk)
```

**prefetch_related Usage:**

```python
# sockets/managers/questions.py:70
question = Question.objects.prefetch_related("options").get(id=question_id)
```

### Async/Sync Bridge

Django ORM is synchronous. Socket.IO uses `asyncio.to_thread()`:

```python
# sockets/managers/questions.py
async def load_question(question_id: int):
    return await asyncio.to_thread(_load_question_sync, question_id)

def _load_question_sync(question_id: int):
    # Synchronous Django ORM query
    return Question.objects.prefetch_related("options").get(id=question_id)
```

**Benefits:**
- Doesn't block event loop
- Other socket events can be processed
- Uses thread pool for DB queries

### Caching Strategy

**Correct Option Caching:**

```python
# During send_question() - cache in session
session["current_correct_option"] = question_data.get("correct_option_id")

# During close_question() - use cache, no DB query
correct_option_id = session.get("current_correct_option")
```

**Why?** Timer expiration previously caused DB query race conditions.

### In-Memory Session Storage

**Pros:**
- Fast access (no DB queries for session data)
- Simple implementation

**Cons:**
- Data lost on server restart
- Single-server only (no horizontal scaling)
- Memory grows with active sessions

**Production Recommendation:** Use Redis for session storage.

---

## 5.6 Security Considerations

### Identified Vulnerabilities

| Issue | Severity | Location | Description |
|-------|----------|----------|-------------|
| Hardcoded SECRET_KEY | High | settings.py:24 | Exposed in source control |
| Hardcoded DB password | High | settings.py:96 | Exposed in source control |
| No Socket.IO auth | High | server.py | Any client can impersonate teacher |
| DEBUG=True | Medium | settings.py:27 | Exposes detailed errors |
| CORS wildcard | Medium | server.py:47 | Socket.IO allows all origins |
| No rate limiting | Medium | - | Vulnerable to flooding |

### Recommendations

1. **Use Environment Variables:**
```python
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DATABASES['default']['PASSWORD'] = os.environ.get('DB_PASSWORD')
```

2. **Implement Socket.IO Auth:**
```python
@sio.event
async def connect(sid, environ, auth=None):
    if not auth or 'token' not in auth:
        raise ConnectionRefusedError('Authentication required')

    try:
        token = AccessToken(auth['token'])
        user_id = token['user_id']
        # Store user_id in socket session
        await sio.save_session(sid, {'user_id': user_id})
    except:
        raise ConnectionRefusedError('Invalid token')
```

3. **Production Settings:**
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
CORS_ALLOWED_ORIGINS = ['https://your-frontend.com']
```

4. **Add Rate Limiting:**
```python
# Use django-ratelimit for API
# Implement custom rate limiting for sockets
```

---

## 5.7 Testing

### Current State

All test files are empty:
- `users/tests.py`
- `quizzes/tests.py`
- `live/tests.py`

### Recommended Test Structure

```
tests/
├── test_api/
│   ├── test_auth.py
│   ├── test_topics.py
│   └── test_questions.py
├── test_sockets/
│   ├── test_teacher_events.py
│   ├── test_student_events.py
│   └── test_timer.py
└── test_models/
    ├── test_user.py
    └── test_quiz.py
```

### Example Test Cases

```python
# API Tests
def test_login_with_valid_credentials()
def test_login_with_invalid_credentials()
def test_create_topic_authenticated()
def test_create_topic_unauthenticated()
def test_create_question_with_4_options()
def test_create_question_with_3_options_fails()

# Socket Tests
async def test_create_session_flow()
async def test_student_join_waiting_session()
async def test_student_join_started_session_fails()
async def test_answer_before_deadline()
async def test_answer_after_deadline_fails()
async def test_timer_auto_close()
```

---

## 5.8 Deployment

### ASGI Server

**Recommended:** uvicorn

```bash
# Development
uvicorn backend.asgi:application --host 0.0.0.0 --port 8000 --reload

# Production
uvicorn backend.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

### ASGI Application

**Location:** `backend/asgi.py`

```python
async def application(scope, receive, send):
    if scope["type"] == "http":
        if path.startswith("/socket.io"):
            await sio.handle_request(scope, receive, send)
        else:
            await django_asgi_app(scope, receive, send)
    elif scope["type"] == "websocket":
        await sio.handle_request(scope, receive, send)
```

### Production Checklist

- [ ] Set DEBUG=False
- [ ] Use environment variables for secrets
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up HTTPS
- [ ] Configure proper CORS origins
- [ ] Implement Socket.IO authentication
- [ ] Add rate limiting
- [ ] Set up Redis for session storage
- [ ] Configure logging to file/service
- [ ] Set up monitoring
- [ ] Database connection pooling
- [ ] Static file serving (nginx/CDN)

---

## 5.9 Dependencies

**File:** `requirements.txt`

```
Django==5.2.8
djangorestframework>=3.15,<3.16
djangorestframework-simplejwt==5.5.1
psycopg2-binary>=2.9
django-cors-headers>=4.3

# Socket.IO for real-time quiz functionality
python-socketio>=5.10
aiohttp>=3.9

# ASGI server
uvicorn[standard]>=0.27
```

### Version Constraints

| Package | Min | Max | Purpose |
|---------|-----|-----|---------|
| Django | 5.2.8 | 5.2.8 | Web framework |
| DRF | 3.15 | 3.16 | REST API |
| simplejwt | 5.5.1 | 5.5.1 | JWT auth |
| psycopg2 | 2.9 | - | PostgreSQL driver |
| cors-headers | 4.3 | - | CORS support |
| python-socketio | 5.10 | - | Real-time |
| uvicorn | 0.27 | - | ASGI server |

---

[← Back to Index](./README.md)
