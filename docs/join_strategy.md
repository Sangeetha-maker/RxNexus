# Join strategy

Every physical join needs a `join_report.csv` record with source files, keys, uniqueness, cardinality, match rate, unmatched count, pre/post row counts, multiplier, status, and notes.

- **CMS utilization → CMS formulary:** disabled until an approved authoritative row in `drug_crosswalk` resolves a common RxCUI or NDC.
- **Plan → pharmacy network:** candidate key is Contract ID + Plan ID + Segment ID. Validate source-year compatibility and multiplier before use.
- **Synthea → CMS:** prohibited. A UI screen can show a synthetic illustrative medication story beside CMS population evidence, but cannot state or encode an underlying join.
- **HLSum → CMS detailed utilization:** prohibited as a physical join; use as annual standalone context only.
