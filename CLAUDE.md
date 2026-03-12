# AI Job Assistant — Backend

## Project overview

FastAPI backend for an AI-powered job search assistant. Core features:

- **Job search aggregation**: France Travail, Adzuna, Arbeitnow, Remotive, JobSpy scraper
- **AI engine**: CV parsing, job parsing, scoring/matching, cover letter & resume generation
- **LLM abstraction**: supports OpenAI-compatible APIs and Anthropic (`LLM_PROVIDER` env var)
- **Application tracking**: manage job applications with status workflow
- **Auth**: JWT access + refresh tokens, Google OAuth2, password reset via email
- **Billing/subscriptions**: quota enforcement per plan
- **Background tasks**: Celery + Redis (e.g. periodic job scraping)
- **Documents**: PDF generation with xhtml2pdf + Jinja2 templates

## Tech stack

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy (SQLite for dev, configurable via `DATABASE_URL`)
- Celery + Redis
- OpenAI SDK + Anthropic SDK
- pdfplumber + pytesseract (CV OCR)
- Virtual env: `myenv-job/`

## Project structure

```
app/
  api/v1/          # Route handlers (auth, users, cv, jobs, applications, profile, billing)
  core/            # config.py (Settings), security.py, auth.py, llm.py, logging.py
  db/              # session.py (engine/SessionLocal), base.py (Base)
  models/          # SQLAlchemy ORM models
  schemas/         # Pydantic schemas
  services/        # Business logic (auth, user, cv, email, billing, quota, search/*)
  ai_engine/       # LLM pipeline: parser/, scoring/, generation/, explainability/, llm/
  agents/          # Higher-level agents (document, apply, search)
  tasks/           # Celery tasks (jobs_tasks.py)
  services/document/ # PDF generator
  services/search/   # Per-source scrapers + normalizer
  utils/           # pdf.py, ocr.py, text.py, prompts.py
  templates/       # Jinja2 HTML templates for PDF generation
  tests/           # pytest tests
```

## Key entry points

- `app/main.py` — FastAPI app creation, router registration, DB init
- `app/celery_app.py` — Celery app instance
- `app/core/config.py` — All settings via env vars (`Settings` class, singleton `settings`)
- `app/core/llm.py` — LLM client abstraction

## Environment variables (`.env`)

```
SECRET_KEY=
DATABASE_URL=sqlite:///./app.db
LLM_PROVIDER=openai          # or "anthropic"
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_FAST=gpt-4o-mini
LLM_MODEL_SMART=gpt-4o
FRANCE_TRAVAIL_CLIENT_ID=
FRANCE_TRAVAIL_CLIENT_SECRET=
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
SMTP_SERVER=
SMTP_USERNAME=
SMTP_PASSWORD=
FRONTEND_URL=
```

## Dev commands

```bash
# Activate venv
source myenv-job/bin/activate

# Run API server
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.celery_app worker --loglevel=info

# Run Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info

# Run tests
pytest app/tests/
```

## Conventions

- Route prefix: `/api/v1/`
- DB session: dependency-injected via `get_db()` from `app/db/session.py`
- Auth: `get_current_user` dependency from `app/core/auth.py`
- New models must be imported in `app/db/base.py` to be picked up by `Base.metadata`
- LLM calls go through `app/ai_engine/llm/llm_client.py`, never call provider SDKs directly
- Background tasks use Celery, not FastAPI `BackgroundTasks`
