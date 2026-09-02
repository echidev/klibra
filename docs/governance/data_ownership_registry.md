# FINDEX — Data Ownership Registry

**Document Type:** Data Ownership Registry  
**Product:** FINDEX — Financial Data & Intelligence Exchange  
**Product Class:** Enterprise Financial Intelligence Data Platform  
**Document Status:** Draft — Subject to Team Assignment  
**Version:** 1.0  
**Date:** 2026-09-02  
**Owner:** FINDEX Data Governance Team  
**Classification:** Internal  

---

## 1. Purpose

This Data Ownership Registry is the authoritative record of all ownership assignments across the FINDEX platform. It specifies the Business Owner, Data Owner, and Technical Owner for every data product and critical dataset.

This registry ensures that every dataset has a named, accountable owner — and that ownership is never implicit or ambiguous.

---

## 2. Ownership Model

Every production dataset must have three distinct owners:

| Role | Responsibility | Accountable For |
|---|---|---|
| **Business Owner** | Definition and acceptance | Business relevance and consumer satisfaction |
| **Data Owner** | Quality and governance | Definitions, quality metrics, lineage, and governance compliance |
| **Technical Owner** | Pipeline and reliability | Pipeline correctness, reliability, incident response, and infrastructure |

---

## 3. Ownership Registry

### 3.1 Gold Data Products

#### `gold_credit_growth` — Credit Growth Intelligence

| Role | Name/Team | Responsibility |
|---|---|---|
| **Business Owner** | Credit Team Lead | Credit growth definitions, lending intelligence scope, consumer acceptance |
| **Data Owner** | Data Governance Representative | Quality thresholds, lineage, definitions, glossary alignment |
| **Technical Owner** | Data Engineering Lead (Credit) | Pipeline development, reliability, incident response |
| **Target Release** | Release 1 | |

#### `gold_financial_sector_monitor` — Financial Sector Monitor

| Role | Name/Team | Responsibility |
|---|---|---|
| **Business Owner** | Finance Team Lead | Financial sector indicator definitions and scope |
| **Data Owner** | Data Governance Representative | Quality thresholds, lineage, definitions, glossary alignment |
| **Technical Owner** | Data Engineering Lead (Financial Sector) | Pipeline development, reliability, incident response |
| **Target Release** | Release 1 | |

#### `gold_macro_financial_context` — Macro-Financial Context

| Role | Name/Team | Responsibility |
|---|---|---|
| **Business Owner** | Strategy Team Lead | Macro-financial context definitions and scope |
| **Data Owner** | Data Governance Representative | Quality thresholds, lineage, definitions, glossary alignment |
| **Technical Owner** | Data Engineering Lead (Macro) | Pipeline development, reliability, incident response |
| **Target Release** | Release 1 | |

#### `gold_regional_financial_profile` — Regional Financial Profile

| Role | Name/Team | Responsibility |
|---|---|---|
| **Business Owner** | Regional Analysis Team Lead | Regional financial indicator definitions and scope |
| **Data Owner** | Data Governance Representative | Quality thresholds, lineage, definitions, glossary alignment |
| **Technical Owner** | Data Engineering Lead (Regional) | Pipeline development, reliability, incident response |
| **Target Release** | Release 2 | |

### 3.2 Silver Datasets

