# File: README.md
# Purpose: Project overview, setup instructions, API reference, and CI/CD description.

# 🧮 CalcApp — Module 14: BREAD Functionality for Calculations

A FastAPI application with **full BREAD operations** for calculations, JWT authentication, PostgreSQL persistence, a Jinja2/JS frontend, 100% pytest coverage, and a three-stage GitHub Actions CI/CD pipeline.

| Resource | Link |
|---|---|
| GitHub | https://github.com/KKS071/assignment14_calculation_bread |
| Docker Hub | https://hub.docker.com/r/kks59/601_module14 |

---

## 📁 Project Structure

```
assignment14_calculation_bread/
├── .github/
│   └── workflows/
│       └── ci.yml                  # CI/CD: test → Trivy → Docker push
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, all routes
│   ├── database.py                 # SQLAlchemy engine + session
│   ├── database_init.py            # Table creation helper
│   ├── operations.py               # Pure arithmetic functions
│   ├── auth/
│   │   ├── dependencies.py         # get_current_user dependency
│   │   └── jwt.py                  # Password hashing, JWT create/decode
│   ├── core/
│   │   └── config.py               # Pydantic Settings (env vars)
│   ├── models/
│   │   ├── calculation.py          # Polymorphic Calculation ORM models
│   │   └── user.py                 # User ORM model + auth helpers
│   └── schemas/
│       ├── calculation.py          # Pydantic schemas for calculations
│       ├── token.py                # JWT token schemas
│       └── user.py                 # User create/response schemas
├── static/
│   ├── css/style.css
│   └── js/auth.js
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html              # Browse + Add
│   ├── view_calculation.html       # Read
│   └── edit_calculation.html       # Edit
├── tests/
│   ├── conftest.py                 # Shared fixtures
│   ├── unit/
│   │   ├── test_calculation_model.py
│   │   ├── test_config.py
│   │   ├── test_jwt.py
│   │   ├── test_operations.py
│   │   └── test_schemas.py
│   ├── integration/
│   │   ├── test_api_auth.py
│   │   ├── test_api_calculations.py
│   │   ├── test_api_routes.py
│   │   ├── test_auth_dependencies.py
│   │   ├── test_calculation_model.py
│   │   ├── test_database.py
│   │   ├── test_database_init.py
│   │   └── test_user_model.py
│   └── e2e/
│       └── test_playwright.py
├── docs/
│   └── reflection.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── init-db.sh
├── pytest.ini
└── requirements.txt
```

---

## 🔌 BREAD API Endpoints

| Operation | Method | Path | Description |
|---|---|---|---|
| **B**rowse | `GET` | `/calculations` | List all calculations for the logged-in user |
| **R**ead | `GET` | `/calculations/{id}` | Get a single calculation by UUID |
| **E**dit | `PUT` | `/calculations/{id}` | Update inputs/type and recompute result |
| **A**dd | `POST` | `/calculations` | Create a new calculation |
| **D**elete | `DELETE` | `/calculations/{id}` | Remove a calculation |

All calculation endpoints require `Authorization: Bearer <access_token>`.

### Auth Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/auth/login` | Login (JSON) — returns tokens + user info |
| `POST` | `/auth/token` | Login (form) — Swagger UI compatible |

---

## 🚀 Running Locally

### Option A — Docker Compose (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/KKS071/assignment14_calculation_bread.git
cd assignment14_calculation_bread

# 2. Copy env file
cp .env.example .env   # edit secrets as needed

# 3. Start everything
docker compose up --build

# App: http://localhost:8000
# pgAdmin: http://localhost:5050  (admin@example.com / admin)
```

### Option B — Local Python (no Docker)

```bash
# Prerequisites: Python 3.10+, PostgreSQL running

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create a .env file with your DB URL and JWT secrets (see .env.example)
cp .env.example .env

# Create databases (psql)
createdb fastapi_db
createdb fastapi_test_db

# Run
uvicorn app.main:app --reload

# App: http://localhost:8000
```

---

## 🧪 Running Tests

### pytest + coverage

```bash
# All unit + integration tests with coverage report
pytest tests/unit/ tests/integration/ -v

# HTML coverage report in htmlcov/index.html
pytest tests/unit/ tests/integration/ --cov=app --cov-report=html
```

### Playwright E2E tests

```bash
# Install browser binaries once
playwright install --with-deps chromium

# Start the app in a separate terminal first, then:
pytest tests/e2e/ -v -m e2e
```

---

## ⚙️ CI/CD — GitHub Actions

The pipeline in `.github/workflows/ci.yml` has three jobs:

1. **test** — Spins up a Postgres service container, installs deps, runs `pytest` with coverage, then runs Playwright tests against a live `uvicorn` instance.
2. **trivy-scan** — Builds the Docker image and runs [Trivy](https://github.com/aquasecurity/trivy) to scan for `CRITICAL` and `HIGH` vulnerabilities.
3. **push-image** — On `main` branch only: builds a multi-platform image and pushes to `kks59/601_module14` on Docker Hub.

GitHub secrets needed: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.

---

## 🎓 Learning Outcomes

| CLO | Description |
|---|---|
| CLO3 | Python apps with automated testing (pytest, pytest-cov, 100% coverage) |
| CLO4 | GitHub Actions CI for tests + Docker builds (DevOps) |
| CLO9 | Containerization with Docker and Docker Compose |
| CLO10 | REST API design with Python (FastAPI) |
| CLO11 | Python + SQL database integration (SQLAlchemy + PostgreSQL) |
| CLO12 | JSON serialization/validation with Pydantic v2 |
| CLO13 | Secure auth/authz — bcrypt hashing, JWT access/refresh tokens, user-scoped data |

---

## 🐳 Docker Hub

Image: [`kks59/601_module14`](https://hub.docker.com/r/kks59/601_module14)

```bash
docker pull kks59/601_module14:latest
```