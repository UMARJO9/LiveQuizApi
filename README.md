# LiveQuiz API

Django REST API for managing quizzes, questions, and choices with JWT authentication.

## Features
- Custom user model with email login
- JWT auth (access/refresh) via SimpleJWT
- Quizzes, questions, and choices CRUD
- Swagger UI at `/api/docs/`

## Requirements
- Python 3.11+
- PostgreSQL 13+

## Installation
1) Clone the repo and enter the folder
```
cd LiveQuizApi
```

2) (Recommended) Create and activate a virtual environment
```
python -m venv venv
# Windows PowerShell
venv\Scripts\Activate.ps1
# or cmd
venv\Scripts\activate.bat
```

3) Install dependencies
```
pip install -r requirements.txt
```

## Configuration
By default the project expects a local PostgreSQL instance. Adjust `backend/settings.py` or set environment variables to match your setup.

Suggested env variables:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG` (0/1)
- `DJANGO_ALLOWED_HOSTS` (comma-separated)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

For local development you may switch to SQLite quickly by changing `DATABASES['default']` in `backend/settings.py` to:
```
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
  }
}
```

## Migrations and Run
```
python manage.py migrate
python manage.py runserver
```

## API
- Registration: `POST /api/register/`
- Login (JWT): `POST /api/login/`
- Refresh token: `POST /api/refresh/`
- Quizzes: `GET/POST /api/quizzes/`, `GET/PUT/PATCH/DELETE /api/quizzes/{id}/`
- Questions: `POST /api/quizzes/{quiz_id}/questions/`, `PATCH /api/questions/{id}/`, `DELETE /api/questions/{id}/delete/`
  - Question update body requires `topic_id` and supports partial fields: `text`, `options` (4 items with existing ids)
- Choices: `POST /api/questions/{question_id}/choices/`, `DELETE /api/choices/{id}/delete/`

Docs UI: open `http://127.0.0.1:8000/api/docs/` in a browser.

## Notes
- Do not commit local virtual environments (`venv/`) or secrets. `.gitignore` is included.
- Access to quiz/question/choice operations should be restricted to the owning user; review views before production.
