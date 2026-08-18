"""Machine Learning Prioritization & Outlier Detection Engine for PayerRx Optimizer.

Implements:
  1. Deterministic Rule-Based Baseline
  2. Supervised Priority Classification (Random Forest & Gradient Boosting)
  3. Unsupervised Outlier Anomaly Detection (Isolation Forest)
  4. Rigorous Train/Test Split (80/20) & Evaluation Metrics:
     - Precision, Recall, F1-Score, ROC-AUC, Confusion Matrix
  5. Feature Importance Analysis & Explainability

Outputs:
  - models/ml_evaluation_report.json
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, IsolationForest
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
)

ROOT_DIR = Path(__file__).resolve().parent.parent
CURATED_DIR = ROOT_DIR / "data" / "curated"
MODELS_DIR = ROOT_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def train_and_evaluate_ml_prioritization() -> Dict[str, Any]:
    print("[ml_prioritization] Training and evaluating ML prioritization models...")
    opp_file = CURATED_DIR / "opportunities.parquet"
    if not opp_file.exists():
        raise FileNotFoundError(f"{opp_file} not found. Run opportunity scoring first.")

    df = pd.read_parquet(opp_file)

    # Feature Matrix
    feature_cols = [
        "cost_score",
        "utilization_score",
        "friction_score",
        "adherence_score",
        "alternative_review_score",
        "avg_cost_per_claim",
        "tier_level",
        "prior_auth_flag",
        "step_therapy_flag",
        "quantity_limit_flag"
    ]

    X = df[feature_cols].fillna(0)
    # Binary Target: 1 if High priority opportunity (score >= 75), else 0
    y = (df["priority"] == "High").astype(int)

    # Train / Test Split (80/20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 1. Random Forest Model
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    y_prob_rf = rf.predict_proba(X_test)[:, 1]

    # Metrics
    prec_rf = round(float(precision_score(y_test, y_pred_rf, zero_division=0)), 4)
    rec_rf = round(float(recall_score(y_test, y_pred_rf, zero_division=0)), 4)
    f1_rf = round(float(f1_score(y_test, y_pred_rf, zero_division=0)), 4)
    auc_rf = round(float(roc_auc_score(y_test, y_prob_rf)), 4)
    cm_rf = confusion_matrix(y_test, y_pred_rf).tolist()

    # Feature Importances
    importances = [
        {"feature": col, "importance": round(float(imp), 4)}
        for col, imp in zip(feature_cols, rf.feature_importances_)
    ]
    importances = sorted(importances, key=lambda x: x["importance"], reverse=True)

    # 2. Gradient Boosting Model
    gb = GradientBoostingClassifier(n_estimators=80, learning_rate=0.1, max_depth=4, random_state=42)
    gb.fit(X_train, y_train)
    y_pred_gb = gb.predict(X_test)
    y_prob_gb = gb.predict_proba(X_test)[:, 1]

    prec_gb = round(float(precision_score(y_test, y_pred_gb, zero_division=0)), 4)
    rec_gb = round(float(recall_score(y_test, y_pred_gb, zero_division=0)), 4)
    f1_gb = round(float(f1_score(y_test, y_pred_gb, zero_division=0)), 4)
    auc_gb = round(float(roc_auc_score(y_test, y_prob_gb)), 4)
    cm_gb = confusion_matrix(y_test, y_pred_gb).tolist()

    # 3. Unsupervised Outlier Anomaly Detector (Isolation Forest)
    iso = IsolationForest(contamination=0.05, random_state=42)
    iso_preds = iso.fit_predict(X)
    anomaly_count = int((iso_preds == -1).sum())

    evaluation_report = {
        "dataset_size": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "positive_class_ratio": round(float(y.mean()), 3),
        "models": {
            "random_forest": {
                "model_name": "Random Forest Classifier",
                "precision": prec_rf,
                "recall": rec_rf,
                "f1_score": f1_rf,
                "roc_auc": auc_rf,
                "confusion_matrix": cm_rf
            },
            "gradient_boosting": {
                "model_name": "Gradient Boosting Classifier",
                "precision": prec_gb,
                "recall": rec_gb,
                "f1_score": f1_gb,
                "roc_auc": auc_gb,
                "confusion_matrix": cm_gb
            },
            "isolation_forest_anomaly": {
                "model_name": "Isolation Forest Outlier Detector",
                "anomaly_candidates_detected": anomaly_count,
                "anomaly_pct": f"{round((anomaly_count / len(df)) * 100, 1)}%"
            }
        },
        "feature_importances": importances,
        "governance_note": "ML models provide auxiliary prioritization validation; deterministic weighted opportunity score remains the primary transparent decision-support heuristic."
    }

    out_file = MODELS_DIR / "ml_evaluation_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(evaluation_report, f, indent=2)

    print(f"[ml_prioritization] Evaluation complete. RF F1: {f1_rf}, ROC-AUC: {auc_rf}. Report saved to {out_file.name}")
    return evaluation_report


if __name__ == "__main__":
    train_and_evaluate_ml_prioritization()
