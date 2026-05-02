# File: tests/e2e/test_playwright.py
# Purpose: Playwright E2E tests — positive and negative BREAD scenarios with multi-value inputs.
#          Selectors match the actual button IDs in the templates (no onclick attributes).
import re
import uuid
import pytest

pytest.importorskip("playwright")

from playwright.sync_api import Page, expect
from tests.e2e.conftest import BASE_URL


# ── Helpers ───────────────────────────────────────────────────────────────────

def unique_user():
    s = uuid.uuid4().hex[:8]
    return {
        "username":   f"e2e_{s}",
        "email":      f"e2e_{s}@test.com",
        "password":   "E2ePass1!",
        "first_name": "E2E",
        "last_name":  "Tester",
    }


def register_and_login(page: Page, user: dict):
    """Register then log in; ends on /dashboard."""
    # ── Register ──
    page.goto(f"{BASE_URL}/register")
    page.fill("#first_name",       user["first_name"])
    page.fill("#last_name",        user["last_name"])
    page.fill("#email",            user["email"])
    page.fill("#username",         user["username"])
    page.fill("#password",         user["password"])
    page.fill("#confirm_password", user["password"])
    page.click("#register-btn")                          # ← correct ID
    page.wait_for_url(re.compile(r"/login"), timeout=8000)

    # ── Login ──
    page.fill("#username", user["username"])
    page.fill("#password", user["password"])
    page.click("#login-btn")                             # ← correct ID
    page.wait_for_url(re.compile(r"/dashboard"), timeout=8000)


def add_calc(page: Page, op: str, values: str):
    """Fill the dashboard form and click Calculate & Save."""
    page.select_option("#operation", op)
    page.fill("#inputs-field", values)
    page.click("#calculate-btn")                         # ← correct ID


# ── Page loads ────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_home_page_loads(page: Page):
    page.goto(BASE_URL)
    expect(page.locator("h1")).to_contain_text("CalcApp")


@pytest.mark.e2e
def test_calculator_icon_visible_on_home(page: Page):
    page.goto(BASE_URL)
    expect(page.locator(".hero-icon svg")).to_be_visible()


@pytest.mark.e2e
def test_register_page_loads(page: Page):
    page.goto(f"{BASE_URL}/register")
    expect(page.locator("h2")).to_contain_text("Create Account")


@pytest.mark.e2e
def test_login_page_loads(page: Page):
    page.goto(f"{BASE_URL}/login")
    expect(page.locator("h2")).to_contain_text("Login")


# ── Auth — positive ───────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_register_and_login_flow(page: Page):
    user = unique_user()
    register_and_login(page, user)
    expect(page).to_have_url(re.compile(r"/dashboard"))


@pytest.mark.e2e
def test_navbar_shows_dashboard_after_login(page: Page):
    user = unique_user()
    register_and_login(page, user)
    expect(page.locator("#nav-dashboard")).to_be_visible()
    expect(page.locator("#nav-logout")).to_be_visible()


# ── Auth — negative ───────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_register_password_mismatch_shows_error(page: Page):
    page.goto(f"{BASE_URL}/register")
    page.fill("#first_name",       "Bad")
    page.fill("#last_name",        "User")
    page.fill("#email",            f"bad_{uuid.uuid4().hex[:6]}@test.com")
    page.fill("#username",         f"bad_{uuid.uuid4().hex[:6]}")
    page.fill("#password",         "E2ePass1!")
    page.fill("#confirm_password", "Different9!")
    page.click("#register-btn")                          # ← correct ID
    expect(page.locator("#error-msg")).to_be_visible()
    expect(page).not_to_have_url(re.compile(r"/dashboard"))


