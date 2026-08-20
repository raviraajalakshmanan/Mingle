import pytest
from fastapi.testclient import TestClient

from app.core.auth import User, get_current_user
from app.db import repo
from app.main import app

client = TestClient(app)

FAKE_USER = User(id="user-123", email="creator@example.com", display_name="Creator")


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    yield
    app.dependency_overrides.clear()


def _valid_body():
    return {
        "title": "Saturday evening catch-up",
        "type": "casual",
        "location": "Indiranagar",
        "slots": [
            {"starts_at": "2026-09-05T17:00:00Z", "ends_at": "2026-09-05T19:00:00Z"},
            {"starts_at": "2026-09-05T19:00:00Z", "ends_at": "2026-09-05T21:00:00Z"},
        ],
    }


def test_create_catchup(monkeypatch):
    monkeypatch.setattr(repo, "upsert_profile", lambda *a, **k: None)
    monkeypatch.setattr(
        repo,
        "create_catchup",
        lambda owner_id, data, slots: {
            "id": "catch-1",
            "link_token": "LINKTOK",
            "result_token": "RESULTTOK",
        },
    )

    resp = client.post("/api/catchups", json=_valid_body())
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == "catch-1"
    assert body["invite_url"].endswith("/r/LINKTOK")
    assert body["result_url"].endswith("/result/RESULTTOK")


def test_create_rejects_bad_slot(monkeypatch):
    monkeypatch.setattr(repo, "upsert_profile", lambda *a, **k: None)
    body = _valid_body()
    body["slots"] = [{"starts_at": "2026-09-05T19:00:00Z", "ends_at": "2026-09-05T17:00:00Z"}]
    resp = client.post("/api/catchups", json=body)
    assert resp.status_code == 422


def test_create_rejects_empty_slots():
    body = _valid_body()
    body["slots"] = []
    resp = client.post("/api/catchups", json=body)
    assert resp.status_code == 422


def test_list_catchups(monkeypatch):
    monkeypatch.setattr(
        repo,
        "list_catchups",
        lambda owner_id: [
            {
                "id": "c1",
                "title": "Trip",
                "type": "trip",
                "status": "open",
                "created_at": "2026-09-01T10:00:00Z",
                "responses": [{"count": 3}],
            }
        ],
    )
    resp = client.get("/api/catchups")
    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["response_count"] == 3


def test_get_catchup_owner_ok(monkeypatch):
    monkeypatch.setattr(
        repo,
        "get_catchup",
        lambda cid: {
            "id": "c1",
            "owner_id": FAKE_USER.id,
            "title": "Dinner",
            "type": "food",
            "status": "open",
            "slots": [
                {
                    "id": "s1",
                    "starts_at": "2026-09-05T19:00:00Z",
                    "ends_at": "2026-09-05T21:00:00Z",
                    "sort_order": 0,
                }
            ],
            "responses": [{"count": 0}],
        },
    )
    resp = client.get("/api/catchups/c1")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Dinner"
    assert len(resp.json()["slots"]) == 1


def test_get_catchup_not_owned_is_404(monkeypatch):
    monkeypatch.setattr(
        repo,
        "get_catchup",
        lambda cid: {"id": "c1", "owner_id": "someone-else", "title": "x", "type": "food",
                     "status": "open", "slots": [], "responses": [{"count": 0}]},
    )
    resp = client.get("/api/catchups/c1")
    assert resp.status_code == 404


def test_get_catchup_missing_is_404(monkeypatch):
    monkeypatch.setattr(repo, "get_catchup", lambda cid: None)
    resp = client.get("/api/catchups/nope")
    assert resp.status_code == 404


def test_close_catchup_owner_ok(monkeypatch):
    monkeypatch.setattr(repo, "get_catchup", lambda cid: {"id": cid, "owner_id": FAKE_USER.id})
    called = {}
    monkeypatch.setattr(repo, "set_catchup_status", lambda cid, s: called.update(cid=cid, s=s))
    resp = client.post("/api/catchups/c1/close")
    assert resp.status_code == 200
    assert resp.json() == {"status": "closed"}
    assert called == {"cid": "c1", "s": "closed"}


def test_close_catchup_not_owned_404(monkeypatch):
    monkeypatch.setattr(repo, "get_catchup", lambda cid: {"id": cid, "owner_id": "other"})
    resp = client.post("/api/catchups/c1/close")
    assert resp.status_code == 404


def test_requires_auth():
    # Drop the auth override so the real dependency runs with no bearer token.
    app.dependency_overrides.clear()
    resp = client.get("/api/catchups")
    assert resp.status_code == 401
