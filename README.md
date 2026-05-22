# Fluentian Backend

AI-powered French learning platform API for Ethiopian learners.

## Prerequisites

- Python 3.12+
- PostgreSQL 16
- Redis

## Local Setup

1. **Clone the repository** (if not already in the monorepo).
2. **Navigate to the backend folder**:
   ```bash
   cd backend
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   make install
   ```
5. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your local credentials (DB, Gemini API Key, etc.)
   ```
6. **Run migrations**:
   ```bash
   make migrate
   ```
7. **Start the development server**:
   ```bash
   make dev
   ```

## Environment Variables

| Name | Required | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `SECRET_KEY` | Yes | JWT signing key |
| `GEMINI_API_KEY` | Yes | Google Gemini API Key |

## API Overview

- **Base URL**: `/api/v1`
- **Auth**: Bearer JWT (Access + Refresh tokens)
- **Routers**:
  - `/auth`: Login, Register, Refresh, Password Reset
  - `/users`: Profiles and settings
  - `/content`: Courses, units, lessons
  - `/progress`: Mastery tracking and XP
  - `/ai`: AI tutor conversations and explanations
  - `/social`: Rooms and calls
  - `/notifications`: In-app alerts

## Running Tests

```bash
make test
```

## Project Structure

```
backend/
├── app/
│   ├── main.py         # Entry point
│   ├── models/         # ORM models
│   ├── schemas/        # Pydantic validation
│   ├── services/       # Business logic
│   ├── routers/        # API endpoints
│   └── core/           # Security, Exceptions, Middleware
├── alembic/            # Database migrations
└── tests/              # Pytest suite
```
