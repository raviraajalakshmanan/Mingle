from app.core.logging import REDACTED, redact


def test_redacts_sensitive_keys_at_any_depth():
    raw = {
        "catchup_id": "abc",
        "name": "Priya",
        "budget_min": 200,
        "budget_max": 500,
        "nested": {"contribution": 100, "interests": ["tea"], "count": 8},
        "list": [{"budget": 999, "ok": 1}],
    }
    out = redact(raw)

    # Non-sensitive survives.
    assert out["catchup_id"] == "abc"
    assert out["nested"]["count"] == 8
    assert out["list"][0]["ok"] == 1

    # Sensitive redacted everywhere.
    assert out["name"] == REDACTED
    assert out["budget_min"] == REDACTED
    assert out["budget_max"] == REDACTED
    assert out["nested"]["contribution"] == REDACTED
    assert out["nested"]["interests"] == REDACTED
    assert out["list"][0]["budget"] == REDACTED
