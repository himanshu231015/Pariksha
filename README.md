# Pariksha — RGPV Exam Preparation & Academic Platform

**Pariksha** is a full-stack academic web platform designed to help B.Tech engineering students prepare for university examinations (tailored for **Rajiv Gandhi Proudyogiki Vishwavidyalaya — RGPV**, Bhopal, and extensible to any university).

The platform provides verified Previous Year Question Papers (PYQs), official syllabus documents, structured curriculum tools, peer review workflows, and clean frontend integration boundaries for a future AI domain assistant.

---

## 1. Features Overview

### Core Academic & Document Features
- **Verified PYQ Search & Download:** Multi-filter query engine by Branch, Semester, Subject, Exam Year, and Session with authorized document downloads.
- **Peer Review & Contribution Workflow:** Authenticated students upload examination scans with automatic duplicate detection.
- **Role-Based Access Control (RBAC):** Distinct permissions for Students, Reviewers, and Administrators.
- **Anti-Self-Approval Enforcement:** Students are cryptographically prevented from reviewing or approving their own submissions.
- **Official Syllabus Management:** Administrator-only portal for uploading, versioning, and publishing official curriculum PDFs.
- **Cascading Academic APIs:** Dynamic endpoints (`/academics/api/...`) for live dropdown filtering on the client.
- **Audit Logging:** Comprehensive immutable trail of administrative actions, reviews, approvals, and status changes.
- **Platform Health Endpoint:** `/health/` monitoring endpoint for uptime and container health.

### Future AI Integration Interfaces (Non-AI Phase)
- **Ask Pariksha (`/assistant/`):** Chat-style interface with student & assistant message bubbles, academic context selectors, answer-format customization (detailed, concise, formula-first), and question suggestion chips.
- **Must Prepare Topics (`/preparation/must-prepare/`):** Subject curriculum units and paper metrics with an honest status explanation that empirical topic prioritization requires the future AI/statistical indexing microservice.
- **Predicted Practice Paper (`/preparation/predicted-paper/`):** 70-mark examination blueprint configurator with an explicit disclaimer distinguishing practice tests from actual/leaked university exam papers.
- **Clean Service Boundary (`apps/assistant_ui/services.py`, `schemas.py`):** Explicit dataclasses defining the proposed request/response contracts for future AI integration without fabricating canned answers.

---

## 2. Technology Stack

- **Backend:** Python 3.11+, Django 5.1.x, Django ORM, Django Migrations.
- **Frontend:** HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Vanilla JavaScript.
- **Authentication:** `django-allauth` for Google OAuth2 + Django Auth for local credentials.
- **Database:** SQLite (local development) / PostgreSQL 16 (production).
- **Storage:** Protected media storage abstraction with authorization-aware Django views (`FileResponse`).
- **Containerization:** Docker & Docker Compose (`compose.yaml`).

---

## 3. Repository Structure

```text
Pariksha/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── compose.yaml
├── pytest.ini
├── README.md
├── config/
│   ├── __init__.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       └── production.py
├── apps/
│   ├── accounts/         # User roles, student profiles, Google OAuth & local auth
│   ├── academics/        # University, Program, Branch, Semester, Subject, Unit models & APIs
│   ├── papers/           # Verified AcademicPaper models, search views, secure downloads
│   ├── reviews/          # PaperContribution, ReviewDecision, duplicate detection & audit logs
│   ├── syllabus/         # Official SyllabusDocument management (admin-only)
│   ├── assistant_ui/     # Ask Pariksha, Must Prepare, Predicted Paper & future AI schemas
│   └── core/             # Home landing page, health check, legal pages, custom 403/404/500
├── templates/            # 17 Django HTML templates (base, accounts, dashboard, papers, reviews, errors)
├── static/
│   ├── css/pariksha.css  # Academic navy & slate design system
│   └── js/pariksha.js    # Vanilla JS cascading dropdowns & chat UI interactions
└── media/
    ├── avatars/
    └── protected/        # Private uploaded papers and syllabus files
```

---

## 4. Local Development Setup

### Prerequisites
- Python 3.11 or higher
- Git

### Step 1: Clone and Create Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default development settings in `.env` run with SQLite and require no external services.

### Step 4: Apply Database Migrations
```bash
python manage.py migrate
```

### Step 5: Seed Sample Academic Data (RGPV B.Tech)
Run the built-in seeding command to populate universities, branches (CSE, IT, EC, ME, CE), 8 semesters, core subjects (CS-502 Operating Systems, CS-503 DBMS, etc.), syllabus units, sample verified PYQ papers, and test users:
```bash
python manage.py seed_academic_data
```

#### Pre-configured Test Accounts:
| Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Student** | `student1` | `pariksha123` | `student1@pariksha.edu` |
| **Reviewer** | `reviewer1` | `pariksha123` | `reviewer@pariksha.edu` |
| **Administrator** | `admin` | `pariksha123` | `admin@pariksha.edu` |

