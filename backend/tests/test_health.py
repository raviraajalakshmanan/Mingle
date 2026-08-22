from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "MigleUp"
    assert "version" in body
    # Reflects whether Supabase env is set; value is env-dependent, so just
    # assert it's a boolean and the probe didn't error.
    assert isinstance(body["supabase_configured"], bool)


def test_health_leaks_no_secrets():
    body = client.get("/api/health").json()
    for forbidden in ("supabase_service_key", "supabase_jwt_secret", "service_key"):
        assert forbidden not in body
