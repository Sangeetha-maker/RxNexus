import csv
from processing.mapping.validate_drug_crosswalk import validate

HEADERS = ["source_system","source_drug_identifier","source_drug_name","source_generic_name","target_rxcui","target_ndc","match_method","authoritative_source","confidence","review_status","reviewed_by","reviewed_at","notes"]
def test_approved_mapping_requires_governance_fields(tmp_path):
    path=tmp_path/"crosswalk.csv"
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=HEADERS); w.writeheader(); w.writerow({"source_system":"CMS_Dataset_2","source_drug_name":"Example","target_rxcui":"1","match_method":"exact_rxcui","authoritative_source":"RxNorm","confidence":"1","review_status":"approved","reviewed_by":"reviewer","reviewed_at":"2026-08-13T00:00:00Z"})
    result=validate(path)
    assert result[0]["valid_for_scoring"] is True
def test_unreviewed_mapping_is_not_score_eligible(tmp_path):
    path=tmp_path/"crosswalk.csv"
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=HEADERS); w.writeheader(); w.writerow({"source_system":"CMS_Dataset_2","source_drug_name":"Example","target_rxcui":"1","match_method":"exact_rxcui","authoritative_source":"RxNorm","confidence":"1","review_status":"pending"})
    result=validate(path)
    assert result[0]["validation_status"] == "PASS"
    assert result[0]["valid_for_scoring"] is False
