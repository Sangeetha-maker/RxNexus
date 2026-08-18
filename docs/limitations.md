# Limitations and implementation path

The prototype does not infer CMS-to-Synthea patient, provider, payer, plan, or drug relationships. Implementing cross-dataset scoring is feasible only after an authoritative drug crosswalk (RxCUI/NDC) and approved business mapping are supplied. PDC/MPR is feasible only with dispensing/refill dates and days-supply data. A production deployment is feasible, but requires approved data access, security controls, HIPAA/compliance review, governance, and validated business rules.
