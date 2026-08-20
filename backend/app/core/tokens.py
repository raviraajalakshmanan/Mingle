"""Unguessable, URL-safe tokens for invite/result links (docs/03-lld.md §7)."""

import secrets


def new_token() -> str:
    # 32 bytes -> 256 bits of entropy, URL-safe.
    return secrets.token_urlsafe(32)
