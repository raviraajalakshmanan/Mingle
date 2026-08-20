"""Data access via Supabase PostgREST (service role).

All writes and privacy-sensitive reads go through here. The service role bypasses
RLS, so every caller in the API layer must enforce its own authorization first.
Functions raise httpx.HTTPStatusError on unexpected DB errors.
"""

from typing import Any

from app.core.db import get_client
from app.core.tokens import new_token

_RETURN_REP = {"Prefer": "return=representation"}


# --- profiles ----------------------------------------------------------------


def upsert_profile(user_id: str, email: str | None, display_name: str | None) -> None:
    """Ensure a profile row exists for a signed-in user (idempotent)."""
    client = get_client()
    resp = client.post(
        "/profiles",
        params={"on_conflict": "id"},
        headers={"Prefer": "resolution=merge-duplicates"},
        json={"id": user_id, "email": email, "display_name": display_name},
    )
    resp.raise_for_status()


# --- catchups ----------------------------------------------------------------


def create_catchup(owner_id: str, data: dict[str, Any], slots: list[dict[str, Any]]) -> dict:
    """Insert a catch-up plus its slots. Returns the created catch-up row."""
    client = get_client()
    payload = {
        **data,
        "owner_id": owner_id,
        "link_token": new_token(),
        "result_token": new_token(),
    }
    resp = client.post("/catchups", headers=_RETURN_REP, json=payload)
    resp.raise_for_status()
    catchup = resp.json()[0]

    if slots:
        rows = [
            {**s, "catchup_id": catchup["id"], "sort_order": i} for i, s in enumerate(slots)
        ]
        s_resp = client.post("/slots", headers=_RETURN_REP, json=rows)
        s_resp.raise_for_status()

    return catchup


def list_catchups(owner_id: str) -> list[dict]:
    client = get_client()
    resp = client.get(
        "/catchups",
        params={
            "owner_id": f"eq.{owner_id}",
            "select": "id,title,type,status,created_at,responses(count)",
            "order": "created_at.desc",
        },
    )
    resp.raise_for_status()
    return resp.json()


def get_catchup(catchup_id: str) -> dict | None:
    """Fetch a single catch-up with its slots and response count, or None."""
    client = get_client()
    resp = client.get(
        "/catchups",
        params={
            "id": f"eq.{catchup_id}",
            "select": "*,slots(*),responses(count)",
        },
    )
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None


def set_catchup_status(catchup_id: str, status: str) -> None:
    client = get_client()
    resp = client.patch(
        "/catchups", params={"id": f"eq.{catchup_id}"}, json={"status": status}
    )
    resp.raise_for_status()


def response_count(catchup: dict) -> int:
    """Extract the embedded responses count from a PostgREST result row."""
    embedded = catchup.get("responses")
    if isinstance(embedded, list) and embedded:
        return int(embedded[0].get("count", 0))
    return 0


def get_catchup_by_link_token(link_token: str) -> dict | None:
    """Fetch a catch-up by its invite token, with slots and the creator's name."""
    client = get_client()
    resp = client.get(
        "/catchups",
        params={
            "link_token": f"eq.{link_token}",
            "select": "*,slots(*),profiles(display_name),responses(count)",
        },
    )
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None


# --- responses (PRIVATE, never read back per-row via the API) ---------------


def create_response(catchup_id: str, payload: dict, slot_ids: list[str]) -> None:
    """Insert one private response plus its slot links. Returns nothing."""
    client = get_client()
    body = {
        "catchup_id": catchup_id,
        "name": payload["name"],
        "companions": payload["companions"],
        "budget_min": payload["budget_min"],
        "budget_max": payload["budget_max"],
        "contribution": payload["contribution"],
        "interests": payload["interests"],
    }
    resp = client.post("/responses", headers=_RETURN_REP, json=body)
    resp.raise_for_status()
    response_id = resp.json()[0]["id"]

    links = [{"response_id": response_id, "slot_id": sid} for sid in slot_ids]
    link_resp = client.post("/response_slots", json=links)
    link_resp.raise_for_status()


# --- results aggregation -----------------------------------------------------

_RESULTS_SELECT = (
    "*,slots(*),"
    "responses(id,name,companions,budget_min,budget_max,contribution,interests,"
    "response_slots(slot_id))"
)


def get_catchup_for_results(*, catchup_id: str | None = None, result_token: str | None = None):
    """Fetch a catch-up with its slots and all responses (incl. each response's
    selected slot ids), by id or by result token. Returns the row or None.

    This is the only place raw responses are read, and they are consumed purely
    to compute aggregates, never returned per-row (invariant I1)."""
    client = get_client()
    if catchup_id is not None:
        params = {"id": f"eq.{catchup_id}", "select": _RESULTS_SELECT}
    elif result_token is not None:
        params = {"result_token": f"eq.{result_token}", "select": _RESULTS_SELECT}
    else:
        raise ValueError("catchup_id or result_token required")
    resp = client.get("/catchups", params=params)
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None
