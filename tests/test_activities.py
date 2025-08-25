import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="function")
def client(tmp_path, monkeypatch):
    # Use a temp db per test
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    return TestClient(app)


def test_post_activity_and_fetch(client):
    payload = {
        "actor": "user_1",
        "verb": "posted",
        "object": "Hello world",
    }
    r = client.post("/activities", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["actor"] == "user_1"
    assert data["verb"] == "posted"
    assert data["object"] == "Hello world"
    assert "id" in data

    r = client.get("/activities?limit=10")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1
    assert items[0]["actor"] == "user_1"


def test_validation(client):
    r = client.post("/activities", json={"actor": "", "verb": "x", "object": "o"})
    assert r.status_code == 422
