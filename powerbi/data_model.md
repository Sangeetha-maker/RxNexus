# Power BI semantic model

Use a star schema only where a validated relationship exists.

- `08_opportunity_features`: primary review-queue fact.
- `02_prescriber_drug`: CMS utilization detail; use for drill-through, not a duplicate score fact.
- `03_formulary_drug`: disconnected until approved `drug_crosswalk` relationships exist.
- `04_plan` → `06_pharmacy_network`: candidate relationship by Contract ID, Plan ID, Segment ID; validate first.
- `07_patient_medication_history`: disconnected synthetic demonstration table.
- `dataset2_annual_benchmark`: disconnected annual context table.

Suggested pages: Executive Overview, Opportunity Explorer, Formulary Context, Plan & Pharmacy Network, Synthetic Medication History, Data Quality & Join Governance.