### Step 6: Start the Development Server
```bash
python manage.py runserver
```
Visit **`http://127.0.0.1:8000/`** in your browser.

---

## 5. Running Automated Tests

Run the complete test suite covering authentication, PYQ search, authorized downloads, paper contribution, duplicate prevention, anti-self-approval security, syllabus management, error pages, and AI boundary contracts:

```bash
# Using Django Test Runner
python manage.py test tests

# Or using pytest
pytest
```

---

## 6. Docker & Docker Compose Setup

Run the entire application stack (Web + PostgreSQL) using Docker Compose:

```bash
# Build and run containers
docker compose up -d --build

# Run migrations inside container
docker compose exec web python manage.py migrate

# Seed sample academic data
docker compose exec web python manage.py seed_academic_data

# View logs
docker compose logs -f
```
The application will be accessible at **`http://localhost:8000/`**.

---

## 7. Google OAuth Setup Guide

To enable Google sign-in:
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project named **Pariksha**.
3. Under **APIs & Services > Credentials**, create an **OAuth 2.0 Client ID**.
4. Set Application Type to **Web application**.
5. Add Authorized Redirect URI:
   `http://127.0.0.1:8000/accounts/google/login/callback/` (local)
   `https://yourdomain.com/accounts/google/login/callback/` (production)
6. Copy the **Client ID** and **Client Secret** into your `.env` file:
   ```env
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```
7. Restart the development server. The "Continue with Google" button on `/accounts/login/` will now be active.

---

## 8. Future AI Integration Boundary

Pariksha strictly decouples the web application from the future AI model and inference microservice.

### Integration Boundary Code:
- **`apps/assistant_ui/schemas.py`:** Contains dataclasses (`AssistantInquiryRequest`, `AssistantInquiryResponse`, `SourceCitation`, `MustPrepareTopicItem`, `PredictedPaperResponse`).
- **`apps/assistant_ui/services.py`:** Service adapter. Currently detects that `FUTURE_AI_SERVICE_URL` is unconfigured and returns an honest `pending_integration` response.
- **Connecting the Future AI Backend:**
  When your AI model and RAG pipeline are deployed (e.g. FastAPI / vLLM):
  1. Set in `.env`:
     ```env
     FUTURE_AI_SERVICE_URL=https://ai.pariksha.edu/v1/inquiry
     FUTURE_AI_SERVICE_API_KEY=your-secure-ai-api-key
     ```
  2. Implement the HTTP dispatch call inside `AssistantService.send_inquiry()` in `apps/assistant_ui/services.py`.
  3. No template or database schema changes are required.

---

## 9. Current Status & Known Incomplete Integrations

| Feature | Current Status | Notes |
| :--- | :--- | :--- |
| **Responsive Frontend** | Fully Implemented | 17 Bootstrap 5 templates with custom academic design system |
| **Academic Catalog & ORM** | Fully Implemented | Normalized University, Program, Branch, Semester, Subject, Unit models |
| **PYQ Search & Downloads** | Fully Implemented | Multi-filtering, pagination, authorized `FileResponse` delivery |
| **Paper Contribution** | Fully Implemented | File type/size validation, duplicate prevention across full context |
| **Reviewer & Admin Portals** | Fully Implemented | Peer review workflow, anti-self-approval rule, syllabus management |
| **Audit Trail** | Fully Implemented | Detailed tracking of approvals, rejections, and metadata updates |
| **Automated Tests** | 33 Tests Passed | 100% pass rate across all functional modules |
| **Google OAuth2** | Configured via Allauth | Ready for client credentials in `.env`; fallback to local auth for testing |
| **AI Inference / LLM Model** | Intentionally Excluded | Surfaced with clear integration boundary; pending future model integration |
| **Cloud Object Storage (S3)** | Abstractable | Uses private local filesystem; ready for `django-storages` S3 backend |
| **Email SMTP Delivery** | Console Backend | Set real SMTP credentials in production `.env` if verification emails are needed |

---

## 10. Production Deployment Checklist

1. [ ] Set `DJANGO_DEBUG=False` in `.env`.
2. [ ] Generate a cryptographically secure 50+ character `DJANGO_SECRET_KEY`.
3. [ ] Set `DJANGO_ALLOWED_HOSTS` to your production domain name(s).
4. [ ] Enable `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, and `CSRF_COOKIE_SECURE=True`.
5. [ ] Configure PostgreSQL database credentials and run `python manage.py migrate`.
6. [ ] Collect static assets: `python manage.py collectstatic --no-input`.
7. [ ] Configure Google OAuth Production Credentials in Google Cloud Console with your production domain redirect URL.
8. [ ] Set up automated database backups (`pg_dump`) on a daily cron schedule.
9. [ ] Place Gunicorn behind an Nginx reverse proxy with SSL termination (Let's Encrypt / Certbot).
# Pariksha
