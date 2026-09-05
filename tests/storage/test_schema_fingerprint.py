"""Unit tests for T052 — schema fingerprint change classification (002-F)."""

from __future__ import annotations

from ingestion.storage.schema_fingerprint import (
    SchemaFingerprintStore,
    classify_schema_change,
    fingerprint_payload,
)


def test_classify_compatible_when_only_added() -> None:
    old = {"a": "str", "b": "int"}
    new = {"a": "str", "b": "int", "c": "float"}
    assert classify_schema_change(old, new) == "POTENTIALLY_BREAKING"


def test_classify_potentially_breaking_type_change() -> None:
    old = {"a": "str"}
    new = {"a": "int"}
    assert classify_schema_change(old, new) == "POTENTIALLY_BREAKING"


def test_classify_breaking_when_field_removed() -> None:
    old = {"a": "str", "b": "int"}
    new = {"a": "str"}
    assert classify_schema_change(old, new) == "BREAKING"


def test_fingerprint_payload_nested_json() -> None:
    payload = b'{"a": "x", "b": {"c": 1, "d": 2.0}, "e": [1, 2]}'
    fp = fingerprint_payload(payload)
    assert fp["a"] == "str"
    assert fp["b.c"] == "int"
    assert fp["b.d"] == "float"
    assert fp["e"].startswith("array:")


def test_schema_fingerprint_store_first_run_is_compatible() -> None:
    store = SchemaFingerprintStore()
    fp = store.record(
        source_id="worldbank",
        dataset_id="NY.GDP.MKTP.CD",
        run_id="r1",
        payload=b'{"a": 1}',
    )
    assert fp.change_class == "COMPATIBLE"


def test_schema_fingerprint_store_detects_breaking() -> None:
    store = SchemaFingerprintStore()
    store.record(source_id="s", dataset_id="d", run_id="r1", payload=b'{"a": 1, "b": 2}')
    fp2 = store.record(source_id="s", dataset_id="d", run_id="r2", payload=b'{"a": 1}')
    assert fp2.change_class == "BREAKING"
