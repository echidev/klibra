"""Unit tests for orchestration/util/storage.py (T009, FR-001/002)."""

from __future__ import annotations

import pytest

from ingestion.storage.raw import CloudStorageWriter, LocalStorageWriter
from orchestration.util.storage import is_development, make_storage_writer


def test_is_development_true_case_insensitive(monkeypatch) -> None:
    monkeypatch.setenv("KLIBRA_ENV", "Development")
    assert is_development() is True


def test_is_development_false_when_not_development(monkeypatch) -> None:
    monkeypatch.setenv("KLIBRA_ENV", "production")
    assert is_development() is False


def test_make_storage_writer_development_returns_local(monkeypatch) -> None:
    monkeypatch.setenv("KLIBRA_ENV", "development")
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
    monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")
    monkeypatch.setenv("AWS_S3_BUCKET_RAW", "klibra-data-raw")
    w = make_storage_writer()
    assert isinstance(w, LocalStorageWriter)
    assert w.bucket_name == "klibra-data-raw"


def test_make_storage_writer_production_returns_cloud(monkeypatch) -> None:
    monkeypatch.setenv("KLIBRA_ENV", "production")
    monkeypatch.setenv("AWS_REGION", "ap-southeast-1")
    monkeypatch.setenv("AWS_S3_BUCKET_RAW", "klibra-data-raw")
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    w = make_storage_writer()
    assert isinstance(w, CloudStorageWriter)


def test_make_storage_writer_development_requires_creds(monkeypatch) -> None:
    monkeypatch.setenv("KLIBRA_ENV", "development")
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="MINIO_ACCESS_KEY"):
        _ = make_storage_writer()
