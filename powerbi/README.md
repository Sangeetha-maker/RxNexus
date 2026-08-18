# Power BI import guide

Import the curated CSV files from `data/`. Keep `02_prescriber_drug.csv`, `03_formulary_drug.csv`, `07_patient_medication_history.csv`, and `dataset2_annual_benchmark.csv` at their natural grains. Do not relate Synthea data to CMS data without an approved crosswalk. Recommended pages: Executive Overview, Opportunity Explorer, Formulary Context, Synthetic Adherence, and Data Quality.

`08_opportunity_features.csv` is the primary dashboard fact table. Its score is a prototype ranking for pharmacist/payer review, not a clinical recommendation.
