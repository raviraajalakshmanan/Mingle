"""Thin Supabase (PostgREST) access layer using the service role key.

The backend enforces its own authorization in code (docs/03-lld.md §7); RLS on
the database is a second wall. We talk to PostgREST over HTTP with httpx rather
than pulling in a heavier client, keeping the dependency surface small.

M0: connection factory + health check only. CRUD helpers arrive in M1.
"""

from functools import lru_cache

import httpx

from app.core.config import get_settings


@lru_cache
def get_client() -> httpx.Client:
    """Return an httpx client pre-configured for the Supabase REST endpoint.

    Uses the service role key, which bypasses RLS, never expose this client or
    its key to the frontend.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError("Supabase is not configured (set SUPABASE_URL and SUPABASE_SERVICE_KEY)")
    return httpx.Client(
        base_url=f"{settings.supabase_url}/rest/v1",
        headers={
            "apikey": settings.supabase_service_key,
            "Authorization": f"Bearer {settings.supabase_service_key}",
            "Content-Type": "application/json",
        },
        timeout=10.0,
    )


def is_configured() -> bool:
    settings = get_settings()
    return bool(settings.supabase_url and settings.supabase_service_key)
