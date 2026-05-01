# File: docs/reflection.md
# Purpose: Student reflection on Module 14 — BREAD functionality, testing, CI/CD, Docker, security.

# Module 14 Reflection

## What I Built

For this assignment I implemented full BREAD (Browse, Read, Edit, Add, Delete) functionality for a FastAPI-based calculation app backed by PostgreSQL. The app uses JWT authentication, a polymorphic SQLAlchemy model for different operation types, Pydantic schemas for validation, and a lightweight Jinja2/JS frontend. I also wired up a three-stage GitHub Actions CI/CD pipeline: pytest → Trivy scan → Docker Hub push.

---

## Key Experiences

### BREAD Endpoints

Getting the five endpoints right took more thought than I expected. The trickiest part was the **Edit** endpoint — when a user changes both the `type` and `inputs`, I need to update the discriminator column *and* recompute the result using the correct subclass logic. I handled this by using the factory method `Calculation.create()` to get a temporary subclass instance for the arithmetic, then writing the result back to the persisted row.

### Polymorphic Inheritance

SQLAlchemy's single-table inheritance with a `polymorphic_identity` on `type` is elegant once it clicks. Getting `get_result()` to dispatch to the right subclass at query time was satisfying — it keeps business logic inside the model where it belongs and keeps the route handlers thin.

### JWT Auth

I reinforced the difference between **access tokens** (short-lived, for API calls) and **refresh tokens** (longer-lived, for re-auth). One bug I chased was timezone-aware vs naive datetimes in token expiry checks — the fix was consistently using `datetime.now(timezone.utc)` everywhere.

### 100% Test Coverage

Reaching 100% coverage meant writing tests for paths I initially skipped — invalid UUIDs, divide-by-zero guard in the update route, cross-user access attempts, and the `database_init` helper functions. The trickiest coverage gap was the `create_token` error branch, which I covered by mocking `jwt.encode` to raise an exception.

### Playwright E2E Tests

Setting up Playwright in CI required installing Chromium browser binaries separately (`playwright install --with-deps chromium`) and starting the server before running tests. I used `continue-on-error: true` for the E2E step so a flaky browser test doesn't block the Docker push.

### Docker + Docker Compose

Running `docker compose up --build` with a health check on the Postgres container before the web service starts was important — without `depends_on: condition: service_healthy`, the app tried to connect before the DB was ready and crashed.

### Trivy Vulnerability Scan

Trivy flagged a few `CRITICAL` packages in the base Python image. Pinning `setuptools >= 70.0.0` and running `apt-get upgrade -y` in the Dockerfile brought those counts down significantly.

---

## Challenges

- **Timezone naive/aware datetime mismatch** in token expiry — subtle but broke login.
- **Polymorphic updates** — updating `type` on an existing row doesn't automatically call the new subclass's `__init__`, so the result had to be recomputed manually.
- **Test isolation** — using transactional rollbacks per test was critical; without it, user-uniqueness constraints caused random failures depending on test ordering.

---

## What I Learned

- **CLO3** — Automated testing with `pytest` + `pytest-cov` gives real confidence that all code paths work.
- **CLO4** — GitHub Actions makes it easy to run tests on every push and block bad code from being shipped.
- **CLO9** — Docker makes the app reproducible; anyone can run it with `docker compose up --build`.
- **CLO10** — FastAPI's dependency injection + Pydantic makes building validated REST APIs much cleaner than doing it manually.
- **CLO11** — SQLAlchemy's ORM handles the SQL boilerplate, but understanding raw SQL still helps when debugging.
- **CLO12** — Pydantic v2 validators catch bad input before it ever hits the database.
- **CLO13** — bcrypt hashing + short-lived JWTs + user-scoped DB queries are the three pillars of keeping this app secure.