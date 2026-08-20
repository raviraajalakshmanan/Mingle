"""Supabase JWT verification and the `get_current_user` dependency.

Supports both signing schemes so it works regardless of the project's key setup
(docs/03-lld.md §7):
  - Legacy: HS256 signed with the shared `SUPABASE_JWT_SECRET`.
  - Current: asymmetric (RS256/ES256) verified against the project's JWKS.

Verified tokens must carry aud="authenticated". The returned user carries the
Supabase user id (`sub`), email, and a best-effort display name.
"""

from dataclasses import dataclass
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import get_settings

_bearer = HTTPBearer(auto_error=False)


@dataclass
class User:
    id: str
    email: str | None
    display_name: str | None


@lru_cache
def _jwks() -> dict:
    settings = get_settings()
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10.0)
    resp.raise_for_status()
    return resp.json()


def _decode(token: str) -> dict:
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise _unauthorized("malformed token") from e

    alg = header.get("alg", "")
    common = {"audience": "authenticated", "options": {"verify_aud": True}}

    try:
        if alg == "HS256":
            if not settings.supabase_jwt_secret:
                raise _unauthorized("HS256 token but no JWT secret configured")
            return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], **common)

        # Asymmetric: find the matching key in the JWKS by `kid`.
        kid = header.get("kid")
        key = next((k for k in _jwks().get("keys", []) if k.get("kid") == kid), None)
        if key is None:
            _jwks.cache_clear()  # keys may have rotated; retry once
            key = next((k for k in _jwks().get("keys", []) if k.get("kid") == kid), None)
        if key is None:
            raise _unauthorized("no matching signing key")
        return jwt.decode(token, key, algorithms=[alg], **common)
    except JWTError as e:
        raise _unauthorized(f"invalid token: {e}") from e


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> User:
    if creds is None or not creds.credentials:
        raise _unauthorized("missing bearer token")
    claims = _decode(creds.credentials)
    sub = claims.get("sub")
    if not sub:
        raise _unauthorized("token missing subject")
    meta = claims.get("user_metadata") or {}
    return User(
        id=sub,
        email=claims.get("email"),
        display_name=meta.get("full_name") or meta.get("name") or claims.get("email"),
    )
