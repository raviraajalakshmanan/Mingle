from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.ratelimit import response_limiter
from app.db import repo
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    response_limiter._hits.clear()
    yield


def _catchup(status="open", deadline=None, max_responses=None, count=0):
    return {
        "id": "c1",
        "status": status,
        "title": "Sat evening",
        "type": "casual",
        "message": None,
        "location": "Indiranagar",
        "deadline": deadline,
        "max_responses": max_responses,
        "responses": [{"count": count}],
        "profiles": {"display_name": "Ravi Raj"},
        "slots": [
            {"id": "s1", "starts_at": "2026-09-05T17:00:00Z", "ends_at": "2026-09-05T19:00:00Z",
             "sort_order": 0},
            {"id": "s2", "starts_at": "2026-09-05T19:00:00Z", "ends_at": "2026-09-05T21:00:00Z",
             "sort_order": 1},
        ],
    }


def _body(**over):
    b = {
        "name": "Priya",
        "slot_ids": ["s1"],
        "companions": 2,
        "budget_min": 200,
        "budget_max": 500,
        "contribution": 100,
        "interests": ["tea", "walk"],
    }
    b.update(over)
    return b


# --- summary ----------------------------------------------------------------


def test_invite_summary_first_name_only(monkeypatch):
    monkeypatch.setattr(repo, "get_catchup_by_link_token", lambda t: _catchup())
    resp = client.get("/api/invite/TOK")
    assert resp.status_code == 200
    body = resp.json()
    assert body["creator_first_name"] == "Ravi"  # first name only
    assert len(body["slots"]) == 2
    # Must not leak internal identifiers.
    assert "owner_id" not in body
    assert "link_token" not in body
    assert "result_token" not in body


def test_invite_summary_404(monkeypatch):
    monkeypatch.setattr(repo, "get_catchup_by_link_token", lambda t: None)
    assert client.get("/api/invite/NOPE").status_code == 404


# --- submit -----------------------------------------------------------------


def test_submit_ok_and_leaks_nothing(monkeypatch):
    captured = {}
    monkeypatch.setattr(repo, "get_catchup_by_link_token", lambda t: _catchup())
    monkeypatch.setattr(
        repo,
        "create_response",
        lambda cid, payload, slot_ids: captured.update(cid=cid, payload=payload, slots=slot_ids),
    )
    resp = client.post("/api/invite/TOK/responses", json=_body())
    assert resp.status_code == 201
    # The ack body must contain ONLY {"ok": true} — no echo of budget/name/slots.
    assert resp.json() == {"ok": True}
    # But the data did reach the repo.
    assert captured["cid"] == "c1"
    assert captured["payload"]["budget_max"] == 500


def test_submit_rejects_foreign_slot(monkeypatch):
    monkeypatch.setattr(repo, "get_catchup_by_link_token", lambda t: _catchup())
    monkeypatch.setattr(repo, "create_response", lambda *a, **k: None)
    resp = client.post("/api/invite/TOK/responses", json=_body(slot_ids=["s1", "sX"]))
    assert resp.status_code == 422


def test_submit_rejects_bad_budget():
    resp = client.post("/api/invite/TOK/responses", json=_body(budget_min=800, budget_max=500))
    assert resp.status_code == 422


def test_submit_rejects_closed(monkeypatch):
    monkeypatch.setattr(repo, "get_catchup_by_link_token", lambda t: _catchup(status="closed"))
    resp = client.post("/api/invite/TOK/responses", json=_body())
    assert resp.status_code == 409


def test_submit_rejects_past_deadline(monkeypatch):
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    monkeypatch.setattr(repo, "get_catchup_by_link_token", lambda t: _catchup(deadline=past))
    resp = client.post("/api/invite/TOK/responses", json=_body())
    assert resp.status_code == 409


def test_submit_allows_future_deadline(monkeypatch):
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    monkeypatch.setattr(repo, "get_catchup_by_link_token", lambda t: _catchup(deadline=future))
    monkeypatch.setattr(repo, "create_response", lambda *a, **k: None)
    resp = client.post("/api/invite/TOK/responses", json=_body())
    assert resp.status_code == 201


def test_submit_honeypot_silently_dropped(monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(repo, "get_catchup_by_link_token", lambda t: _catchup())

    def _create(*a, **k):
        called["n"] += 1

    monkeypatch.setattr(repo, "create_response", _create)
    resp = client.post("/api/invite/TOK/responses", json=_body(website="http://spam"))
    # Bot gets a normal-looking ack but nothing is stored.
    assert resp.status_code == 201
    assert called["n"] == 0


def test_submit_rejected_when_cap_reached(monkeypatch):
    monkeypatch.setattr(
        repo, "get_catchup_by_link_token", lambda t: _catchup(max_responses=2, count=2)
    )
    monkeypatch.setattr(repo, "create_response", lambda *a, **k: None)
    resp = client.post("/api/invite/TOK/responses", json=_body())
    assert resp.status_code == 409


def test_submit_allowed_below_cap(monkeypatch):
    monkeypatch.setattr(
        repo, "get_catchup_by_link_token", lambda t: _catchup(max_responses=5, count=2)
    )
    monkeypatch.setattr(repo, "create_response", lambda *a, **k: None)
    resp = client.post("/api/invite/TOK/responses", json=_body())
    assert resp.status_code == 201


def test_submit_rate_limited(monkeypatch):
    monkeypatch.setattr(repo, "get_catchup_by_link_token", lambda t: _catchup())
    monkeypatch.setattr(repo, "create_response", lambda *a, **k: None)
    codes = [client.post("/api/invite/TOK/responses", json=_body()).status_code for _ in range(12)]
    assert codes.count(201) == 10
    assert codes.count(429) == 2