| Dataset ID | Business Owner | Data Owner | Technical Owner | Source |
|---|---|---|---|---|
| `ojk_banking_stats` | Credit Team Lead | Data Governance Representative | Data Engineering Lead (Credit) | OJK |
| `ojk_islamic_banking` | Finance Team Lead | Data Governance Representative | Data Engineering Lead (Financial Sector) | OJK |
| `ojk_capital_markets` | Strategy Team Lead | Data Governance Representative | Data Engineering Lead (Macro) | OJK |
| `bi_monetary_stats` | Strategy Team Lead | Data Governance Representative | Data Engineering Lead (Macro) | Bank Indonesia |
| `bi_exchange_rates` | Risk Management Lead | Data Governance Representative | Data Engineering Lead (Macro) | Bank Indonesia |
| `bi_interest_rates` | Credit Team Lead | Data Governance Representative | Data Engineering Lead (Macro) | Bank Indonesia |
| `bi_inflation` | Strategy Team Lead | Data Governance Representative | Data Engineering Lead (Macro) | Bank Indonesia |
| `bi_fx_reserves` | Finance Team Lead | Data Governance Representative | Data Engineering Lead (Macro) | Bank Indonesia |
| `bps_gdp` | Strategy Team Lead | Data Governance Representative | Data Engineering Lead (Macro) | BPS |
| `bps_trade_balance` | Strategy Team Lead | Data Governance Representative | Data Engineering Lead (Macro) | BPS |
| `bps_prices` | Strategy Team Lead | Data Governance Representative | Data Engineering Lead (Macro) | BPS |
| `bps_labor` | Strategy Team Lead | Data Governance Representative | Data Engineering Lead (Macro) | BPS |
| `bps_poverty` | Regional Analysis Team Lead | Data Governance Representative | Data Engineering Lead (Regional) | BPS |
| `bps_demographics` | Regional Analysis Team Lead | Data Governance Representative | Data Engineering Lead (Regional) | BPS |

### 3.3 Bronze and Raw Layers

Bronze and Raw layers inherit ownership from their corresponding Silver and source datasets respectively. No separate ownership assignment is required — ownership flows upward from the dataset.

### 3.4 Platform-Level Assets

| Asset | Business Owner | Data Owner | Technical Owner |
|---|---|---|---|
| Source Catalog | Data Governance Lead | Data Governance Lead | Data Engineering Lead |
| Data Dictionary | Data Governance Lead | Data Governance Lead | Data Engineering Lead |
| Data Contracts | Data Governance Lead | Data Governance Lead | Data Engineering Lead |
| Metadata System | Data Governance Lead | Data Governance Lead | Data Engineering Lead |
| Quality Framework | Data Governance Lead | Data Governance Lead | Data Engineering Lead |
| Lineage System | Data Governance Lead | Data Governance Lead | Data Engineering Lead |

---

## 4. Ownership Contact Information

> Note: Specific individual names, emails, and contact details are maintained in the internal team directory and are not published in this registry. Contact mappings are managed by the Platform Admin.

---

## 5. Ownership Assignment Rules

1. Every production dataset must have all three roles assigned before reaching production readiness.
2. Business Owner, Data Owner, and Technical Owner must be different individuals or distinct team roles.
3. Ownership assignments are recorded in this registry and in each dataset's Data Contract.
4. Changes to ownership are documented with date, reason, and approval.
5. Ownership is reviewed quarterly during the governance review cycle.
6. When a team member leaves, ownership is reassigned within 5 business days.

---

## 6. Ownership Change Log

| Date | Dataset/Asset | Role | Previous Owner | New Owner | Reason | Approved By |
|---|---|---|---|---|---|---|
| — | — | — | — | — | Initial assignment — all owners to be confirmed upon team formation | — |

---

## 7. Escalation Path

When ownership conflicts or gaps arise:

```text
Dataset Owner Dispute
  ↓
Data Governance Review
  ↓
Unresolved → Data Governance Lead escalation
  ↓
Unresolved → Executive Management escalation
```

---

## 8. Document Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-02 | FINDEX Data Governance Team | Initial draft — ownership assignments for all Gold products, Silver datasets, and platform-level assets |

---

## 9. Document Status

This Data Ownership Registry is a draft artifact. Specific individual assignments are subject to team formation. The role assignments and dataset-to-owner mappings are the authoritative structure pending individual confirmation.

This document is a companion to:
- **Data Governance Policy** (`docs/governance/data_governance_policy.md`)
- **Data Contracts** (`docs/data/contracts/data_contracts.md`)
- **PRD** — ownership referenced in stakeholder and data product sections
- **TDD** — ownership referenced in engineering operating model

---

*This document is classified as Internal. Distribution is restricted to authorized FINDEX team members and stakeholders.*