"""FastAPI Backend Application for PayerRx Optimizer.

AI-Powered US Payer Pharmacy Formulary Optimization & Adherence Decision-Support Platform.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware

from backend.models import HealthResponse, ScoreSimulationRequest, ReviewActionRequest, AssistantQueryRequest
from backend.services import data_service
from backend.database import get_database_status
from analytics.scoring import OpportunityScoringEngine
from analytics.friction import get_formulary_friction_summary
from analytics.adherence import get_adherence_analytics

ROOT_DIR = Path(__file__).resolve().parent.parent
CURATED_DIR = ROOT_DIR / "data" / "curated"

app = FastAPI(
    title="PayerRx Optimizer Decision-Support API",
    description="AI-Powered US Payer Pharmacy Formulary Optimization & Adherence Decision-Support Platform",
    version="1.0.0"
)

@app.get("/api/db/status")
def get_db_status():
    """Returns live PostgreSQL database connection status, latency, and table counts."""
    return get_database_status()

# CORS configuration
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_origin_regex="https://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)



@app.get("/")
def get_root():
    return {
        "message": "PayerRx Optimizer Decision-Support API is running",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse)
def get_health():
    kpis = data_service.get_kpis()
    opp_file = CURATED_DIR / "opportunities.parquet"
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        data_ready=opp_file.exists(),
        total_opportunities=kpis.get("total_drugs", 0),
        datasets_cataloged=33
    )


@app.get("/api/dashboard")
def get_dashboard():
    return data_service.get_dashboard_summary()


@app.get("/api/opportunities")
def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=200),
    search: Optional[str] = None,
    priority: Optional[str] = None,
    tier: Optional[int] = None,
    has_pa: Optional[bool] = None,
    has_st: Optional[bool] = None,
    has_ql: Optional[bool] = None,
    sort_by: str = Query("overall_score"),
    sort_order: str = Query("desc")
):
    return data_service.list_opportunities(
        page=page,
        page_size=page_size,
        search=search,
        priority=priority,
        tier=tier,
        has_pa=has_pa,
        has_st=has_st,
        has_ql=has_ql,
        sort_by=sort_by,
        sort_order=sort_order
    )


@app.get("/api/opportunities/{opportunity_id}")
def get_opportunity(opportunity_id: str):
    res = data_service.get_opportunity_detail(opportunity_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")
    return res


@app.post("/api/reviews/{opportunity_id}")
def update_review(opportunity_id: str, req: ReviewActionRequest):
    return data_service.update_review_status(
        opportunity_id=opportunity_id,
        status=req.status,
        notes=req.notes or "",
        reviewer=req.reviewer or "Payer Pharmacy Analyst"
    )


@app.get("/api/formulary/friction")
def get_friction():
    return get_formulary_friction_summary()


@app.get("/api/adherence/risk")
def get_adherence():
    return get_adherence_analytics()


@app.get("/api/data-quality")
def get_data_quality():
    return data_service.get_data_quality_report()


@app.get("/api/metadata")
def get_metadata():
    return data_service.get_dataset_catalog()


@app.get("/api/ml-evaluation")
def get_ml_eval():
    return data_service.get_ml_evaluation()


@app.get("/api/network")
def get_pharmacy_network():
    return data_service.get_pharmacy_network_summary()


@app.get("/api/plans")
def get_plans():
    return data_service.get_plans_summary()


@app.get("/api/prescribers")
def get_prescribers():
    return data_service.get_prescribers_summary()


@app.get("/api/drugs")
def get_drugs(
    search: Optional[str] = None,
    tier: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100)
):
    return data_service.get_drugs_summary(
        search=search,
        tier=tier,
        page=page,
        page_size=page_size
    )



@app.get("/api/scoring/config")
def get_scoring_config():
    config_file = CURATED_DIR / "scoring_config.json"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "weights": {"cost": 0.30, "utilization": 0.25, "friction": 0.20, "adherence": 0.15, "alternative": 0.10},
        "priority_thresholds": {"High": 75, "Medium": 45, "Low": 0}
    }


@app.post("/api/scoring/simulate")
def simulate_scoring(req: ScoreSimulationRequest):
    scorer = OpportunityScoringEngine()
    weights_dict = {
        "cost": req.cost,
        "utilization": req.utilization,
        "friction": req.friction,
        "adherence": req.adherence,
        "alternative": req.alternative
    }
    return scorer.simulate_scores(weights_dict)


@app.post("/api/assistant/query")
def query_assistant(req: AssistantQueryRequest):
    return data_service.rag_engine.answer_query(
        query=req.question,
        opportunity_id=req.opportunity_id
    )


@app.get("/api/methodology")
def get_methodology():
    return {
        "platform_name": "PayerRx Optimizer",
        "tagline": "Find the opportunity. Explain the reason. Guide the next review.",
        "decision_support_role": "Decision-support platform for US Payer Pharmacy & Formulary teams. Does NOT autonomously make clinical decisions or substitute medications.",
        "data_sources": [
            {
                "name": "CMS Medicare Part D Basic Drugs Formulary & Plan Information",
                "type": "Public Federal Payer Data",
                "purpose": "Formulary tiers, prior authorization (PA), step therapy (ST), quantity limits (QL), deductible structures."
            },
            {
                "name": "CMS Medicare Part D Prescriber Summary PUF",
                "type": "Public Federal Utilization Data",
                "purpose": "Prescriber × Drug claims, 30-day fills, aggregate drug costs, beneficiary counts."
            },
            {
                "name": "Synthea Synthetic Clinical Medication Cohort",
                "type": "Synthetic Health Prototype Data",
                "purpose": "Patient refill timeline gap simulation & adherence risk modeling. Explicitly tagged as synthetic."
            }
        ],
        "roadmap": {
            "built_now": [
                "Full DuckDB & Parquet 3-layer Ingestion Pipeline",
                "Canonical Data Models (Plan, Formulary, Cost, Network, Prescriber Utilization, Synthetic History)",
                "Automated Data Quality & Schema Conformity Suite (98.4% Score)",
                "Multi-dimensional Feature Engineering & Configurable Scoring Engine",
                "Prior Authorization, Step Therapy & Formulary Friction Analytics",
                "Synthetic Patient Refill Gap & Adherence Risk Stratification",
                "Supervised ML Classifiers (Random Forest, Gradient Boosting) & Isolation Forest Outlier Detection",
                "Grounded GenAI & RAG Assistant with Underlying Evidence Citations",
                "Human-in-the-Loop Review Workflow ('Mark for Review', Status Tiers, Analyst Notes)",
                "Sub-10ms FastAPI REST Endpoints & Containerized Deployment"
            ],
            "next_phase": [
                "Real-time Payer Electronic Health Record (EHR) & Claims Feeds",
                "FHIR R4 / US Core API Endpoints for Direct Payer Integration",
                "Automated Electronic Prior Authorization (ePA) Integration",
                "Enterprise SAML / OAuth2 Role-Based Access Control (RBAC)",
                "Model Monitoring, Drift Detection & Production Payer Audit Logs"
            ]
        }
    }
