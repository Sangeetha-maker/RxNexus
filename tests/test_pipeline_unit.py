"""Unit Tests for Parsers, Scoring Engine, and ML Prioritization."""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
import pandas as pd
from analytics.scoring import OpportunityScoringEngine
from analytics.alternatives import find_review_alternatives
from processing.inspect_inventory import detect_delimiter_and_encoding, identify_identifiers


def test_inspect_helpers():
    ids = identify_identifiers(["CONTRACT_ID", "PLAN_ID", "DRUG_NAME", "RXCUI", "STATE"])
    assert "CONTRACT_ID" in ids
    assert "PLAN_ID" in ids
    assert "RXCUI" in ids
    assert "STATE" not in ids


def test_opportunity_scoring_weights():
    scorer = OpportunityScoringEngine(weights={
        "cost": 0.50, "utilization": 0.20, "friction": 0.10, "adherence": 0.10, "alternative": 0.10
    })
    sim = scorer.simulate_scores({"cost": 0.50, "utilization": 0.20, "friction": 0.10, "adherence": 0.10, "alternative": 0.10})
    assert "top_simulated_items" in sim
    assert sim["high_priority_count"] >= 0


def test_alternatives_guardrails():
    alts = find_review_alternatives(
        drug_name="LIPITOR",
        generic_name="ATORVASTATIN CALCIUM",
        tier_level=4,
        avg_cost=450.0
    )
    assert len(alts) > 0
    # Verify decision support language
    for alt in alts:
        assert "review" in alt["decision_support_label"].lower() or "option" in alt["decision_support_label"].lower()
