# AI Job Assistant

An intelligent backend that automates the job search process end-to-end. Instead of spending hours browsing job boards and writing applications, the user provides their profile once — the AI takes care of the rest.

---

## What it does

**1. CV Parsing**
The user uploads their existing CV (PDF, image, or manual input). The AI extracts and structures all relevant information: skills, work experience, education, and contact details.

**2. Job Search**
Based on the user's profile and preferences, the AI automatically searches for matching job offers across available sources. No manual browsing required.

**3. CV Generation**
For each job offer found, the AI generates a tailored version of the user's CV — highlighting the skills and experiences most relevant to that specific position.

**4. Cover Letter Generation**
The AI writes a personalized cover letter for each job offer, aligned with both the job requirements and the user's background.

---

## How it works

```
User profile + CV
       │
       ▼
  AI Job Search ──► Job Offers
       │
       ▼
 CV & Cover Letter Generation (per offer)
       │
       ▼
  Ready-to-send applications
```

---

## Tech Stack

- **FastAPI** — REST API
- **SQLAlchemy** — ORM
- **DeepSeek** — LLM for parsing, generation and scoring
- **pdfplumber / pytesseract** — OCR for CV extraction
- **Argon2 + JWT** — Authentication
- **Google OAuth2** — Social login
- **SMTP** — Email notifications

---

## Environment Setup

Copy `.env.example` to `.env` and fill in the required values:

```env
SECRET_KEY=
DATABASE_URL=
DEEPSEEK_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=
SMTP_SERVER=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
FRONTEND_URL=
```

Then run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
