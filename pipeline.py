"""Master End-to-End Ingestion, Validation, Scoring & ML Pipeline for PayerRx Optimizer.

Executes the 20-phase reproducible workflow:
  1. Automated Dataset Inspection & Cataloging
  2. Canonical Data Modeling (Raw -> Staging -> Curated Parquet)
  3. Data Linkage & Key Crosswalk Validation
  4. Automated Data Quality Suite & Audit Report
  5. Multi-dimensional Feature Engineering & Opportunity Scoring
  6. Machine Learning Prioritization & Outlier Detection
"""
import time
import json
from pathlib import Path

from processing.inspect_inventory import inspect_dataset_inventory
from processing.canonical_model import CanonicalDataPipeline
from processing.data_linkage import evaluate_data_linkage
from processing.data_quality import run_data_quality_checks
from analytics.scoring import OpportunityScoringEngine
from models.ml_prioritization import train_and_evaluate_ml_prioritization


def run_pipeline():
    start_time = time.time()
    print("================================================================")
    print("  PAYERRX OPTIMIZER — AI-POWERED US PAYER PHARMACY PIPELINE   ")
    print("================================================================")

    # Step 1: Inventory & Inspection
    print("\n[PHASE 1-2] Automated Dataset Inspection & Catalog Generation...")
    inspect_dataset_inventory()

    # Step 2: Canonical Model
    print("\n[PHASE 3-5] Canonical Data Modeling & Normalization...")
    canonical = CanonicalDataPipeline()
    canonical.run_all()

    # Step 3: Linkage & Lineage
    print("\n[PHASE 6-7] Data Linkage & Crosswalk Evaluation...")
    evaluate_data_linkage()

    # Step 4: Opportunity Scoring
    print("\n[PHASE 8-10] Feature Engineering & Opportunity Scoring Engine...")
    scorer = OpportunityScoringEngine()
    scorer.generate_opportunities()

    # Step 5: Data Quality Suite
    print("\n[PHASE 11] Data Quality Engine & Metric Audit...")
    run_data_quality_checks()

    # Step 6: Machine Learning Models
    print("\n[PHASE 12] Machine Learning Prioritization & Anomaly Detection...")
    train_and_evaluate_ml_prioritization()

    elapsed = round(time.time() - start_time, 2)
    print("================================================================")
    print(f"  PIPELINE EXECUTION COMPLETED SUCCESSFULLY IN {elapsed}s       ")
    print("================================================================")


if __name__ == "__main__":
    run_pipeline()
