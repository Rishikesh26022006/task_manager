# AI-Powered Task Management System

A backend REST API built with **Python and Flask**. Users register, log in with **JWT**, and manage their own tasks. Admins can see and manage every task. An **AI feature** (Google Gemini) generates a task description from a task title.

## Features
- User registration and login with JWT tokens
- Two roles: `user` and `admin`
- Task create, list, view, update and update-status APIs
- Role-based access control (users only touch their own tasks, only admins change the status)
- AI-generated task descriptions (Gemini)
- JSON error responses with correct HTTP status codes
- Seeder with sample users and tasks
- Postman collection with automatic tests

## Tech stack
- Python 3.10 or newer (developed on Python 3.14)
- Flask and Flask-SQLAlchemy
- MySQL (XAMPP was used during development)
- PyJWT for tokens, Werkzeug for password hashing
- Google Gemini API, called with the `requests` library

## Project structure
```
task_manager/
├── app/
│   ├── api/          routes (auth, tasks, ai) and error handlers
│   ├── models/       User and Task tables
│   ├── auth/         JWT helpers and login/admin decorators
│   ├── ai/           Gemini client (kept separate from the rest of the app)
│   ├── database/     db object and seeder
│   ├── config.py
│   └── main.py
├── postman/          Postman collection
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

1. **Create and activate a virtual environment**
   ```
   python -m venv venv
   venv\Scripts\activate          (Windows)
   source venv/bin/activate       (Mac/Linux)
   ```
2. **Install the packages**
   ```
   pip install -r requirements.txt
   ```
3. **Start MySQL** (for example, start MySQL in the XAMPP Control Panel).
4. **Create an empty database** called `task_manager` (phpMyAdmin: New, name it `task_manager`, Create).
5. **Create your `.env` file.** Copy `.env.example` to `.env` and fill in the values (see below).
6. **Run the app.** The tables are created automatically on the first start.
   ```
   flask --app app.main run --debug
   ```
   The API runs at `http://127.0.0.1:5000`.
7. **Add the sample data** (in a second terminal, with the venv active):
   ```
   python -m app.database.seed
   ```
   The seeder can be run more than once. It skips data that already exists.

## Database configuration
- Database: **MySQL**
- Default XAMPP settings: user `root`, empty password, host `localhost`, database `task_manager`
- The schema comes from the SQLAlchemy models in `app/models/` and is created with `db.create_all()` when the app starts. No separate SQL file is used.
- Sample data comes from the seeder `app/database/seed.py`.

## Environment variables
Set these in `.env` (never commit this file):

| Variable | Meaning |
|---|---|
| `SECRET_KEY` | Secret used to sign JWT tokens |
| `DB_USER` | MySQL user |
| `DB_PASSWORD` | MySQL password (empty for default XAMPP) |
| `DB_HOST` | MySQL host, usually `localhost` |
| `DB_NAME` | Database name, `task_manager` |
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `GEMINI_MODEL` | Main Gemini model, e.g. `gemini-flash-latest` |
| `GEMINI_FALLBACK_MODEL` | Backup model used if the main one is busy, e.g. `gemini-2.5-flash-lite` |

## AI configuration
1. Create a free API key at https://aistudio.google.com (API keys).
2. Put it in `.env` as `GEMINI_API_KEY`.
3. Restart the app after changing `.env`.

The model names can be changed in `.env` if Google renames or retires a model.

**AI feature implemented: Option A, Generate Task Description** (`POST /api/tasks/generate-description`).

How it works:
- The request must include a valid JWT and a `title`.
- The Gemini client (`app/ai/gemini_client.py`) asks the model for JSON in the form `{"description": "..."}`.
- The response is validated (it must be valid JSON, a dictionary, and contain a non-empty `description` string).
- Failures are handled: missing key (503), timeout (504), rate limit (429), service busy (503, after one retry and a fallback model), other errors and invalid responses (502). The API always answers with clean JSON.

## API endpoints

Send the token as `Authorization: Bearer <token>` on every endpoint except register and login.

| Method | URL | Who | Description |
|---|---|---|---|
| POST | `/api/auth/register` | Anyone | Register a new user (role is always `user`) |
| POST | `/api/auth/login` | Anyone | Log in and receive a JWT |
| GET | `/api/auth/me` | Logged in | Show the current user |
| POST | `/api/tasks` | User, Admin | Create a task (starts as `Pending`) |
| GET | `/api/tasks` | User, Admin | List tasks (users see their own, admins see all) |
| GET | `/api/tasks/<id>` | Owner, Admin | View one task |
| PUT | `/api/tasks/<id>` | Owner, Admin | Update title and/or description |
| PATCH | `/api/tasks/<id>/status` | Admin only | Update status |
| POST | `/api/tasks/generate-description` | User, Admin | AI: generate a description from a title |

Allowed statuses: `Pending`, `In Progress`, `Testing`, `Completed`.

Example request bodies:
```
POST /api/auth/register   {"name": "Test", "email": "test@example.com", "password": "123456"}
POST /api/auth/login      {"email": "rahul@example.com", "password": "User@123"}
POST /api/tasks           {"title": "Fix login bug", "description": "Check the login page"}
PATCH /api/tasks/1/status {"status": "Testing"}
POST /api/tasks/generate-description   {"title": "Fix login bug"}
```

## Test credentials (created by the seeder)

| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | Admin@123 |
| User | rahul@example.com | User@123 |
| User | priya@example.com | User@123 |

## Postman collection
File: `postman/Task_Manager.postman_collection.json`

1. In Postman, use Import and choose the file.
2. Make sure MySQL and the Flask app are running and the seeder has been run.
3. Right-click the collection, choose Run collection, then Run.

The first folder logs in and saves the user and admin tokens as collection variables, so no token needs to be copied by hand. The collection covers registration, login, regular user task APIs, admin task APIs, authorization failures, and the AI endpoint.

## Error handling
| Situation | Status |
|---|---|
| Invalid request data | 400 |
| Invalid credentials, missing/invalid/expired JWT | 401 |
| Not allowed (for example a user changing a status or opening another user's task) | 403 |
| Task or URL not found | 404 |
| Duplicate email | 409 |
| Database or unexpected server errors | 500 |
| AI problems | 429 / 502 / 503 / 504 |

## Important assumptions and decisions
- **Roles:** public registration always creates a `user`. Admins are only created by the seeder, so nobody can make themselves an admin.
- **Status changes:** only admins can change a task status, through the dedicated status endpoint. If a regular user sends `status` in a normal update, the API returns 403.
- **Ownership:** a task's `user_id` is taken from the JWT, never from the request body.
- **Passwords:** stored as hashes (Werkzeug), never as plain text.
- **JWT:** signed with `SECRET_KEY` (HS256) and valid for 24 hours.
- **Schema:** created from the models with `db.create_all()` (no migration tool and no SQL file).
- **AI resilience:** the AI call has a 30-second timeout, one retry on 500/503, and a fallback model.
- **Package versions:** SQLAlchemy is pinned to a 2.0 release in `requirements.txt` because the newest version caused a compiled-file problem on one Windows machine.