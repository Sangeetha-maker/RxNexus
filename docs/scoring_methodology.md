# Scoring methodology

The baseline score is a transparent 0–100 prioritization signal, not a clinical or CMS methodology.

| Component | Baseline weight | Availability in current supplied data |
|---|---:|---|
| Cost impact | 60% | Enabled from CMS prescriber × drug fact |
| Utilization | 40% | Enabled from CMS prescriber × drug fact |
| Formulary friction | 0% | Requires approved CMS utilization ↔ RxCUI/NDC mapping |
| Adherence risk | 0% | Requires dated dispensing/refill and days-supply data |
| Generic opportunity | 0% | Requires authoritative reference and reviewed mapping |
| Network friction | 0% | Requires validated plan/drug relationship |

Cost and utilization use exact 90th-percentile thresholds computed from the full CMS prescriber-drug source. Missing or suppressed denominators return null and do not become zero. When additional components become eligible, weights must be revised in `11_scoring_configuration.csv`, versioned, and shown in the UI/API response.
