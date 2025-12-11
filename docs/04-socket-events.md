# 4. Socket.IO Events

[← Back to Index](./README.md) | [← Database Schema](./03-database-schema.md)

---

## 4.1 Server Configuration

**Location:** `sockets/server.py:44`

```python
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
)
```

| Setting | Value | Description |
|---------|-------|-------------|
| Path | `/socket.io/` | WebSocket endpoint |
| Namespace | `/` (default) | Single namespace |
| Transport | WebSocket + HTTP polling | Auto-negotiated |
| CORS | `*` (all origins) | Development setting |

---

## 4.2 In-Memory Data Structures

### active_sessions

**Location:** `sockets/managers/sessions.py:39`

```python
active_sessions: dict[str, SessionData] = {}
```

**SessionData TypedDict:**

```python
{
    "session_id": str,              # 4-char code (e.g., "AB12")
    "topic_id": int,                # FK to Topic
    "teacher_sid": str,             # Teacher's socket ID
    "time_per_question": int,       # Seconds per question
    "question_queue": list[int],    # Remaining question IDs (shuffled)
    "current_question": int | None, # Current question ID
    "current_correct_option": int | None,  # Cached correct option ID
    "question_started_at": datetime | None,
    "question_deadline": datetime | None,
    "answers": dict[str, int],      # {student_sid: option_id}
    "students": dict[str, StudentData],  # {sid: {name, score}}
    "stage": str,                   # "waiting" | "running" | "finished"
}
```

**StudentData TypedDict:**

```python
{
    "name": str,   # Display name
    "score": int,  # Cumulative score
}
```

### question_timers

**Location:** `sockets/server.py:40`

```python
question_timers: dict[str, asyncio.Task] = {}
# {session_id: Timer Task}
```

Stores asyncio tasks that auto-close questions after timeout.

---

## 4.3 Session Stages

| Stage | Value | Description |
|-------|-------|-------------|
| WAITING | `"waiting"` | Session created, accepting students |
| RUNNING | `"running"` | Quiz in progress |
| FINISHED | `"finished"` | Quiz completed |

---

## 4.4 Connection Events

### connect

**Direction:** Client → Server

**Location:** `sockets/server.py:337`

**Description:** Fired when any client connects to the Socket.IO server.

**Client Example:**
```javascript
const socket = io("http://localhost:8000", {
    auth: { token: "jwt_token" }
});
```

**Server Behavior:**
- Logs connection with socket ID
- Does NOT assign role or validate auth
- Waits for join event to identify user type

**Assumption:** JWT validation for socket connections is not implemented.

---

### disconnect

**Direction:** Client → Server (automatic)

**Location:** `sockets/server.py:354`

**Description:** Fired when a client disconnects.

**Server Behavior:**

**For Students:**
1. Find session by student SID
2. Remove student from `session["students"]`
3. Emit `session:state` to teacher with updated list

**For Teachers:**
1. Find session by teacher SID
2. Emit `session:ended` to all students
3. Delete session from `active_sessions`
4. Cancel any running timer

---

## 4.5 Teacher Events

### teacher:create_session

**Direction:** Client → Server

**Location:** `sockets/server.py:402`

**Description:** Create a new quiz session for a topic.

#### Payload

