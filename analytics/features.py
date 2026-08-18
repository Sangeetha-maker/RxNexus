"""Feature Engineering Engine for PayerRx Optimizer.

Constructs mathematically grounded features across 4 core domains:
  1. Cost Impact Features (Spend, Cost/Claim, Cost/30-day fill, 90th percentile cost threshold)
  2. Utilization Features (Total Claims, 30-day fills, Prescriber Count, Beneficiary Reach)
  3. Formulary Friction Features (PA flag, Step Therapy flag, Quantity Limit flag, High-Tier indicator, Friction Index)
  4. Synthetic Adherence Features (Refill Gaps, Regularity, Missed Intervals, MPR proxy, Adherence Risk Level)
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
CURATED_DIR = ROOT_DIR / "data" / "curated"


def compute_cost_features(df_util: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Calculates normalized cost metrics and percentile thresholds."""
    df = df_util.copy()
    
    # Cost per claim & fill
    df["cost_per_claim"] = (df["total_drug_cost"] / df["total_claims"].replace(0, np.nan)).round(2).fillna(0)
    df["cost_per_30day_fill"] = (df["total_drug_cost"] / df["total_30day_fills"].replace(0, np.nan)).round(2).fillna(0)

    # 90th percentile thresholds
    cost_p90 = float(df["total_drug_cost"].quantile(0.90))
    cost_per_claim_p90 = float(df["cost_per_claim"].quantile(0.90))

    df["is_high_cost_p90"] = (df["total_drug_cost"] >= cost_p90).astype(int)
    
    # Cost score normalized 0 - 100 (log-scale normalized to prevent outlier skew)
    max_cost_log = np.log1p(df["total_drug_cost"].max())
    df["cost_score"] = (np.log1p(df["total_drug_cost"]) / max_cost_log * 100.0).round(1).clip(0, 100)

    thresholds = {
        "cost_p90": cost_p90,
        "cost_per_claim_p90": cost_per_claim_p90
    }
    return df, thresholds


def compute_utilization_features(df_util: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Calculates normalized utilization metrics and percentile thresholds."""
    df = df_util.copy()
    
    claims_p90 = float(df["total_claims"].quantile(0.90))
    prescribers_p90 = float(df["prescriber_count"].quantile(0.90))

    df["is_high_util_p90"] = (df["total_claims"] >= claims_p90).astype(int)

    # Utilization score normalized 0 - 100
    max_claims_log = np.log1p(df["total_claims"].max())
    df["utilization_score"] = (np.log1p(df["total_claims"]) / max_claims_log * 100.0).round(1).clip(0, 100)

    thresholds = {
        "claims_p90": claims_p90,
        "prescribers_p90": prescribers_p90
    }
    return df, thresholds


def compute_formulary_friction_features(df_form: pd.DataFrame) -> pd.DataFrame:
    """Computes drug-level and formulary-level friction index (0 - 100)."""
    # Group formulary drugs by drug identifier / RxCUI / NDC to get aggregate friction profile
    friction_summary = df_form.groupby("rxcui").agg(
        formulary_count=("formulary_id", "nunique"),
        avg_tier=("tier_level", "mean"),
        max_tier=("tier_level", "max"),
        pa_rate=("prior_authorization_flag", "mean"),
        st_rate=("step_therapy_flag", "mean"),
        ql_rate=("quantity_limit_flag", "mean"),
        avg_friction_score=("formulary_friction_score", "mean")
    ).reset_index()

    friction_summary["friction_score"] = friction_summary["avg_friction_score"].round(1)
    return friction_summary


def compute_synthetic_adherence_features(df_meds: pd.DataFrame) -> pd.DataFrame:
    """Analyzes synthetic medication history to compute refill intervals and adherence risk signals."""
    if df_meds.empty:
        return pd.DataFrame()

    df = df_meds.copy()
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["stop_date"] = pd.to_datetime(df["stop_date"], errors="coerce")

    # Sort by patient and medication start date
    df = df.sort_values(by=["patient_id", "medication_name", "start_date"])

    # Duration and gap calculation per medication fill
    df["duration_days"] = (df["stop_date"] - df["start_date"]).dt.days.fillna(30).clip(lower=1)
    
    # Calculate days between subsequent starts for same patient and medication
    df["prev_stop_date"] = df.groupby(["patient_id", "medication_name"])["stop_date"].shift(1)
    df["refill_gap_days"] = (df["start_date"] - df["prev_stop_date"]).dt.days.clip(lower=0).fillna(0)

    # Patient-medication level adherence aggregation
    adherence_by_med = df.groupby("medication_name").agg(
        synthetic_patient_count=("patient_id", "nunique"),
        total_dispenses=("dispenses", "sum"),
        avg_gap_days=("refill_gap_days", "mean"),
        max_gap_days=("refill_gap_days", "max"),
        high_gap_fills=("refill_gap_days", lambda x: (x > 15).sum()),
        total_fills=("patient_id", "count")
    ).reset_index()

    adherence_by_med["missed_refill_pct"] = (
        adherence_by_med["high_gap_fills"] / adherence_by_med["total_fills"].replace(0, 1) * 100.0
    ).round(1)

    # MPR / PDC proxy calculation (Possession ratio ~ 1.0 - missed fraction)
    adherence_by_med["mpr_proxy"] = (1.0 - (adherence_by_med["missed_refill_pct"] / 100.0)).clip(0.1, 1.0).round(2)

    # Adherence risk score: higher missed pct = higher risk score (0 to 100)
    adherence_by_med["adherence_risk_score"] = (adherence_by_med["missed_refill_pct"] * 1.0).clip(0, 100).round(1)
    adherence_by_med["adherence_risk_tier"] = pd.cut(
        adherence_by_med["adherence_risk_score"],
        bins=[-1, 30, 60, 100],
        labels=["Low", "Medium", "High"]
    ).astype(str)

    adherence_by_med["is_synthetic"] = True
    return adherence_by_med
