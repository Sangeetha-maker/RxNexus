"""Validate governed drug mappings before they can enable cross-domain scoring."""
from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parents[2]
TEMPLATE = Path(__file__).with_name("drug_crosswalk_template.csv")
REPORT = ROOT / "data" / "drug_crosswalk_validation_report.csv"
REQUIRED = {"source_system", "source_drug_identifier", "source_drug_name", "target_rxcui", "target_ndc", "match_method", "authoritative_source", "confidence", "review_status", "reviewed_by", "reviewed_at"}
ALLOWED_METHODS = {"exact_rxcui", "exact_ndc", "authoritative_reference", "manual_review"}

def validate(path: Path = TEMPLATE) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f)); fields = set(rows[0]) if rows else set()
    missing = REQUIRED - fields
    results=[]
    for n, row in enumerate(rows, 2):
        errors=[]
        if missing: errors.append("missing required columns: " + ", ".join(sorted(missing)))
        if not (row.get("source_drug_identifier") or row.get("source_drug_name")): errors.append("source drug identifier or name required")
        if not (row.get("target_rxcui") or row.get("target_ndc")): errors.append("target RxCUI or NDC required")
        if row.get("match_method") not in ALLOWED_METHODS: errors.append("unsupported match method")
        try:
            confidence=float(row.get("confidence", ""));
            if not 0 <= confidence <= 1: errors.append("confidence must be 0..1")
        except ValueError: errors.append("confidence is required")
        if not row.get("authoritative_source"): errors.append("authoritative source required")
        if row.get("review_status") == "approved" and not (row.get("reviewed_by") and row.get("reviewed_at")): errors.append("approved mapping requires reviewer and timestamp")
        results.append({"row_number":n,"mapping_key":"|".join([row.get("source_system", ""),row.get("source_drug_identifier", ""),row.get("source_drug_name", "")]),"review_status":row.get("review_status"),"valid_for_scoring":not errors and row.get("review_status")=="approved","validation_status":"PASS" if not errors else "FAIL","errors":"; ".join(errors)})
    REPORT.parent.mkdir(exist_ok=True)
    with REPORT.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["row_number","mapping_key","review_status","valid_for_scoring","validation_status","errors"]); writer.writeheader(); writer.writerows(results)
    return results
if __name__ == "__main__":
    results=validate(); print(f"Validated {len(results)} mapping rows; {sum(x['valid_for_scoring'] for x in results)} approved for scoring.")
