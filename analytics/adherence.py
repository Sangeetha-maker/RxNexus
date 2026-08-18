"""Synthetic Patient Adherence Risk Analytics Engine for PayerRx Optimizer.

Processes synthetic patient clinical timelines (Synthea Dataset 3):
  - Expected refill intervals vs observed gap days
  - Proportion of Days Covered (PDC) & Medication Possession Ratio (MPR) style proxy
  - Patient adherence risk stratification (Low / Medium / High)
  - Medication-level adherence gap aggregations

Strict Labeling Guardrail:
  All outputs are explicitly badged with:
  "Synthetic patient data - not real CMS beneficiary data."
"""
from typing import Dict, Any, List
import pandas as pd
from pathlib import Path
import duckdb

ROOT_DIR = Path(__file__).resolve().parent.parent
CURATED_DIR = ROOT_DIR / "data" / "curated"


def get_adherence_analytics() -> Dict[str, Any]:
    con = duckdb.connect()
    pat_file = CURATED_DIR / "synthetic_patients.parquet"
    med_file = CURATED_DIR / "synthetic_medication_history.parquet"

    if not pat_file.exists() or not med_file.exists():
        return {
            "notice": "Synthetic patient data - not real beneficiary data.",
            "status": "DATA_NOT_READY",
            "synthetic_patients_count": 0
        }

    # Total synthetic patients
    total_patients = con.execute(f"SELECT COUNT(DISTINCT patient_id) FROM read_parquet('{pat_file.as_posix()}')").fetchone()[0]

    # Medication refill timelines & gap analysis
    df_meds = con.execute(f"""
        SELECT 
            patient_id,
            medication_name,
            rxnorm_code,
            TRY_CAST(start_date AS DATE) AS start_dt,
            TRY_CAST(stop_date AS DATE) AS stop_dt,
            dispenses,
            total_cost
        FROM read_parquet('{med_file.as_posix()}')
        ORDER BY patient_id, medication_name, start_dt
    """).df()

    # Calculate gaps
    df_meds["prev_stop"] = df_meds.groupby(["patient_id", "medication_name"])["stop_dt"].shift(1)
    df_meds["gap_days"] = (df_meds["start_dt"] - df_meds["prev_stop"]).dt.days.fillna(0).clip(lower=0)

    # Patient-level risk scoring
    patient_risk = df_meds.groupby("patient_id").agg(
        medication_count=("medication_name", "nunique"),
        total_dispenses=("dispenses", "sum"),
        avg_gap_days=("gap_days", "mean"),
        max_gap_days=("gap_days", "max"),
        repeated_gap_count=("gap_days", lambda x: (x > 15).sum())
    ).reset_index()

    patient_risk["adherence_risk_score"] = (
        (patient_risk["avg_gap_days"] * 2.0 + patient_risk["repeated_gap_count"] * 15.0).clip(0, 100)
    ).round(1)

    patient_risk["risk_tier"] = pd.cut(
        patient_risk["adherence_risk_score"],
        bins=[-1, 30, 65, 100],
        labels=["Low Risk", "Medium Risk", "High Risk"]
    ).astype(str)

    # Top risk medications
    med_risk = df_meds.groupby("medication_name").agg(
        patient_count=("patient_id", "nunique"),
        avg_gap=("gap_days", "mean"),
        high_gap_patients=("gap_days", lambda x: (x > 15).sum())
    ).reset_index()
    med_risk["avg_gap"] = med_risk["avg_gap"].round(1)
    med_risk = med_risk.sort_values(by="avg_gap", ascending=False).head(10)

    # Sample synthetic patient timeline cases for UI demonstration
    sample_patients = patient_risk.sort_values(by="adherence_risk_score", ascending=False).head(15).to_dict(orient="records")

    return {
        "synthetic_notice": "Synthetic patient data - not real CMS beneficiary data.",
        "synthetic_patients_analyzed": total_patients,
        "total_medication_records": len(df_meds),
        "low_risk_count": int((patient_risk["risk_tier"] == "Low Risk").sum()),
        "medium_risk_count": int((patient_risk["risk_tier"] == "Medium Risk").sum()),
        "high_risk_count": int((patient_risk["risk_tier"] == "High Risk").sum()),
        "average_synthetic_gap_days": round(float(patient_risk["avg_gap_days"].mean()), 1),
        "top_adherence_risk_medications": med_risk.to_dict(orient="records"),
        "sample_patient_cohort": sample_patients
    }
