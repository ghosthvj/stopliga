"""Logging configuration helpers."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import json
import logging
from typing import Any


SENSITIVE_FIELD_MARKERS = {"password", "secret", "token", "api_key", "key"}
_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("stopliga_log_context", default={})


def _quote(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=True)


def _sanitize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in fields.items():
        key_lower = key.lower()
        if any(marker in key_lower for marker in SENSITIVE_FIELD_MARKERS):
            sanitized[key] = "***"
        else:
            sanitized[key] = value
    return sanitized


class KeyValueFormatter(logging.Formatter):
    """Simple key=value formatter that stays readable in Docker stdout."""

    def format(self, record: logging.LogRecord) -> str:
        fields = getattr(record, "fields", {})
        event = getattr(record, "event", None)
        merged_fields: dict[str, Any] = {}
        merged_fields.update(_LOG_CONTEXT.get({}))
        if isinstance(fields, dict):
            merged_fields.update(fields)
        sanitized = _sanitize_fields(merged_fields)
        payload = {
            "level": record.levelname,
            "logger": record.name,
        }
        if event:
            payload["event"] = event
        message = record.getMessage()
        if message and (event is None or message != event):
            payload["message"] = message
        payload.update(sanitized)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return " ".join(f"{key}={_quote(value)}" for key, value in payload.items())


def configure_logging(level_name: str) -> None:
    """Configure application-wide logging."""

    handler = logging.StreamHandler()
    handler.setFormatter(KeyValueFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level_name.upper(), logging.INFO))
    root.addHandler(handler)


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Emit a structured log event."""

    logger.log(level, event, extra={"event": event, "fields": fields})


@contextmanager
def log_context(**fields: Any):
    """Temporarily attach structured fields to all logs in the current context."""

    current = dict(_LOG_CONTEXT.get({}))
    current.update(fields)
    token = _LOG_CONTEXT.set(current)
    try:
        yield
    finally:
        _LOG_CONTEXT.reset(token)
