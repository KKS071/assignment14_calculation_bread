# File: tests/e2e/conftest.py
# Purpose: Start the FastAPI app in a background thread for the E2E test session,
#          then provide Playwright browser/page fixtures. No manual server needed.
import socket
import threading
import time

import pytest
import uvicorn

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

HOST = "127.0.0.1"
PORT = 8001  # separate port so it never collides with a dev server on 8000
BASE_URL = f"http://{HOST}:{PORT}"


# ── Live server ───────────────────────────────────────────────────────────────

class _ServerThread(threading.Thread):
    """Run uvicorn in a daemon thread; stops cleanly via server.should_exit."""

    def __init__(self):
        super().__init__(daemon=True)
        from app.main import app
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)

        self.config = uvicorn.Config(
            app,
            host=HOST,
            port=PORT,
            log_level="error",
            loop="asyncio",
        )
        self.server = uvicorn.Server(self.config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def _wait_for_server(host: str, port: int, timeout: float = 10.0):
    """Block until the server accepts TCP connections or raise on timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(
        f"E2E server on {host}:{port} did not start within {timeout}s"
    )


@pytest.fixture(scope="session", autouse=True)
def live_server():
    """Session-scoped: start the app once, share across all E2E tests."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("playwright package not installed — run: pip install playwright && playwright install")

    thread = _ServerThread()
    thread.start()
    _wait_for_server(HOST, PORT)

    yield BASE_URL

    thread.stop()
    thread.join(timeout=5)


# ── Playwright fixtures ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def playwright_instance(live_server):
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    b = playwright_instance.chromium.launch(headless=True)
    yield b
    b.close()


@pytest.fixture()
def page(browser, live_server):
    """Fresh browser page for each test; base URL is the live server."""
    p = browser.new_page()
    p.set_default_timeout(8000)
    yield p
    p.close()
