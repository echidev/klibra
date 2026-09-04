# Notebook Quickstart — Reproducible Feature Derivation

This document explains how a Data Scientist produces **reproducible
features** from KLIBRA semantic metrics (TDD §77, US4).

## Prerequisites

- Access to a KLIBRA Gold product (e.g. `gold_macro_indicators`).
- A registered semantic metric version (see `docs/data/contracts/semantic/`).
- A version-controlled notebook with `feature_code_version` recorded.

## Workflow

### 1. Pin the inputs

```python
import os, hashlib
from datetime import datetime, timezone

METRIC_VERSION = "1.0.0"        # pinned in feature notebook
SOURCE_SNAPSHOT_ID = "gold_macro_indicators@2024-12-31T23:59:59Z"
CALC_TS = datetime.now(timezone.utc).isoformat()
FEATURE_CODE_VERSION = "v0.1.0"
```

### 2. Use the point-in-time helper

```python
from semantic.point_in_time import filter_as_of
import duckdb

con = duckdb.connect()
rows = con.execute("SELECT * FROM gold_macro_indicators").fetchall()
features = filter_as_of([dict(r) for r in rows], "2023-12-31T00:00:00Z")
```

### 3. Record the feature manifest

```python
import json
manifest = {
    "metric_version": METRIC_VERSION,
    "source_snapshot_id": SOURCE_SNAPSHOT_ID,
    "calculation_timestamp": CALC_TS,
    "feature_code_version": FEATURE_CODE_VERSION,
}
print(json.dumps(manifest, indent=2))
```

### 4. Save the manifest alongside the notebook

The manifest must be committed next to the notebook so the feature
derivation is fully reproducible from inputs (Constitution §II,
TDD §77).

## Reproducibility invariant

> Same `metric_version` + `source_snapshot_id` + `feature_code_version`
> ⇒ identical output. The calculation timestamp is recorded but does not
> affect determinism.

## Re-running a feature derivation

To re-derive a feature, re-execute the notebook pinned to the recorded
manifest. KLIBRA's Gold layer is point-in-time immutable: the snapshot
ID maps to a specific SQL `as_of_timestamp` filter that is fully
reproducible.
