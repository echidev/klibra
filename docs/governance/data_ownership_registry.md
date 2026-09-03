# KLIBRA — Data Ownership Registry

**Document Type:** Data Ownership Registry  
**Product:** KLIBRA — Economic Intelligence Platform  
**Product Class:** Enterprise Economic Intelligence & Data Products Platform  
**Document Status:** Active  
**Version:** 2.0  
**Date:** 2026-09-03  
**Owner:** KLIBRA Data Governance Team  
**Classification:** Internal  
**Related:** PRD §4, §12, §30; TDD §13, §60, §71  

---

## 1. Purpose

This registry records ownership assignments for all KLIBRA data assets, ensuring clear accountability for data quality, lineage, and lifecycle management (PRD §30‑§33, TDD §59).

---

## 2. Ownership Model

KLIBRA follows a **Three‑Owner Model** (Data Governance Policy §3):

- **Business Owner** – defines business meaning, acceptance criteria, and KPI alignment.
- **Technical Owner** – responsible for pipeline implementation, quality enforcement, and operational health.
- **Data Owner** – custodial owner of the source; manages source contracts, access, and updates.

---

## 3. Registry Structure

The registry is stored as a **YAML** file (`docs/governance/data_ownership_registry.yaml`) and version‑controlled.

```yaml
datasets:
  gold_macro_indicators:
    business_owner: finance-analytics-team
    technical_owner: data-engineering-team
    data_owner: world-bank
    description: Standardized macro‑economic indicators (GDP, inflation, etc.)
    last_updated: 2026-09-02
  gold_interest_rate_monitor:
    business_owner: risk-management-team
    technical_owner: data-engineering-team
    data_owner: fred
    description: Central bank policy rates and benchmark yields
    last_updated: 2026-09-02
  gold_market_overview:
    business_owner: market-insights-team
    technical_owner: data-engineering-team
    data_owner: coin-gecko
    description: FX, equity, commodity, crypto market observations
    last_updated: 2026-09-02
  gold_country_benchmark:
    business_owner: strategy-team
    technical_owner: data-engineering-team
    data_owner: world-bank
    description: Cross‑country macro benchmarks
    last_updated: 2026-09-02
  gold_source_health:
    business_owner: data-ops-team
    technical_owner: data-engineering-team
    data_owner: platform
    description: Operational health metrics for each source
    last_updated: 2026-09-02
semantic_metrics:
  gdp_growth_rate:
    business_owner: finance-analytics-team
    technical_owner: data-engineering-team
    data_owner: world-bank
    description: Annual GDP growth rate per country
    version: 1.0.0
    last_updated: 2026-09-02
  inflation_rate:
    business_owner: finance-analytics-team
    technical_owner: data-engineering-team
    data_owner: world-bank
    description: Consumer price index inflation rate
    version: 1.0.0
    last_updated: 2026-09-02
# ...additional metrics and intelligence products follow same pattern...
```

---

## 4. Maintenance Process

1. **New Asset Creation** – When a new dataset, metric, or intelligence product is added, the owning team updates the registry via a pull request.
2. **Owner Change** – Any change to ownership triggers a **Major change** in the Change Management Process (ADR‑002).
3. **Periodic Review** – Quarterly review by Data Governance Committee to verify owners remain appropriate.
4. **Audit Trail** – All changes tracked in Git commit history; an audit log exported monthly for compliance.

---

## 5. Ownership Responsibilities

| Owner | Responsibilities |
| --- | --- |
| **Business Owner** | Define business definition, acceptance criteria, usage guidance; sign off on release of Gold products and semantic metrics. |
| **Technical Owner** | Ensure pipelines produce outputs meeting contracts; monitor quality; maintain CI/CD; manage backfills. |
| **Data Owner** | Maintain source contract, monitor source availability, manage credentials, update source catalog. |

---

## 6. Governance Integration

- **Access Review Process** uses this registry to populate the `owner` field in the access matrix.
- **Change Management Process** requires owner sign‑off for any change affecting the asset.
- **Data Quality Governance** monitors quality metrics per owner responsibility.
- **Incident Management** includes owner fields for impact analysis.

---

## 7. Document Version History

| Version | Date | Author | Changes |
| --- | --- | --- | --- |
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft (FINDEX) |
| 2.0 | 2026-09-03 | KLIBRA Data Governance Team | Re‑aligned to KLIBRA PRD v2.0 / TDD v2.0; updated asset list, owners, and structure |

---

*This document is classified as Internal. Distribution is restricted to authorized KLIBRA team members and stakeholders.*
