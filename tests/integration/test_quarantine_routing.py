"""Integration tests for quarantine routing (T026/T027)."""

from __future__ import annotations

from orchestration.tasks import apply_quality_gate


def _bronze_worldbank():
    return {
        "status": "BRONZE_BUILT",
        "batches": [
            {
                "source_id": "worldbank",
                "dataset_id": "NY.GDP.MKTP.KD.ZG",
                "run_id": "r-1",
                "records": [
                    {
                        "observation_id": "r-1:US:GDP:2023",
                        "value": 2.5,
                        "metric_id": "gdp_growth_rate",
                        "observation_date": "2023",
                    },
                    {
                        "observation_id": "r-1:US:NULL:2023",
                        "value": None,
                        "metric_id": "gdp_growth_rate",
                        "observation_date": "2023",
                    },
                ],
            }
        ],
    }


def test_quarantine_returns_shape(monkeypatch) -> None:
    # Disable quarantine writer env so it just emits WARN; we only verify shape.
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.setenv("KLIBRA_ENV", "development")
    out = apply_quality_gate(_bronze_worldbank())
    assert "quarantined" in out
    assert "quarantine_count" in out
    # Either accepted only (records still both since framework ACCEPTED for nonempty) or mixed; tolerate both.
    assert out["status"] == "QUALITY_ACCEPTED"


def test_apply_quality_gate_no_storage_does_not_crash(monkeypatch) -> None:
    monkeypatch.setenv("KLIBRA_ENV", "development")
    monkeypatch.delenv("MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("MINIO_SECRET_KEY", raising=False)
    out = apply_quality_gate(_bronze_worldbank())
    # Should not raise; pipeline continues.
    assert out["status"] == "QUALITY_ACCEPTED"
