# File: README.md
# Purpose: Project README — setup, API reference, multi-value usage, CI/CD description.

# 🧮 CalcApp — Module 14: BREAD Calculations

A FastAPI application with **full BREAD operations**, JWT auth, PostgreSQL storage, a Jinja2/JS frontend, 100% pytest coverage, and a GitHub Actions CI/CD pipeline. Calculations accept **multiple comma-separated values** (not just two numbers).

| Resource | Link |
|---|---|
| GitHub | https://github.com/KKS071/assignment14_calculation_bread |
| Docker Hub | https://hub.docker.com/r/kks59/601_module14 |

---

## 📁 Project Structure

```
assignment14_calculation_bread/
├── .github/workflows/ci.yml         # CI: test → Trivy scan → Docker push
├── app/
│   ├── main.py                      # All routes (auth + BREAD)
│   ├── database.py                  # SQLAlchemy engine + session
│   ├── database_init.py             # Table creation helper
│   ├── operations.py                # Pure arithmetic functions
│   ├── auth/
│   │   ├── dependencies.py          # get_current_user FastAPI dep
│   │   └── jwt.py                   # Password hashing, JWT create/decode
│   ├── core/config.py               # Pydantic Settings (env vars)
│   ├── models/
│   │   ├── calculation.py           # Polymorphic Calculation ORM models
│   │   └── user.py                  # User ORM model + auth helpers
│   └── schemas/
│       ├── calculation.py           # Pydantic schemas (multi-value inputs)
│       ├── token.py                 # JWT token schemas
│       └── user.py                  # User schemas
├── static/
│   ├── css/style.css                # Calculator theme + pill display
│   └── js/auth.js                   # parseInputs, renderPills, authFetch helpers
├── templates/
│   ├── base.html                    # Shared navbar with SVG calculator icon
│   ├── index.html                   # Landing page
│   ├── login.html                   # Login form
│   ├── register.html                # Registration form
│   ├── dashboard.html               # Browse + Add (multi-value input)
│   ├── view_calculation.html        # Read
│   └── edit_calculation.html        # Edit (multi-value input)
├── tests/
│   ├── conftest.py                  # Shared fixtures (transactional rollbacks)
│   ├── unit/                        # Pure logic tests (no DB)
│   ├── integration/                 # API + DB tests
│   └── e2e/                         # Playwright browser tests (auto-starts server)
├── docs/reflection.md
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── init-db.sh
├── pytest.ini
└── requirements.txt
```

---

## 🔌 BREAD API Reference

All `/calculations` endpoints require `Authorization: Bearer <access_token>`.

### Browse — `GET /calculations`
Returns all calculations for the logged-in user, newest first.
```json
[{ "id": "...", "type": "addition", "inputs": [10, 5, 3], "result": 18.0, ... }]
```

### Read — `GET /calculations/{id}`
Returns a single calculation by UUID. 404 if not found or belongs to another user.

### Edit — `PUT /calculations/{id}`
Updates type and/or inputs; recomputes result automatically.
```json
// Request
{ "type": "multiplication", "inputs": [2, 3, 4] }
// Response
{ "type": "multiplication", "inputs": [2.0, 3.0, 4.0], "result": 24.0, ... }
```

### Add — `POST /calculations`
Creates a new calculation with **2 or more** comma-separated values.
```json
// Request
{ "type": "division", "inputs": [120, 2, 3, 4] }
// Response
{ "type": "division", "inputs": [120.0, 2.0, 3.0, 4.0], "result": 5.0, ... }
```

### Delete — `DELETE /calculations/{id}`
Deletes one calculation; returns 204. Other calculations are untouched.

### Auth endpoints
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login (JSON) — returns tokens + user info |
| POST | `/auth/token` | Login (form — Swagger UI) |

---

## 🚀 Running Locally

### Option A — Docker Compose (recommended)
```bash
git clone https://github.com/KKS071/assignment14_calculation_bread.git
cd assignment14_calculation_bread
cp .env.example .env          # edit secrets if needed
docker compose up --build
# App → http://localhost:8000
# pgAdmin → http://localhost:5050  (admin@example.com / admin)
```

### Option B — Python venv
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL and JWT keys
createdb fastapi_db
createdb fastapi_test_db
uvicorn app.main:app --reload
```

---

## 🧪 Running Tests

```bash
# All unit + integration tests with coverage
pytest tests/unit/ tests/integration/ -v

# Playwright E2E (server auto-starts in background on port 8001)
playwright install --with-deps chromium   # once
pytest tests/e2e/ -v -m e2e

# Full suite
pytest -v
```

Coverage report is written to `htmlcov/index.html`.

---

## ⚙️ CI/CD

`.github/workflows/ci.yml` runs three jobs on every push/PR to `main`:

1. **test** — Postgres service container → `pytest` with coverage → Playwright E2E
2. **trivy-scan** — builds Docker image → Trivy vulnerability scan (CRITICAL + HIGH)
3. **push-image** — builds multi-platform image → pushes to `kks59/601_module14` on Docker Hub

Secrets required: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.

---

## 🎓 Learning Outcomes

| CLO | Description |
|---|---|
| CLO3 | Python apps with automated testing (pytest + pytest-cov, 100% coverage) |
| CLO4 | GitHub Actions CI/CD (tests → Trivy scan → Docker push) |
| CLO9 | Containerisation with Docker and Docker Compose |
| CLO10 | REST API design with FastAPI |
| CLO11 | SQLAlchemy + PostgreSQL integration |
| CLO12 | Pydantic v2 validation (multi-value inputs, password strength) |
| CLO13 | JWT auth, bcrypt hashing, user-scoped data access |

---

## 🐳 Docker Hub

```bash
docker pull kks59/601_module14:latest
```
