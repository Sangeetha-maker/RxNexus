"""Tests for normalization and ratio helpers."""
import pytest
from processing.inspect_inventory import identify_identifiers


def test_identify_identifiers():
    cols = ["CONTRACT_ID", "PLAN_ID", "RXCUI", "NDC", "PRSCRBR_NPI", "DRUG_NAME"]
    ids = identify_identifiers(cols)
    assert "CONTRACT_ID" in ids
    assert "PRSCRBR_NPI" in ids
    assert "RXCUI" in ids
    assert "DRUG_NAME" not in ids
