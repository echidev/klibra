"""Structured JSON logger — AGENTS.md §3 (Logging Standards).

Every log line is a single JSON object with the required field set:

    ts (ISO 8601 UTC ms)
    level (DEBUG | INFO | WARN | ERROR | FATAL)
    service
    trace_id
    run_id
    source_id (when applicable)
    dataset_id (when applicable)
    message
    duration_ms (when applicable)

No multi-line logs. Use ``details`` for structured payloads. Sensitive
data MUST NOT appear in any field (AGENTS.md §3.3).
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any

__all__ = [
    "JsonFormatter",
    "StructuredLogger",
    "configure_root_logging",
    "log_event",
]

_DEFAULT_FIELDS: tuple[str, ...] = (
    "ts",
    "level",
    "service",
    "trace_id",
    "run_id",
)


class JsonFormatter(logging.Formatter):
    """Emit log records as a single line of JSON."""

    def __init__(self, *, service: str = "klibra") -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": dt.datetime.fromtimestamp(record.created, tz=dt.UTC).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "service": self.service,
            "trace_id": getattr(record, "trace_id", "-"),
            "run_id": getattr(record, "run_id", "-"),
            "message": record.getMessage(),
        }
        source_id = getattr(record, "source_id", None)
        if source_id:
            payload["source_id"] = source_id
        dataset_id = getattr(record, "dataset_id", None)
        if dataset_id:
            payload["dataset_id"] = dataset_id
        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        details = getattr(record, "details", None)
        if details:
            payload["details"] = details
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False) + "\n"


class _Context:
    __slots__ = ("trace_id", "run_id")

    def __init__(self) -> None:
        self.trace_id: str = "-"
        self.run_id: str = "-"


_local = threading.local()


def _get_context() -> _Context:
    ctx = getattr(_local, "ctx", None)
    if ctx is None:
        ctx = _Context()
        _local.ctx = ctx
    return ctx


def log_event(
    level: int,
    message: str,
    *,
    service: str = "klibra",
    details: dict[str, Any] | None = None,
    duration_ms: int | None = None,
    source_id: str | None = None,
    dataset_id: str | None = None,
) -> None:
    """Emit a structured log record through the standard logging module."""

    logger = logging.getLogger(service)
    ctx = _get_context()
    extra: dict[str, Any] = {
        "trace_id": ctx.trace_id,
        "run_id": ctx.run_id,
    }
    if details is not None:
        extra["details"] = details
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms
    if source_id is not None:
        extra["source_id"] = source_id
    if dataset_id is not None:
        extra["dataset_id"] = dataset_id
    logger.log(level, message, extra=extra)


def new_trace_id() -> str:
    return uuid.uuid4().hex


def set_context(trace_id: str | None = None, run_id: str | None = None) -> None:
    ctx = _get_context()
    if trace_id is not None:
        ctx.trace_id = trace_id
    if run_id is not None:
        ctx.run_id = run_id


@contextmanager
def trace_context(trace_id: str | None = None, run_id: str | None = None):
    """Temporarily bind a trace_id/run_id to all log lines in this scope."""
    ctx = _get_context()
    prev_trace, prev_run = ctx.trace_id, ctx.run_id
    set_context(trace_id=trace_id or new_trace_id(), run_id=run_id or prev_run)
    try:
        yield
    finally:
        ctx.trace_id = prev_trace
        ctx.run_id = prev_run


def configure_root_logging(
    *,
    service: str = "klibra",
    level: str = "INFO",
    stream: Any | None = None,
) -> None:
    """Replace the root handler with a single JSON handler.

    Idempotent: replaces existing handlers to avoid double-logging.
    """

    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonFormatter(service=service))
    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level.upper() if isinstance(level, str) else level)


class StructuredLogger:
    """Thin convenience wrapper that respects thread-local context."""

    def __init__(self, name: str = "klibra") -> None:
        self._logger = logging.getLogger(name)

    def debug(self, message: str, **fields: Any) -> None:
        self._log(logging.DEBUG, message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self._log(logging.INFO, message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._log(logging.WARNING, message, **fields)

    def warn(self, message: str, **fields: Any) -> None:
        self._log(logging.WARNING, message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._log(logging.ERROR, message, **fields)

    def exception(self, message: str, **fields: Any) -> None:
        self._log(logging.ERROR, message, exc_info=True, **fields)

    def fatal(self, message: str, **fields: Any) -> None:
        self._log(logging.FATAL, message, **fields)

    def _log(
        self,
        level: int,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        source_id: str | None = None,
        dataset_id: str | None = None,
        exc_info: bool = False,
    ) -> None:
        ctx = _get_context()
        extra: dict[str, Any] = {
            "trace_id": ctx.trace_id,
            "run_id": ctx.run_id,
        }
        if details is not None:
            extra["details"] = details
        if duration_ms is not None:
            extra["duration_ms"] = duration_ms
        if source_id is not None:
            extra["source_id"] = source_id
        if dataset_id is not None:
            extra["dataset_id"] = dataset_id
        self._logger.log(level, message, extra=extra, exc_info=exc_info)


@contextmanager
def timed(logger: StructuredLogger, message: str, **fields: Any):
    """Emit a `duration_ms`-bearing log line at end of block."""

    start = time.monotonic()
    try:
        yield
    finally:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(message, duration_ms=elapsed_ms, **fields)
