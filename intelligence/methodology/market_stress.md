# intelligence_economic_momentum

**Product ID:** `intelligence_economic_momentum`
**Methodology version:** `1.0.0`
**Owner:** data-platform@klibra.local
**Score range:** 0-100 (higher = stronger expansion)
**Coverage threshold:** ≥ 0.66

## Inputs

| metric_id | Direction | Rationale |
|---|---|---|
| `gdp_growth_rate` | higher → higher score | Direct growth signal |
| `unemployment_rate` | lower → higher score | Inverted; tight labor = strength |
| `industrial_activity` | higher → higher score | Coincident indicator proxy |

## Normalization

- GDP growth: linear map from -10% to +10% → 0 to 100.
- Unemployment: linear map from 0% to 30% → 100 to 0 (inverted).
- Industrial activity: pass-through 0-100.

## Aggregation

Weighted mean using `weights = {gdp_growth_rate: 0.5, unemployment_rate: 0.3, industrial_activity: 0.2}`.

## Coverage

At least 2 of 3 inputs required (coverage ≥ 0.66). Below threshold, the
score is published but the coverage ratio is exposed in lineage; consumers
are expected to handle low-coverage scores.

## Determinism

Score depends only on (inputs, methodology_version). The same inputs +
methodology_version produces the same score and the same component
breakdown. See `intelligence/composite.py` and `tests/intelligence/`.

## Methodology change control

Per FR-8 002-D, weights are pinned to `methodology_version`. Any change to
the weights dict (via `intelligence.util.version_pin.pin_weights` /
`check_weights_pinned`) requires a MAJOR methodology version bump
(see `MethodologyVersionBumpRequired`).
