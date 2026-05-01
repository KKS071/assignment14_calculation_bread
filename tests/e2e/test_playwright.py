# File: tests/e2e/test_playwright.py
# Purpose: Playwright E2E tests — positive and negative BREAD scenarios via browser UI.
#          The live_server fixture (conftest.py) starts uvicorn automatically on port 8001.
import re
import uuid
import pytest

pytest.importorskip("playwright")

from playwright.sync_api import Page, expect
from tests.e2e.conftest import BASE_URL


# ── Helpers ───────────────────────────────────────────────────────────────────

def unique_user():
    suffix = uuid.uuid4().hex[:8]
    return {
        "username": f"e2euser_{suffix}",
        "email": f"e2e_{suffix}@test.com",
        "password": "E2ePass1!",
        "first_name": "E2E",
        "last_name": "Tester",
    }


def register_and_login(page: Page, user: dict):
    page.goto(f"{BASE_URL}/register")
    page.fill("#first_name", user["first_name"])
    page.fill("#last_name", user["last_name"])
    page.fill("#email", user["email"])
    page.fill("#username", user["username"])
    page.fill("#password", user["password"])
    page.fill("#confirm_password", user["password"])
    page.click("button[onclick='handleRegister()']")
    page.wait_for_url(re.compile(r"/login"), timeout=8000)

    page.fill("#username", user["username"])
    page.fill("#password", user["password"])
    page.click("button[onclick='handleLogin()']")
    page.wait_for_url(re.compile(r"/dashboard"), timeout=8000)


# ── Register / Login ──────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_register_page_loads(page: Page):
    page.goto(f"{BASE_URL}/register")
    expect(page.locator("h2")).to_contain_text("Create Account")


@pytest.mark.e2e
def test_login_page_loads(page: Page):
    page.goto(f"{BASE_URL}/login")
    expect(page.locator("h2")).to_contain_text("Login")


@pytest.mark.e2e
def test_register_and_login_flow(page: Page):
    user = unique_user()
    register_and_login(page, user)
    expect(page).to_have_url(re.compile(r"/dashboard"))


@pytest.mark.e2e
def test_register_password_mismatch_shows_error(page: Page):
    page.goto(f"{BASE_URL}/register")
    page.fill("#first_name", "Bad")
    page.fill("#last_name", "User")
    page.fill("#email", f"bad_{uuid.uuid4().hex[:6]}@test.com")
    page.fill("#username", f"bad_{uuid.uuid4().hex[:6]}")
    page.fill("#password", "E2ePass1!")
    page.fill("#confirm_password", "DifferentPass9!")
    page.click("button[onclick='handleRegister()']")
    # JS validation fires before submit — stays on register page
    expect(page).to_have_url(re.compile(r"/register"))
    expect(page.locator("#error-msg")).to_be_visible()


@pytest.mark.e2e
def test_login_wrong_password_shows_error(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.fill("#username", "nonexistentuser_xyz")
    page.fill("#password", "WrongPass1!")
    page.click("button[onclick='handleLogin()']")
    # Should stay on login and show error
    expect(page).not_to_have_url(re.compile(r"/dashboard"))
    expect(page.locator("#error-msg")).to_be_visible()


# ── Browse ────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_dashboard_shows_calculations_container(page: Page):
    user = unique_user()
    register_and_login(page, user)
    expect(page).to_have_url(re.compile(r"/dashboard"))
    expect(page.locator("#calculations-list")).to_be_visible()


# ── Add ───────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_create_addition(page: Page):
    user = unique_user()
    register_and_login(page, user)

    page.select_option("#operation", "addition")
    page.fill("#num1", "10")
    page.fill("#num2", "5")
    page.click("#calculate-btn")

    expect(page.locator("#result-box")).to_be_visible()
    expect(page.locator("#result-value")).to_contain_text("15")


@pytest.mark.e2e
def test_create_subtraction(page: Page):
    user = unique_user()
    register_and_login(page, user)

    page.select_option("#operation", "subtraction")
    page.fill("#num1", "20")
    page.fill("#num2", "8")
    page.click("#calculate-btn")

    expect(page.locator("#result-value")).to_contain_text("12")


@pytest.mark.e2e
def test_create_multiplication(page: Page):
    user = unique_user()
    register_and_login(page, user)

    page.select_option("#operation", "multiplication")
    page.fill("#num1", "6")
    page.fill("#num2", "7")
    page.click("#calculate-btn")

    expect(page.locator("#result-value")).to_contain_text("42")


@pytest.mark.e2e
def test_create_division(page: Page):
    user = unique_user()
    register_and_login(page, user)

    page.select_option("#operation", "division")
    page.fill("#num1", "20")
    page.fill("#num2", "4")
    page.click("#calculate-btn")

    expect(page.locator("#result-value")).to_contain_text("5")


@pytest.mark.e2e
def test_create_division_by_zero_shows_error(page: Page):
    user = unique_user()
    register_and_login(page, user)

    page.select_option("#operation", "division")
    page.fill("#num1", "10")
    page.fill("#num2", "0")
    page.click("#calculate-btn")

    # JS guard catches divide-by-zero before the API call
    expect(page.locator("#calc-error")).to_be_visible()
    expect(page.locator("#calc-error")).to_contain_text("zero")


# ── Read ──────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_view_calculation(page: Page):
    user = unique_user()
    register_and_login(page, user)

    page.select_option("#operation", "addition")
    page.fill("#num1", "3")
    page.fill("#num2", "7")
    page.click("#calculate-btn")
    page.wait_for_selector("#calc-success:visible", timeout=5000)

    page.locator(".view-btn").first.click()
    expect(page).to_have_url(re.compile(r"/view/"))
    expect(page.locator(".detail-table")).to_contain_text("10")


# ── Edit ──────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_edit_calculation(page: Page):
    user = unique_user()
    register_and_login(page, user)

    page.select_option("#operation", "multiplication")
    page.fill("#num1", "3")
    page.fill("#num2", "3")
    page.click("#calculate-btn")
    page.wait_for_selector("#calc-success:visible", timeout=5000)

    page.locator(".edit-btn").first.click()
    expect(page).to_have_url(re.compile(r"/edit/"))

    page.fill("#num1", "5")
    page.fill("#num2", "6")
    page.click("#save-btn")

    expect(page.locator("#success-msg")).to_be_visible()
    expect(page.locator("#success-msg")).to_contain_text("30")


# ── Delete ────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_delete_calculation(page: Page):
    user = unique_user()
    register_and_login(page, user)

    # Create a calculation to delete
    page.select_option("#operation", "subtraction")
    page.fill("#num1", "100")
    page.fill("#num2", "1")
    page.click("#calculate-btn")
    page.wait_for_selector("#calc-success:visible", timeout=5000)

    # Accept the confirm dialog automatically
    page.on("dialog", lambda d: d.accept())

    initial_count = page.locator(".calculation-row").count()
    page.locator(".delete-btn").first.click()
    page.wait_for_timeout(1500)

    expect(page.locator(".calculation-row")).to_have_count(initial_count - 1)


# ── Unauthorized ──────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_dashboard_without_login_shows_login_page(page: Page):
    # Clear any stored token
    page.goto(f"{BASE_URL}/login")
    page.evaluate("localStorage.clear()")

    page.goto(f"{BASE_URL}/dashboard")
    # JS on dashboard.html redirects to /login when no token is found
    expect(page).to_have_url(re.compile(r"/login"))