```json
{
  "topic_id": 1
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| topic_id | integer | Yes | Topic/quiz ID to use |

#### Processing Flow

1. Validate `topic_id` provided
2. Load topic from DB (title, description, question_timer)
3. Load all question IDs for topic (ordered by order_index)
4. Shuffle question IDs
5. Generate unique 4-character session code (A-Z, 0-9)
6. Create session object in `active_sessions`
7. Add teacher to room `room_{session_id}`
8. Emit `teacher:session_created`

#### Response Event

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

| Error | Condition |
|-------|-----------|
| `"topic_id is required"` | Missing topic_id |
| `"Topic not found"` | Invalid topic_id |
| `"No questions found for topic"` | Topic has no questions |

---

### teacher:start_session

**Direction:** Client → Server

**Location:** `sockets/server.py:471`

**Description:** Start the quiz, sending the first question.

#### Payload

```json
{
  "session_id": "AB12"
}
```

#### Processing Flow

1. Validate session exists
2. Verify sender is the teacher (SID match)
3. Check stage is "waiting"
4. Check at least 1 student joined
5. Set stage to "running"
6. Pop first question from queue
7. Load question + options from DB
8. Cache `correct_option_id` in session
9. Emit `session:question` to room
10. Start auto-close timer
11. Emit `session:started` to teacher

#### Response Events

**session:started** → Teacher

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

**Note:** `is_correct` is NOT included in options sent to students.

#### Errors

| Error | Condition |
|-------|-----------|
| `"session_id is required"` | Missing session_id |
| `"Session not found"` | Invalid session_id |
| `"Not authorized"` | SID doesn't match teacher |
| `"Session already started"` | Stage != "waiting" |
| `"No students in session"` | Empty students dict |

---

### teacher:next_question

**Direction:** Client → Server

**Location:** `sockets/server.py:532`

**Description:** Advance to the next question (closes current first).

#### Payload

```json
{
  "session_id": "AB12"
}
```

#### Processing Flow

1. Validate session and teacher
2. Check stage is "running"
3. Call `close_question()` to process current answers
4. If questions remain: send next question
5. If no questions: call `finish_session()`

#### Events from close_question()

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

### teacher:finish_session

**Direction:** Client → Server

**Location:** `sockets/server.py:583`

**Description:** Manually end the quiz early.

#### Payload

```json
{
  "session_id": "AB12"
}
```

#### Processing Flow

1. Validate session and teacher
2. If running, close current question
3. Set stage to "finished"
4. Build final results
5. Emit `quiz_finished` to all

#### Response Event

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

## 4.6 Student Events

### student:join

**Direction:** Client → Server

**Location:** `sockets/server.py:625`

**Description:** Join a quiz session using the 4-character code.

#### Payload

```json
{
  "session_id": "AB12",
  "name": "Alice"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string | Yes | 4-char session code |
| name | string | Yes | Display name (whitespace trimmed) |

#### Validation

- Session must exist
- Stage must be "waiting" (cannot join after start)
- Name must not be empty after trim

#### Processing Flow

1. Validate inputs
2. Add student to `session["students"]` with score=0
3. Add student to room `room_{session_id}`
4. Emit `student:joined` to student
5. Emit `session:state` to teacher

#### Response Events

**student:joined** → Student

```json
{
  "session_id": "AB12",
  "name": "Alice",
  "message": "Successfully joined the quiz"
}
```

**session:state** → Teacher

```json
{
  "students": [
    {"sid": "abc123", "name": "Alice", "score": 0},
    {"sid": "def456", "name": "Bob", "score": 0}
  ]
}
```

#### Errors

| Error | Condition |
|-------|-----------|
| `"session_id is required"` | Missing session_id |
| `"name is required"` | Empty name |
| `"Session not found"` | Invalid code |
| `"Cannot join - quiz already started"` | Stage != "waiting" |

---

### student:answer

**Direction:** Client → Server

**Location:** `sockets/server.py:702`

**Description:** Submit an answer to the current question.

#### Payload

```json
{
  "session_id": "AB12",
  "option_id": 18
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string | Yes | Session code |
| option_id | integer | Yes | Selected option ID |

#### Validation

1. Session exists
2. Student is in this session
3. Stage is "running"
4. Question deadline not expired
5. Student hasn't already answered

#### Processing Flow

1. Validate all conditions
2. Record answer in `session["answers"]`
3. Emit `student:answer_received` to student
4. Emit `session:answer_count` to teacher
5. If all students answered → auto close question

#### Response Events

**student:answer_received** → Student

```json
{
  "message": "Answer received"
}
```

**session:answer_count** → Teacher

```json
{
  "answered": 5,
  "total": 10
}
```

#### Auto-Close Trigger

If `len(answers) == len(students)`, question closes immediately without waiting for timer.

#### Errors

| Error | Condition |
|-------|-----------|
| `"session_id is required"` | Missing |
| `"option_id is required"` | Missing |
| `"Session not found"` | Invalid session |
| `"Not in this session"` | SID not in students |
| `"Cannot answer - time expired or quiz not running"` | Invalid state |
| `"Already answered this question"` | Duplicate answer |

---

### student:leave

**Direction:** Client → Server

**Location:** `sockets/server.py:793`

**Description:** Voluntarily leave the quiz session.

#### Payload

```json
{
  "session_id": "AB12"
}
```

#### Response Events

**student:left** → Student

```json
{
  "message": "Left the quiz"
}
```

**session:state** → Teacher (updated list)

---

## 4.7 Utility Events

### get_session_state

**Direction:** Client → Server

**Location:** `sockets/server.py:840`

**Description:** Request current session state (for debugging/reconnection).

#### Payload

```json
{
  "session_id": "AB12"
}
```

#### Response

**session:state** → Requester

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

## 4.8 Server-Emitted Events Summary

| Event | Recipients | When |
|-------|------------|------|
| `teacher:session_created` | Teacher | After create_session |
| `session:started` | Teacher | After start_session |
| `session:state` | Teacher | Student joins/leaves |
| `session:question` | Room (students) | New question |
| `session:question_closed` | Teacher + Room | Question ends |
| `session:answer_count` | Teacher | Answer received |
| `session:ranking` | Teacher | After question closes |
| `session:timer_expired` | Teacher + Room | Timer runs out |
| `session:ended` | Room | Teacher disconnects |
| `student:joined` | Student | Join confirmed |
| `student:answer_received` | Student | Answer confirmed |
| `student:left` | Student | Leave confirmed |
| `answer_result` | Student | Score after question |
| `ranking` | Teacher | After question (legacy) |
| `quiz_finished` | Teacher + Room | Quiz ends |
| `error` | Sender | Validation failure |

---

## 4.9 Timer Mechanism

### Starting Timer

**Location:** `sockets/server.py:116`

```python
def start_question_timer(session_id: str, timeout: int) -> None:
    cancel_question_timer(session_id)  # Cancel existing
    task = asyncio.create_task(question_timer_task(session_id, timeout))
    question_timers[session_id] = task
```

### Timer Task

**Location:** `sockets/server.py:63`

```python
async def question_timer_task(session_id: str, timeout: int) -> None:
    await asyncio.sleep(timeout)
    # Emit session:timer_expired to all
    # Call close_question(from_timer=True)
```

### Timer Cancellation

Timers are cancelled when:
- Teacher requests next question
- All students answer before timeout
- Teacher finishes session manually
- Teacher disconnects

**NOT cancelled** when called from timer itself (`from_timer=True`).

---

## 4.10 Room Architecture

```
Room: room_{session_id}

Members:
├── Teacher (sid) - Also receives direct events
└── Students
    ├── Student 1 (sid)
    ├── Student 2 (sid)
    └── Student N (sid)

Usage:
- sio.emit("event", data, room=room)     → All students
- sio.emit("event", data, to=teacher_sid) → Teacher only
- sio.emit("event", data, to=student_sid) → Specific student
```

---

## 4.11 Scoring System

| Event | Points |
|-------|--------|
| Correct answer | +20 |
| Incorrect answer | 0 |
| No answer (timeout) | 0 |

**Constant:** `QuestionManager.POINTS_CORRECT = 20`

**Location:** `sockets/managers/questions.py:95`

### Ranking with Ties

```python
# Players with same score get same position
# Example:
# Alice: 120 → position 1
# Bob:   120 → position 1
# Carol:  80 → position 2  (not 3!)
```

---

## 4.12 Complete Flow Example

```
1. Teacher connects
   └─► Server logs connection

2. Teacher emits teacher:create_session {topic_id: 1}
   ├─► Server loads topic + questions
   ├─► Server generates code "AB12"
   └─► Server emits teacher:session_created to teacher

3. Student connects
   └─► Server logs connection

4. Student emits student:join {session_id: "AB12", name: "Alice"}
   ├─► Server adds student to session
   ├─► Server emits student:joined to student
   └─► Server emits session:state to teacher

5. Teacher emits teacher:start_session {session_id: "AB12"}
   ├─► Server sets stage = "running"
   ├─► Server loads question #1
   ├─► Server starts 20s timer
   ├─► Server emits session:started to teacher
   └─► Server emits session:question to room

6. Student emits student:answer {session_id: "AB12", option_id: 18}
   ├─► Server records answer
   ├─► Server emits student:answer_received to student
   └─► Server emits session:answer_count to teacher

7. Timer expires (or all answered)
   ├─► Server emits session:timer_expired (if timeout)
   ├─► Server calculates scores
   ├─► Server emits answer_result to each student
   ├─► Server emits session:question_closed to all
   └─► Server emits session:ranking to teacher

8. Teacher emits teacher:next_question
   └─► Repeat steps 5-7 until no questions

9. No more questions
   ├─► Server sets stage = "finished"
   └─► Server emits quiz_finished to all
```

---

[Next: Cross-Cutting Concerns →](./05-cross-cutting-concerns.md)