@pytest.mark.e2e
def test_login_wrong_password_shows_error(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.fill("#username", "nonexistent_user_xyz")
    page.fill("#password", "WrongPass1!")
    page.click("#login-btn")                             # ← correct ID
    expect(page.locator("#error-msg")).to_be_visible()
    expect(page).not_to_have_url(re.compile(r"/dashboard"))


@pytest.mark.e2e
def test_dashboard_without_login_redirects(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.evaluate("localStorage.clear()")
    page.goto(f"{BASE_URL}/dashboard")
    expect(page).to_have_url(re.compile(r"/login"))


# ── Add — positive (multi-value) ──────────────────────────────────────────────

@pytest.mark.e2e
def test_add_addition_two_values(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "10, 5")
    expect(page.locator("#result-value")).to_contain_text("15")


@pytest.mark.e2e
def test_add_addition_three_values(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "10, 5, 3")
    expect(page.locator("#result-value")).to_contain_text("18")


@pytest.mark.e2e
def test_add_subtraction_multi(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "subtraction", "100, 30, 20")
    expect(page.locator("#result-value")).to_contain_text("50")


@pytest.mark.e2e
def test_add_multiplication_multi(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "multiplication", "2, 3, 4")
    expect(page.locator("#result-value")).to_contain_text("24")


@pytest.mark.e2e
def test_add_division_multi(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "division", "120, 2, 3, 4")
    expect(page.locator("#result-value")).to_contain_text("5")


@pytest.mark.e2e
def test_add_five_values(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "1, 2, 3, 4, 5")
    expect(page.locator("#result-value")).to_contain_text("15")


@pytest.mark.e2e
def test_inputs_show_as_pills(page: Page):
    register_and_login(page, unique_user())
    page.select_option("#operation", "addition")
    page.fill("#inputs-field", "10, 20, 30")
    page.wait_for_timeout(300)
    expect(page.locator(".input-pill")).to_have_count(3)


@pytest.mark.e2e
def test_success_message_shown_after_add(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "7, 8")
    expect(page.locator("#calc-success")).to_be_visible()


# ── Add — negative ────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_add_invalid_non_numeric_shows_error(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "abc, def")
    expect(page.locator("#calc-error")).to_be_visible()


@pytest.mark.e2e
def test_add_only_one_value_shows_error(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "5")
    expect(page.locator("#calc-error")).to_be_visible()


@pytest.mark.e2e
def test_add_empty_input_shows_error(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "")
    expect(page.locator("#calc-error")).to_be_visible()


@pytest.mark.e2e
def test_add_division_by_zero_shows_error(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "division", "10, 0")
    expect(page.locator("#calc-error")).to_contain_text("zero")


# ── Browse ────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_browse_shows_calculations_list(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "1, 2")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    add_calc(page, "subtraction", "10, 3")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    expect(page.locator(".calculation-row")).to_have_count(2, timeout=5000)


@pytest.mark.e2e
def test_browse_shows_badges(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "multiplication", "3, 4")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    expect(page.locator(".badge-multiplication")).to_be_visible()


@pytest.mark.e2e
def test_browse_empty_shows_message(page: Page):
    register_and_login(page, unique_user())
    expect(page.locator(".empty-msg")).to_be_visible(timeout=5000)


# ── Read ──────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_read_view_page_shows_details(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "3, 7")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    page.locator(".view-btn").first.click()
    expect(page).to_have_url(re.compile(r"/view/"))
    expect(page.locator(".detail-table")).to_contain_text("10")


@pytest.mark.e2e
def test_read_shows_all_inputs(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "10, 20, 30")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    page.locator(".view-btn").first.click()
    expect(page).to_have_url(re.compile(r"/view/"))
    for val in ["10", "20", "30"]:
        expect(page.locator(".detail-table")).to_contain_text(val)


@pytest.mark.e2e
def test_read_shows_edit_button(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "1, 2")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    page.locator(".view-btn").first.click()
    expect(page.locator("#edit-link")).to_be_visible()


# ── Edit ──────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_edit_updates_result(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "3, 3")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    page.locator(".edit-btn").first.click()
    expect(page).to_have_url(re.compile(r"/edit/"))
    page.fill("#inputs-field", "5, 6, 7")
    page.click("#save-btn")                              # ← correct ID
    expect(page.locator("#success-msg")).to_be_visible()
    expect(page.locator("#success-msg")).to_contain_text("18")


@pytest.mark.e2e
def test_edit_form_prefilled(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "multiplication", "4, 5")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    page.locator(".edit-btn").first.click()
    expect(page).to_have_url(re.compile(r"/edit/"))
    expect(page.locator("#operation")).to_have_value("multiplication")


@pytest.mark.e2e
def test_edit_division_by_zero_shows_error(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "division", "20, 4")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    page.locator(".edit-btn").first.click()
    page.wait_for_url(re.compile(r"/edit/"))
    page.fill("#inputs-field", "10, 0")
    page.click("#save-btn")                              # ← correct ID
    expect(page.locator("#error-msg")).to_be_visible()
    expect(page.locator("#error-msg")).to_contain_text("zero")


# ── Delete ────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_delete_removes_row(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "10, 10")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    add_calc(page, "addition", "20, 20")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    page.wait_for_selector(".calculation-row")
    count_before = page.locator(".calculation-row").count()

    page.on("dialog", lambda d: d.accept())
    page.locator(".delete-btn").first.click()
    page.wait_for_timeout(1500)
    expect(page.locator(".calculation-row")).to_have_count(count_before - 1)


@pytest.mark.e2e
def test_delete_does_not_remove_other_rows(page: Page):
    register_and_login(page, unique_user())
    add_calc(page, "addition", "1, 1")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    add_calc(page, "addition", "99, 1")
    page.wait_for_selector("#calc-success:visible", timeout=5000)
    page.wait_for_selector(".calculation-row")

    page.on("dialog", lambda d: d.accept())
    page.locator(".delete-btn").first.click()
    page.wait_for_timeout(1500)
    expect(page.locator(".calculation-row")).to_have_count(1)
