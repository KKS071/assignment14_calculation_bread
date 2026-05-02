# File: app/main.py
# Purpose: FastAPI entrypoint — auth routes, BREAD calculation endpoints, HTML page routes.
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import List
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import update as sa_update
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import Base, engine, get_db
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationBase, CalculationResponse, CalculationUpdate
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CalcApp API",
    description="FastAPI calculator with BREAD operations, JWT auth, and multi-value inputs.",
    version="2.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def read_health():
    return {"status": "ok"}


# ── HTML page routes ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["web"])
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, tags=["web"])
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse, tags=["web"])
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse, tags=["web"])
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard/view/{calc_id}", response_class=HTMLResponse, tags=["web"])
def view_page(request: Request, calc_id: str):
    return templates.TemplateResponse(
        "view_calculation.html", {"request": request, "calc_id": calc_id}
    )


@app.get("/dashboard/edit/{calc_id}", response_class=HTMLResponse, tags=["web"])
def edit_page(request: Request, calc_id: str):
    return templates.TemplateResponse(
        "edit_calculation.html", {"request": request, "calc_id": calc_id}
    )


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Register a new user",
)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    **Add a new user account.**

    - Validates password strength (uppercase, lowercase, digit, symbol).
    - Returns the created user (no token — redirect to login).
    """
    user_data = user_create.model_dump(exclude={"confirm_password"})
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/auth/login", response_model=TokenResponse, tags=["auth"], summary="Login (JSON)")
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    **Login with JSON body.**

    Returns access token, refresh token, and user info.
    """
    auth_result = User.authenticate(db, user_login.username, user_login.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = auth_result["user"]
    db.commit()

    expires_at = auth_result.get("expires_at")
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not expires_at:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    return TokenResponse(
        access_token=auth_result["access_token"],
        refresh_token=auth_result["refresh_token"],
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


@app.post("/auth/token", tags=["auth"], summary="Login (form — Swagger UI)")
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    auth_result = User.authenticate(db, form_data.username, form_data.password)
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    db.commit()
    return {"access_token": auth_result["access_token"], "token_type": "bearer"}


# ── BREAD: Calculations ───────────────────────────────────────────────────────

@app.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["calculations"],
    summary="Add — create a new calculation",
)
def create_calculation(
    calculation_data: CalculationBase,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    **Add** a new calculation.

    - `type`: one of `addition`, `subtraction`, `multiplication`, `division`
    - `inputs`: list of ≥ 2 floats, e.g. `[10, 5, 2]`

    The server computes and stores the result automatically.

    **Example request:**
    ```json
    { "type": "addition", "inputs": [10, 5, 3] }
    ```
    **Example response:**
    ```json
    { "id": "...", "type": "addition", "inputs": [10, 5, 3], "result": 18.0, ... }
    ```
    """
    try:
        calc = Calculation.create(
            calculation_type=calculation_data.type,
            user_id=current_user.id,
            inputs=calculation_data.inputs,
        )
        calc.result = calc.get_result()
        db.add(calc)
        db.commit()
        db.refresh(calc)
        return calc
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get(
    "/calculations",
    response_model=List[CalculationResponse],
    tags=["calculations"],
    summary="Browse — list all calculations for the current user",
)
def list_calculations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    **Browse** all calculations belonging to the logged-in user.

    Results are ordered newest-first.

    **Example response:**
    ```json
    [
      { "id": "...", "type": "addition", "inputs": [10, 5], "result": 15.0, ... },
      { "id": "...", "type": "division", "inputs": [100, 4, 5], "result": 5.0, ... }
    ]
    ```
    """
    return (
        db.query(Calculation)
        .filter(Calculation.user_id == current_user.id)
        .order_by(Calculation.created_at.desc())
        .all()
    )


@app.get(
    "/calculations/{calc_id}",
    response_model=CalculationResponse,
    tags=["calculations"],
    summary="Read — get a single calculation by ID",
)
def get_calculation(
    calc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    **Read** one calculation by UUID.

    Returns 404 if not found or if it belongs to a different user.
    Returns 400 if the ID is not a valid UUID.

    **Example response:**
    ```json
    { "id": "abc-...", "type": "multiplication", "inputs": [3, 4, 5], "result": 60.0, ... }
    ```
    """
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid calculation ID format.",
        )

    calc = (
        db.query(Calculation)
        .filter(Calculation.id == calc_uuid, Calculation.user_id == current_user.id)
        .first()
    )
    if not calc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found."
        )
    return calc


@app.put(
    "/calculations/{calc_id}",
    response_model=CalculationResponse,
    tags=["calculations"],
    summary="Edit — update inputs/type and recompute result",
)
def update_calculation(
    calc_id: str,
    calculation_update: CalculationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    **Edit** an existing calculation.

    - Partial update: send only the fields you want to change.
    - Result is automatically recomputed from the new inputs.
    - Returns 404 for unknown IDs, 400 for invalid payload.

    **Example request:**
    ```json
    { "type": "multiplication", "inputs": [2, 3, 4] }
    ```
    **Example response:**
    ```json
    { "id": "...", "type": "multiplication", "inputs": [2, 3, 4], "result": 24.0, ... }
    ```
    """
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid calculation ID format.",
        )

    calc = (
        db.query(Calculation)
        .filter(Calculation.id == calc_uuid, Calculation.user_id == current_user.id)
        .first()
    )
    if not calc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found."
        )

    new_type   = calculation_update.type   if calculation_update.type   is not None else calc.type
    new_inputs = calculation_update.inputs if calculation_update.inputs  is not None else calc.inputs

    try:
        if new_type == "division" and any(float(v) == 0 for v in new_inputs[1:]):
            raise ValueError("Cannot divide by zero")

        # Use core UPDATE to avoid SQLAlchemy polymorphic identity mismatch warning
        tmp        = Calculation.create(new_type, current_user.id, new_inputs)
        new_result = tmp.get_result()

        db.execute(
            sa_update(Calculation)
            .where(Calculation.id == calc_uuid)
            .where(Calculation.user_id == current_user.id)
            .values(
                type=new_type,
                inputs=new_inputs,
                result=new_result,
                updated_at=datetime.utcnow(),
            )
        )
        db.commit()
        return db.query(Calculation).filter(Calculation.id == calc_uuid).first()
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.delete(
    "/calculations/{calc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["calculations"],
    summary="Delete — remove a calculation",
)
def delete_calculation(
    calc_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    **Delete** a calculation by UUID.

    - Returns 204 No Content on success.
    - Returns 404 if not found or belongs to another user.
    - Other users' calculations remain untouched.
    """
    try:
        calc_uuid = UUID(calc_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid calculation ID format.",
        )

    calc = (
        db.query(Calculation)
        .filter(Calculation.id == calc_uuid, Calculation.user_id == current_user.id)
        .first()
    )
    if not calc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found."
        )

    db.delete(calc)
    db.commit()
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")  # pragma: no cover
