from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "applications.db"

    monkeypatch.setenv("DB_PATH", str(db_path))
    monkeypatch.setenv("API_AUTO_MIGRATE", "true")
    monkeypatch.setenv("API_JWT_SECRET", "test-secret-key-which-is-at-least-32-bytes")
    monkeypatch.setenv("API_JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_LOGIN", "admin")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_PASSWORD", "admin_pass_123")
    monkeypatch.setenv("ADMIN_BOOTSTRAP_NAME", "Admin User")

    tg_dir = Path(__file__).resolve().parents[1]
    tg_dir_str = str(tg_dir)
    if tg_dir_str not in sys.path:
        sys.path.insert(0, tg_dir_str)

    for module_name in list(sys.modules):
        if module_name == "database.db" or module_name.startswith("api.") or module_name.startswith("migrations."):
            sys.modules.pop(module_name, None)

    from api.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client, db_path


def login(client: TestClient, login_value: str, password_value: str) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"login": login_value, "password": password_value},
    )
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_admin_login_and_me(client):
    test_client, _ = client

    auth = login(test_client, "admin", "admin_pass_123")
    me_response = test_client.get(
        "/api/auth/me",
        headers=auth_headers(auth["access_token"]),
    )

    assert me_response.status_code == 200
    me = me_response.json()
    assert me["role"] == "admin"
    assert me["login"] == "admin"


def test_investor_ownership_scope(client):
    test_client, db_path = client

    admin_auth = login(test_client, "admin", "admin_pass_123")
    admin_headers = auth_headers(admin_auth["access_token"])

    investor_1 = test_client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "login": "investor1",
            "password": "investor_pass_1",
            "name": "Investor One",
            "role": "investor",
            "percent": 30,
        },
    )
    assert investor_1.status_code == 201, investor_1.text

    investor_2 = test_client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "login": "investor2",
            "password": "investor_pass_2",
            "name": "Investor Two",
            "role": "investor",
            "percent": 40,
        },
    )
    assert investor_2.status_code == 201, investor_2.text

    inv1_id = investor_1.json()["id"]
    inv2_id = investor_2.json()["id"]

    campaign_1 = test_client.post(
        "/api/campaigns",
        headers=admin_headers,
        json={
            "investor_id": inv1_id,
            "name": "Campaign A",
            "budget": 1000,
            "status": "active",
        },
    )
    assert campaign_1.status_code == 201, campaign_1.text

    campaign_2 = test_client.post(
        "/api/campaigns",
        headers=admin_headers,
        json={
            "investor_id": inv2_id,
            "name": "Campaign B",
            "budget": 800,
            "status": "active",
        },
    )
    assert campaign_2.status_code == 201, campaign_2.text

    camp1_id = campaign_1.json()["id"]
    camp2_id = campaign_2.json()["id"]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(db_path) as conn:
        cur1 = conn.execute(
            """
            INSERT INTO applications (
                telegram_id, username, first_name, phone, age, citizenship, source,
                contacted, submitted_at, campaign_id, revenue, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (111, "u1", "One", "+70000000001", 21, "RU", "camp_1", 0, now, camp1_id, 5000, "approved"),
        )
        app1_id = cur1.lastrowid
        cur2 = conn.execute(
            """
            INSERT INTO applications (
                telegram_id, username, first_name, phone, age, citizenship, source,
                contacted, submitted_at, campaign_id, revenue, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (222, "u2", "Two", "+70000000002", 23, "RU", "camp_2", 0, now, camp2_id, 7000, "approved"),
        )
        app2_id = cur2.lastrowid
        conn.commit()

    investor_auth = login(test_client, "investor1", "investor_pass_1")
    investor_headers = auth_headers(investor_auth["access_token"])

    list_response = test_client.get("/api/applications", headers=investor_headers)
    assert list_response.status_code == 200, list_response.text
    rows = list_response.json()

    assert len(rows) == 1
    assert rows[0]["campaign_id"] == camp1_id
    assert rows[0]["id"] == app1_id

    forbidden_update = test_client.put(
        f"/api/applications/{app2_id}",
        headers=investor_headers,
        json={"status": "rejected", "revenue": 100},
    )
    assert forbidden_update.status_code in {403, 404}
