# 3. Database Schema

[← Back to Index](./README.md) | [← API Documentation](./02-api-documentation.md)

---

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
```

---

## 3.2 Model: User

**Table:** `users_user`

**Location:** `users/models.py:30`

**Description:** Custom user model for teacher authentication. Uses email as the primary identifier instead of username. Extends Django's AbstractBaseUser and PermissionsMixin.

### Fields

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| id | BigAutoField | Auto | Auto-increment | PK | Primary key |
| email | EmailField | Yes | - | Unique, max 254 | Login identifier |
| password | CharField | Yes | - | max 128 | Hashed password |
| first_name | CharField | No | null | max 150, blank | User's first name |
| last_name | CharField | No | null | max 150, blank | User's last name |
| specialty | CharField | No | null | max 255, blank | Professional specialty |
| is_active | BooleanField | No | True | - | Account active status |
| is_staff | BooleanField | No | False | - | Django admin access |
| is_superuser | BooleanField | No | False | - | All permissions granted |
| last_login | DateTimeField | No | null | blank | Last login timestamp |

### Relationships

| Relation | Type | Related Model | Related Name | On Delete |
|----------|------|---------------|--------------|-----------|
| groups | M:N | auth.Group | user_set | - |
| user_permissions | M:N | auth.Permission | user_set | - |
| topics | 1:N (reverse) | Topic | topics | CASCADE |

### UserManager Methods

```python
def create_user(self, email, password=None, first_name='', last_name='', specialty=''):
    """Create a regular user with hashed password."""

def create_superuser(self, email, password=None):
    """Create a superuser with is_staff=True, is_superuser=True."""
