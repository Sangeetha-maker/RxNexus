# Data limitations

CMS Dataset 2 is a prescriber × drug aggregate fact. Formulary records use RxCUI/NDC identifiers. A drug relationship is usable only when `drug_crosswalk` has an approved, authoritative mapping. Synthea patients, plans, payers, providers, and medication codes have no automatic CMS relationship. PDC/MPR needs dated dispensing/refill events and days supply; do not calculate it from an unsupported medication export.
