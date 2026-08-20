"""Structured JSON logging with private-field redaction.

CRITICAL (docs/03-lld.md §7): budget and identity fields must never be logged.
Any dict passed via `extra={"data": {...}}` is scrubbed of sensitive keys before
it reaches the log output.
"""

import json
import logging
import sys
from typing import Any

# Keys that must never appear in logs, at any nesting depth.
SENSITIVE_KEYS = frozenset(
    {
        "budget_min",
        "budget_max",
        "contribution",
        "interests",
        "name",
        "budget",
        "email",
        "supabase_service_key",
        "supabase_jwt_secret",
        "authorization",
        "token",
        "link_token",
        "result_token",
    }
)

REDACTED = "[REDACTED]"


def redact(value: Any) -> Any:
    """Recursively replace values of sensitive keys with a placeholder."""
    if isinstance(value, dict):
        return {
            k: (REDACTED if k.lower() in SENSITIVE_KEYS else redact(v)) for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        data = getattr(record, "data", None)
        if data is not None:
            payload["data"] = redact(data)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