```

### Business Rules

- `email` is the USERNAME_FIELD for authentication
- Password is hashed using Django's password hashers
- Email is normalized (lowercase domain) on creation
- Error raised if email is not provided: "Email не указан" (Russian)

### Used in APIs

- **POST /api/auth/login/** - Authentication
- All other APIs via `request.user`

### Used in Socket Events

- Indirectly via Topic ownership validation

### SQL Definition

```sql
CREATE TABLE users_user (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(254) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    specialty VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE
);
```

---

## 3.3 Model: Topic

**Table:** `quizzes_topic`

**Location:** `quizzes/models.py:5`

**Description:** Represents a quiz/topic container owned by a teacher. Contains configuration for quiz sessions including time per question.

### Fields

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| id | BigAutoField | Auto | Auto-increment | PK | Primary key |
| teacher_id | BigIntegerField | Yes | - | FK to User | Owner user ID |
| title | CharField | Yes | - | max 255 | Quiz title |
| description | TextField | No | null | blank | Quiz description |
| question_timer | IntegerField | No | 20 | - | Seconds per question |
| created_at | DateTimeField | Auto | now | auto_now_add | Creation timestamp |
| updated_at | DateTimeField | Auto | now | auto_now | Last modification |

### Relationships

| Relation | Type | Related Model | Related Name | On Delete |
|----------|------|---------------|--------------|-----------|
| teacher | FK | User | topics | CASCADE |
| questions | 1:N (reverse) | Question | questions | CASCADE |

### Business Rules

- Deleting a User cascades to delete all their Topics
- Deleting a Topic cascades to all Questions and AnswerOptions
- `question_timer` defaults to 20 seconds
- `created_at` is set automatically on creation and never changes
- `updated_at` is updated automatically on every save

### Used in APIs

- **GET /api/quizzes/** - List user's topics
- **POST /api/quizzes/** - Create topic
- **GET/PUT/PATCH/DELETE /api/quizzes/{id}/** - Topic operations

### Used in Socket Events

- **teacher:create_session** - Loads topic data including `question_timer`

### SQL Definition

```sql
CREATE TABLE quizzes_topic (
    id BIGSERIAL PRIMARY KEY,
    teacher_id BIGINT NOT NULL REFERENCES users_user(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    question_timer INTEGER DEFAULT 20,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX quizzes_topic_teacher_id ON quizzes_topic(teacher_id);
```

---

## 3.4 Model: Question

**Table:** `quizzes_question`

**Location:** `quizzes/models.py:17`

**Description:** Represents a multiple-choice question within a topic. Questions are ordered by `order_index` but shuffled during live quiz sessions.

### Fields

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| id | BigAutoField | Auto | Auto-increment | PK | Primary key |
| topic_id | BigIntegerField | Yes | - | FK to Topic | Parent topic |
| text | CharField | Yes | - | max 500 | Question text |
| order_index | IntegerField | No | 0 | - | Display/load order |

### Relationships

| Relation | Type | Related Model | Related Name | On Delete |
|----------|------|---------------|--------------|-----------|
| topic | FK | Topic | questions | CASCADE |
| options | 1:N (reverse) | AnswerOption | options | CASCADE |

### Business Rules

- Deleting a Topic cascades to delete all Questions
- Deleting a Question cascades to delete all AnswerOptions
- Questions are loaded ordered by `order_index` for API
- During live sessions, question order is shuffled randomly
- Must have exactly 4 options (enforced by serializer, not DB)
- `order_index` defaults to 0 (no explicit ordering unless set)

### Used in APIs

- **POST /api/topics/{topic_id}/questions/** - Create question
- **PATCH /api/questions/{id}/** - Update question
- **DELETE /api/questions/{id}/delete/** - Delete question
- Nested in Topic responses

### Used in Socket Events

- **teacher:create_session** - Loads all question IDs
- **session:question** - Sends question to students

### SQL Definition

```sql
CREATE TABLE quizzes_question (
    id BIGSERIAL PRIMARY KEY,
    topic_id BIGINT NOT NULL REFERENCES quizzes_topic(id) ON DELETE CASCADE,
    text VARCHAR(500) NOT NULL,
    order_index INTEGER DEFAULT 0
);

CREATE INDEX quizzes_question_topic_id ON quizzes_question(topic_id);
```

---

## 3.5 Model: AnswerOption

**Table:** `quizzes_answeroption`

**Location:** `quizzes/models.py:26`

**Description:** Represents an answer option for a question. Each question should have exactly 4 options with at least one marked as correct.

### Fields

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| id | BigAutoField | Auto | Auto-increment | PK | Primary key |
| question_id | BigIntegerField | Yes | - | FK to Question | Parent question |
| text | CharField | Yes | - | max 255 | Option text |
| is_correct | BooleanField | No | False | - | Correct answer flag |

### Relationships

| Relation | Type | Related Model | Related Name | On Delete |
|----------|------|---------------|--------------|-----------|
| question | FK | Question | options | CASCADE |

### Business Rules

- Deleting a Question cascades to delete all AnswerOptions
- At least one option per question must have `is_correct=True` (enforced by serializer)
- Multiple options CAN be marked as correct (handled in scoring logic)
- Options are NOT shuffled during quiz sessions
- `is_correct` is hidden from students during quiz (only `id` and `text` sent)

### Used in APIs

- Created via **POST /api/topics/{topic_id}/questions/**
- Updated via **PATCH /api/questions/{id}/**
- **DELETE /api/options/{id}/delete/**
- Nested in Question responses

### Used in Socket Events

- **session:question** - Options sent to students (without `is_correct`)
- **answer_result** - `correct_option_id` revealed after question closes

### SQL Definition

```sql
CREATE TABLE quizzes_answeroption (
    id BIGSERIAL PRIMARY KEY,
    question_id BIGINT NOT NULL REFERENCES quizzes_question(id) ON DELETE CASCADE,
    text VARCHAR(255) NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE
);

CREATE INDEX quizzes_answeroption_question_id ON quizzes_answeroption(question_id);
```

---

## 3.6 Migration History

### users app

| Migration | Date | Description |
|-----------|------|-------------|
| 0001_initial | 2025-11-19 | Create User model with email, password, is_active, is_staff, groups, permissions |
| 0002_add_profile_fields | - | Add first_name, last_name, specialty, role fields |
| 0003_remove_user_role | - | Remove role field (deprecated) |

### quizzes app

| Migration | Date | Description |
|-----------|------|-------------|
| 0001_initial | 2025-12-03 | Create Topic, Question, AnswerOption models with ForeignKey relationships |

---

## 3.7 Database Configuration

**Location:** `backend/settings.py:91`

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

**Note:** These credentials are hardcoded. For production, use environment variables.

---

## 3.8 Indexes

Django automatically creates indexes for:
- Primary keys
- Foreign keys
- Unique fields

Additional indexes that may improve performance:
```sql
-- For filtering topics by teacher
CREATE INDEX idx_topic_teacher ON quizzes_topic(teacher_id);

-- For ordering questions
CREATE INDEX idx_question_order ON quizzes_question(topic_id, order_index);
```

---

## 3.9 Data Integrity Constraints

| Constraint | Table | Description |
|------------|-------|-------------|
| UNIQUE | users_user.email | Prevents duplicate emails |
| NOT NULL | All PKs and FKs | Referential integrity |
| CASCADE DELETE | All FKs | Automatic cleanup |
| DEFAULT | Various fields | Sensible defaults |

---

[Next: Socket.IO Events →](./04-socket-events.md)
