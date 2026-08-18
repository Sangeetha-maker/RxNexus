"""Unit & Integration Tests for PayerRx Optimizer Backend API."""
import sys
from pathlib import Path

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["data_ready"] is True
    assert data["total_opportunities"] > 0


def test_dashboard_endpoint():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "top_opportunities" in data
    assert "spend_by_tier" in data
    assert len(data["top_opportunities"]) > 0


def test_opportunities_list_and_filters():
    # Test default
    response = client.get("/api/opportunities?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) == 10
    
    first_item = data["items"][0]
    opp_id = first_item["opportunity_id"]

    # Test detail
    detail_resp = client.get(f"/api/opportunities/{opp_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "opportunity" in detail
    assert "score_breakdown" in detail
    assert "alternatives" in detail


def test_human_in_the_loop_review():
    opp_id = "OPP-0001"
    payload = {
        "status": "Under Review",
        "notes": "Flagged for Q3 formulary committee review.",
        "reviewer": "Dr. Smith (Lead Pharmacist)"
    }
    response = client.post(f"/api/reviews/{opp_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "Under Review"

    # Verify detail reflects updated review status
    detail_resp = client.get(f"/api/opportunities/{opp_id}")
    assert detail_resp.json()["opportunity"]["review_status"] == "Under Review"


def test_formulary_friction_endpoint():
    response = client.get("/api/formulary/friction")
    assert response.status_code == 200
    data = response.json()
    assert "pa_count" in data
    assert "st_count" in data
    assert "tier_breakdown" in data


def test_synthetic_adherence_endpoint():
    response = client.get("/api/adherence/risk")
    assert response.status_code == 200
    data = response.json()
    assert "synthetic_notice" in data
    assert "Synthetic patient data" in data["synthetic_notice"]
    assert "synthetic_patients_analyzed" in data


def test_scoring_simulation_endpoint():
    payload = {
        "cost": 0.50,
        "utilization": 0.20,
        "friction": 0.10,
        "adherence": 0.10,
        "alternative": 0.10
    }
    response = client.post("/api/scoring/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "top_simulated_items" in data
    assert len(data["top_simulated_items"]) > 0


def test_genai_assistant_query():
    payload = {"question": "Why is this drug high priority?", "opportunity_id": "OPP-0001"}
    response = client.post("/api/assistant/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "evidence" in data
    assert len(data["citations"]) > 0


def test_data_quality_endpoint():
    response = client.get("/api/data-quality")
    assert response.status_code == 200
    data = response.json()
    assert "data_quality_score" in data
    assert "checks" in data


def test_methodology_endpoint():
    response = client.get("/api/methodology")
    assert response.status_code == 200
    data = response.json()
    assert "data_sources" in data
    assert "roadmap" in data
    assert "built_now" in data["roadmap"]
