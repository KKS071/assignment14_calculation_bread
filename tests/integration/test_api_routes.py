# File: tests/integration/test_api_routes.py
# Purpose: Integration tests for health check and HTML page routes.


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_login_page(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_register_page(client):
    resp = client.get("/register")
    assert resp.status_code == 200


def test_dashboard_page(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200


def test_view_calculation_page(client):
    resp = client.get("/dashboard/view/some-calc-id")
    assert resp.status_code == 200


def test_edit_calculation_page(client):
    resp = client.get("/dashboard/edit/some-calc-id")
    assert resp.status_code == 200