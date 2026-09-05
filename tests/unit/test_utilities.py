"""Coverage tests for idempotency, manifest, and logging utilities."""

from __future__ import annotations

import io
import json
import logging
import sys

import pytest

from ingestion.util.idempotency import (
    compute_idempotency_key,
    validate_idempotency_components,
)
from ingestion.util.logging import (
    JsonFormatter,
    StructuredLogger,
    configure_root_logging,
    log_event,
    new_trace_id,
    set_context,
)
from ingestion.util.manifest import build_manifest, manifest_to_json, sha256_hex

# ── idempotency ────────────────────────────────────────────────


def test_compute_idempotency_key_deterministic() -> None:
    k1 = compute_idempotency_key("source", "dataset", "2024", "v1", "abc123")
    k2 = compute_idempotency_key("source", "dataset", "2024", "v1", "abc123")
    assert k1 == k2
    assert len(k1) == 64


def test_compute_idempotency_key_version_none() -> None:
    k1 = compute_idempotency_key("source", "dataset", "2024", None, "abc123")
    k2 = compute_idempotency_key("source", "dataset", "2024", "", "abc123")
    assert k1 == k2


def test_compute_idempotency_key_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        compute_idempotency_key("source", "dataset", "2024", None, 123)  # type: ignore[arg-type]


def test_validate_idempotency_components_all_missing() -> None:
    errors = validate_idempotency_components("", "", "", None, "")
    assert len(errors) >= 4


def test_validate_idempotency_components_invalid_chars() -> None:
    errors = validate_idempotency_components("source", "dataset", "2024", None, "hash@with!special")
    assert any("disallowed characters" in e for e in errors)


# ── manifest ──────────────────────────────────────────────────


def test_sha256_hex_bytes() -> None:
    assert len(sha256_hex(b"abc")) == 64


def test_sha256_hex_string() -> None:
    assert sha256_hex("abc") == sha256_hex(b"abc")


def test_build_manifest_defaults() -> None:
    manifest = build_manifest(
        source_id="worldbank",
        dataset_id="NY.GDP.MKTP.CD",
        run_id="run1",
        source_url="https://example.test",
        content_hash="abc123",
    )
    assert manifest["source_id"] == "worldbank"
    assert manifest["content_hash"] == "abc123"


def test_manifest_to_json() -> None:
    manifest = build_manifest(
        source_id="worldbank",
        dataset_id="NY.GDP.MKTP.CD",
        run_id="run1",
        source_url="https://example.test",
        content_hash="abc",
    )
    json_str = manifest_to_json(manifest)
    assert "worldbank" in json_str


# ── logging ───────────────────────────────────────────────────


def test_json_formatter_basic() -> None:
    formatter = JsonFormatter(service="test")
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "msg", (), None)
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["message"] == "msg"
    assert data["service"] == "test"
    assert data["trace_id"] == "-"


def test_json_formatter_with_extras() -> None:
    formatter = JsonFormatter(service="test")
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "msg", (), None)
    record.source_id = "src"
    record.dataset_id = "ds"
    record.duration_ms = 100
    record.details = {"k": "v"}
    record.exc_info = None
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert data["source_id"] == "src"
    assert data["dataset_id"] == "ds"
    assert data["duration_ms"] == 100
    assert data["details"] == {"k": "v"}


def test_json_formatter_with_exception() -> None:
    formatter = JsonFormatter(service="test")
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord("test", logging.ERROR, __file__, 1, "msg", (), sys.exc_info())
    formatted = formatter.format(record)
    data = json.loads(formatted)
    assert "exception" in data


def test_log_event() -> None:
    stream = io.StringIO()
    configure_root_logging(service="test", stream=stream)
    log_event(logging.INFO, "hello", service="test", details={"k": 1})


def test_new_trace_id() -> None:
    tid = new_trace_id()
    assert len(tid) == 32


def test_set_context() -> None:
    set_context(trace_id="trace123", run_id="run456")
    from ingestion.util.logging import _get_context

    ctx = _get_context()
    assert ctx.trace_id == "trace123"
    assert ctx.run_id == "run456"


def test_configure_root_logging() -> None:
    stream = io.StringIO()
    configure_root_logging(service="test", stream=stream)


def test_structured_logger_methods() -> None:
    stream = io.StringIO()
    configure_root_logging(service="test", stream=stream)
    logger = StructuredLogger("test")
    logger.debug("debug")
    logger.info("info")
    logger.warning("warn")
    logger.warn("warn2")
    logger.error("error")
    logger.exception("exc")
    logger.fatal("fatal")
