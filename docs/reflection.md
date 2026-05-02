# File: docs/reflection.md
# Purpose: Student reflection on Module 14 — BREAD, multi-value calculations, testing, CI/CD.

# Module 14 Reflection

## What I Built

I extended a FastAPI + PostgreSQL calculator app to support full BREAD operations (Browse, Read,
Edit, Add, Delete) with JWT authentication and a Jinja2/JS frontend. The major new feature this
iteration was **multi-value inputs** — instead of always requiring exactly two numbers, the API and
frontend now accept any number of comma-separated values (minimum two), making calculations like
`120 ÷ 2 ÷ 3 ÷ 4 = 5` possible in a single request. I also replaced the abacus logo with a proper
calculator SVG icon, wired up a full Playwright E2E suite that auto-starts the server, and reached
100% pytest coverage.

---

## Key Experiences

### Multi-value Calculation Logic

The Pydantic schema validator `coerce_inputs` was the right place to handle the comma-string
`"10, 5, 3"` → `[10.0, 5.0, 3.0]` conversion, because it runs before the model is constructed and
gives the frontend and API clients a consistent interface. Each model subclass (`Addition`,
`Subtraction`, `Multiplication`, `Division`) already iterated over a list, so the only change
needed there was removing the hardcoded two-element assumption and replacing it with a loop from
index `[0]` downward. The division subclass still checks every element from index `[1:]` for zero.

### Polymorphic Update Without ORM Identity Mismatch

The biggest technical bug I fixed was the SQLAlchemy warning:
`Flushing object <Addition> with incompatible polymorphic identity <multiplication>`.
Setting `calc.type = "multiplication"` on an existing `Addition` ORM instance confuses the
mapper because the Python object's class no longer matches the discriminator value. The clean fix
is to skip the ORM entirely for updates and use SQLAlchemy's **core** `update()` statement, then
re-query the updated row. This means no ORM object ever has a mismatched identity.

### Playwright E2E With Auto-Starting Server

The original E2E setup required a running dev server before running tests, which broke CI. I fixed
this by adding a `_ServerThread` in `tests/e2e/conftest.py` that starts `uvicorn.Server` as a
daemon thread bound to port 8001 at session scope. A `_wait_for_server()` TCP check blocks until
the port is accepting connections before the first test runs. This makes `pytest` fully self-contained — no manual startup step needed, locally or in GitHub Actions.

### Frontend Multi-value UX

Displaying multiple inputs as coloured pills (`<span class="input-pill">10</span>`) via the
`renderPills()` JS helper was a small detail that significantly improves readability in the browse
table and detail view. The `parseInputs()` helper validates the comma string client-side before
any fetch is made, so users see an inline error immediately rather than waiting for an API round-trip.

### 100% Test Coverage

Reaching 100% coverage required targeting specific branches I had initially skipped — particularly
the `NotImplementedError` in the abstract base `Calculation.get_result()`, the `no sub` claim path
in the JWT dependency, and the password-strength validator branches for "no digit" and "no
lowercase". Mocking `jwt.encode` to raise an exception was the cleanest way to cover the
`create_token` error path without altering production code.

---

## Challenges

- **Timezone-aware vs naive datetimes** — `datetime.now(timezone.utc)` vs `datetime.utcnow()` mixed
  in different files caused subtle token expiry validation failures. Standardised on `timezone.utc`
  everywhere in auth code.

- **Transactional test isolation** — using `session.begin_nested()` (a `SAVEPOINT`) instead of a
  plain outer transaction prevents the `transaction already deassociated` SAWarning when a test
  triggers a DB-level rollback inside the route handler.

- **Playwright selector reliability** — the first E2E iteration used broad CSS selectors like
  `button[type=submit]` that matched multiple elements. Switching to `onclick` attribute selectors
  (`button[onclick='handleLogin()']`) and explicit IDs (`#calculate-btn`, `#save-btn`) made tests
  deterministic.

---

## What I Learned

- **CLO3** — pytest fixtures with transactional rollbacks give fast, isolated tests without
  teardown boilerplate.
- **CLO4** — GitHub Actions matrix is powerful: running Postgres as a service container with a
  health check, installing playwright browsers, and pushing to Docker Hub all in one YAML file.
- **CLO9** — Docker multi-stage builds and `--break-system-packages` pip flags are important for
  clean Debian-based images.
- **CLO10** — FastAPI's dependency injection and OpenAPI docstring support make self-documenting
  APIs almost effortless.
- **CLO11** — SQLAlchemy's polymorphic single-table inheritance is elegant but requires care when
  updating the discriminator column — the core `update()` bypass is the correct pattern.
- **CLO12** — Pydantic v2 `@field_validator(mode="before")` is the right hook for input coercion
  (string → list of floats) before model construction.
- **CLO13** — Short-lived JWT access tokens + user-scoped DB queries (`filter(user_id == current_user.id)`)
  are the two most important security primitives in this app.
