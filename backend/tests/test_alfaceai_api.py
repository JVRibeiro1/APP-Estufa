"""Backend tests for AlfaceAI Greenhouse API"""
import os
import uuid
import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"
API = f"{BASE_URL}/api"

DEMO_EMAIL = "demo@estufa.com"
DEMO_PASSWORD = "demo1234"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- Auth ----------
class TestAuth:
    def test_login_success(self):
        r = requests.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data and data["access_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == DEMO_EMAIL
        assert data["user"]["id"]

    def test_login_wrong_password(self):
        r = requests.post(f"{API}/auth/login", json={"email": DEMO_EMAIL, "password": "wrongpass"}, timeout=20)
        assert r.status_code == 401

    def test_register_new_user(self):
        email = f"test_{uuid.uuid4().hex[:8]}@estufa.com"
        r = requests.post(f"{API}/auth/register", json={"email": email, "password": "pass1234", "name": "TEST User"}, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["access_token"]
        assert data["user"]["email"] == email

    def test_me_with_token(self, auth_headers):
        r = requests.get(f"{API}/auth/me", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        assert r.json()["email"] == DEMO_EMAIL

    def test_me_without_token(self):
        r = requests.get(f"{API}/auth/me", timeout=20)
        assert r.status_code == 401


# ---------- Sensors ----------
class TestSensors:
    def test_latest_sensor(self, auth_headers):
        r = requests.get(f"{API}/sensors/latest", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data is not None
        for key in ["temperature", "humidity", "soil_moisture", "light", "co2", "id", "timestamp"]:
            assert key in data

    def test_history(self, auth_headers):
        r = requests.get(f"{API}/sensors/history", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0

    def test_public_push_sensor(self, auth_headers):
        payload = {"temperature": 24.5, "humidity": 68.0, "soil_moisture": 55.0, "light": 700, "co2": 430}
        r = requests.post(f"{API}/sensors/data", json=payload, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data["temperature"] == 24.5
        # Verify persisted -> latest should reflect this
        r2 = requests.get(f"{API}/sensors/latest", headers=auth_headers, timeout=20)
        assert r2.status_code == 200
        assert r2.json()["id"] == data["id"]


# ---------- Alerts ----------
class TestAlerts:
    def test_list_alerts_seeded(self, auth_headers):
        r = requests.get(f"{API}/alerts", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        diseases = [a["disease"] for a in data]
        assert any("Míldio" in d for d in diseases)
        assert any("Septoriose" in d for d in diseases)
        assert any("Sclerotinia" in d for d in diseases)

    def test_unread_count(self, auth_headers):
        r = requests.get(f"{API}/alerts/unread-count", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        assert isinstance(r.json()["count"], int)

    def test_unread_only_filter(self, auth_headers):
        r = requests.get(f"{API}/alerts?unread_only=true", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        for a in r.json():
            assert a["read"] is False

    def test_get_marks_read(self, auth_headers):
        # get an unread alert
        r = requests.get(f"{API}/alerts?unread_only=true", headers=auth_headers, timeout=20)
        alerts = r.json()
        if not alerts:
            pytest.skip("No unread alerts")
        aid = alerts[0]["id"]
        r2 = requests.get(f"{API}/alerts/{aid}", headers=auth_headers, timeout=20)
        assert r2.status_code == 200
        assert r2.json()["read"] is True

    def test_resolve_alert(self, auth_headers):
        r = requests.get(f"{API}/alerts", headers=auth_headers, timeout=20)
        alerts = [a for a in r.json() if not a["resolved"]]
        if not alerts:
            pytest.skip("No unresolved alerts")
        aid = alerts[0]["id"]
        r2 = requests.post(f"{API}/alerts/{aid}/resolve", headers=auth_headers, timeout=20)
        assert r2.status_code == 200
        assert r2.json()["resolved"] is True

    def test_webhook_creates_alert(self, auth_headers):
        payload = {
            "disease": "TEST_Míldio Detection",
            "confidence": 0.85,
            "severity": "warning",
            "plant_zone": "TEST Zone",
            "description": "webhook test",
            "recommendations": ["r1", "r2"],
        }
        r = requests.post(f"{API}/alerts/webhook", json=payload, timeout=20)
        assert r.status_code == 200
        new_id = r.json()["id"]
        # Verify appears in list
        r2 = requests.get(f"{API}/alerts", headers=auth_headers, timeout=20)
        assert any(a["id"] == new_id for a in r2.json())
