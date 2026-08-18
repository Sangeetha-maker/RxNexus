"""Formulary Friction Analytics Engine for PayerRx Optimizer.

Provides deep drill-down metrics on:
  - Prior Authorization (PA) distribution
  - Step Therapy (ST) protocols
  - Quantity Limits (QL) thresholds
  - High-tier (Tier 4/5 specialty) barrier impact
  - Plan-level and contract-level friction rankings
"""
from typing import Dict, Any, List
import pandas as pd
from pathlib import Path
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent
CURATED_DIR = ROOT_DIR / "data" / "curated"


def get_formulary_friction_summary() -> Dict[str, Any]:
    con = duckdb.connect()
    form_file = CURATED_DIR / "formulary_drug.parquet"
    plan_file = CURATED_DIR / "plan.parquet"

    if not form_file.exists():
        return {}

    # Aggregate counts
    stats = con.execute(f"""
        SELECT 
            COUNT(*) AS total_records,
            COUNT(DISTINCT formulary_id) AS total_formularies,
            COUNT(DISTINCT rxcui) AS total_drugs,
            SUM(prior_authorization_flag) AS pa_count,
            SUM(step_therapy_flag) AS st_count,
            SUM(quantity_limit_flag) AS ql_count,
            SUM(tier_friction_flag) AS high_tier_count,
            ROUND(AVG(formulary_friction_score), 1) AS avg_friction_score
        FROM read_parquet('{form_file.as_posix()}')
    """).fetchone()

    # Tier level breakdown
    tier_breakdown = con.execute(f"""
        SELECT 
            tier_level,
            COUNT(*) AS drug_count,
            ROUND(AVG(prior_authorization_flag) * 100, 1) AS pa_rate_pct,
            ROUND(AVG(step_therapy_flag) * 100, 1) AS st_rate_pct,
            ROUND(AVG(quantity_limit_flag) * 100, 1) AS ql_rate_pct,
            ROUND(AVG(formulary_friction_score), 1) AS avg_friction
        FROM read_parquet('{form_file.as_posix()}')
        WHERE tier_level IS NOT NULL
        GROUP BY tier_level
        ORDER BY tier_level
    """).df().to_dict(orient="records")

    # Friction distribution buckets
    friction_distribution = con.execute(f"""
        SELECT 
            CASE 
                WHEN formulary_friction_score >= 75 THEN 'Severe Friction (75-100)'
                WHEN formulary_friction_score >= 50 THEN 'Moderate-High (50-74)'
                WHEN formulary_friction_score >= 25 THEN 'Low-Moderate (25-49)'
                ELSE 'Minimal / Open (0-24)'
            END AS bucket,
            COUNT(*) AS count
        FROM read_parquet('{form_file.as_posix()}')
        GROUP BY 1
        ORDER BY count DESC
    """).df().to_dict(orient="records")

    return {
        "total_records": stats[0],
        "total_formularies": stats[1],
        "total_unique_drugs": stats[2],
        "pa_count": stats[3],
        "st_count": stats[4],
        "ql_count": stats[5],
        "high_tier_count": stats[6],
        "avg_friction_score": stats[7],
        "tier_breakdown": tier_breakdown,
        "friction_distribution": friction_distribution
    }
