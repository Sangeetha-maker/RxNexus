"""Canonical Data Model & Normalization Engine for PayerRx Optimizer.

Implements the 3-layer architecture:
  RAW -> STAGING -> CURATED
Extracts, validates, cleans, and standardizes canonical entities:
  - PLAN
  - FORMULARY / FORMULARY_DRUG
  - BENEFICIARY_COST
  - PHARMACY_NETWORK
  - DRUG_UTILIZATION (prescriber & national summary)
  - PATIENT (synthetic)
  - MEDICATION_HISTORY (synthetic)
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import duckdb
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
STAGING_DIR = ROOT_DIR / "data" / "staging"
CURATED_DIR = ROOT_DIR / "data" / "curated"
QUALITY_DIR = ROOT_DIR / "data" / "quality"

for d in [STAGING_DIR, CURATED_DIR, QUALITY_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class CanonicalDataPipeline:
    def __init__(self):
        self.con = duckdb.connect()

    def build_canonical_plans(self) -> pd.DataFrame:
        print("[canonical] Building canonical PLAN entity...")
        plan_file = next((RAW_DIR / "dataset_1_cms_formulary").glob("plan_information*.csv"))
        query = f"""
        SELECT 
            TRIM(CAST(CONTRACT_ID AS VARCHAR)) AS contract_id,
            TRIM(CAST(PLAN_ID AS VARCHAR)) AS plan_id,
            TRIM(CAST(SEGMENT_ID AS VARCHAR)) AS segment_id,
            TRIM(CAST(CONTRACT_NAME AS VARCHAR)) AS contract_name,
            TRIM(CAST(PLAN_NAME AS VARCHAR)) AS plan_name,
            TRIM(CAST(FORMULARY_ID AS VARCHAR)) AS formulary_id,
            TRY_CAST(REPLACE(REPLACE(CAST(PREMIUM AS VARCHAR), '$', ''), ',', '') AS DOUBLE) AS premium,
            TRY_CAST(REPLACE(REPLACE(CAST(DEDUCTIBLE AS VARCHAR), '$', ''), ',', '') AS DOUBLE) AS deductible,
            TRIM(CAST(STATE AS VARCHAR)) AS state,
            TRIM(CAST(SNP AS VARCHAR)) AS snp_type,
            TRIM(CAST(PLAN_SUPPRESSED_YN AS VARCHAR)) AS is_suppressed
        FROM read_csv('{plan_file.as_posix()}', normalize_names=false, ignore_errors=true)
        WHERE CONTRACT_ID IS NOT NULL AND PLAN_ID IS NOT NULL
        """
        df = self.con.execute(query).df()
        out_parquet = CURATED_DIR / "plan.parquet"
        df.to_parquet(out_parquet, index=False)
        print(f"[canonical] Saved {len(df):,} PLAN records to {out_parquet.name}")
        return df

    def build_canonical_formulary(self) -> pd.DataFrame:
        print("[canonical] Building canonical FORMULARY_DRUG entity...")
        form_file = next((RAW_DIR / "dataset_1_cms_formulary").glob("basic_drugs_formulary_file*.csv"))
        query = f"""
        SELECT 
            TRIM(CAST(FORMULARY_ID AS VARCHAR)) AS formulary_id,
            TRIM(CAST(FORMULARY_VERSION AS VARCHAR)) AS formulary_version,
            TRIM(CAST(CONTRACT_YEAR AS VARCHAR)) AS contract_year,
            TRIM(CAST(RXCUI AS VARCHAR)) AS rxcui,
            TRIM(CAST(NDC AS VARCHAR)) AS ndc,
            TRY_CAST(TIER_LEVEL_VALUE AS INTEGER) AS tier_level,
            CASE WHEN UPPER(TRIM(CAST(QUANTITY_LIMIT_YN AS VARCHAR))) IN ('Y', 'YES', '1') THEN 1 ELSE 0 END AS quantity_limit_flag,
            TRY_CAST(QUANTITY_LIMIT_AMOUNT AS DOUBLE) AS quantity_limit_amount,
            TRY_CAST(QUANTITY_LIMIT_DAYS AS INTEGER) AS quantity_limit_days,
            CASE WHEN UPPER(TRIM(CAST(PRIOR_AUTHORIZATION_YN AS VARCHAR))) IN ('Y', 'YES', '1') THEN 1 ELSE 0 END AS prior_authorization_flag,
            CASE WHEN UPPER(TRIM(CAST(STEP_THERAPY_YN AS VARCHAR))) IN ('Y', 'YES', '1') THEN 1 ELSE 0 END AS step_therapy_flag,
            CASE WHEN UPPER(TRIM(CAST(SELECTED_DRUG_YN AS VARCHAR))) IN ('Y', 'YES', '1') THEN 1 ELSE 0 END AS selected_drug_flag
        FROM read_csv('{form_file.as_posix()}', normalize_names=false, ignore_errors=true)
        """
        df = self.con.execute(query).df()
        
        df["tier_friction_flag"] = (df["tier_level"] >= 4).astype(int)
        df["formulary_friction_score"] = (
            df["prior_authorization_flag"] * 35.0 +
            df["step_therapy_flag"] * 25.0 +
            df["quantity_limit_flag"] * 20.0 +
            df["tier_friction_flag"] * 20.0
        ).round(1)

        out_parquet = CURATED_DIR / "formulary_drug.parquet"
        df.to_parquet(out_parquet, index=False)
        print(f"[canonical] Saved {len(df):,} FORMULARY_DRUG records to {out_parquet.name}")
        return df

    def build_canonical_beneficiary_cost(self) -> pd.DataFrame:
        print("[canonical] Building canonical BENEFICIARY_COST entity...")
        cost_file = next((RAW_DIR / "dataset_1_cms_formulary").glob("beneficiary_cost_file*.csv"), None)
        if not cost_file:
            return pd.DataFrame()
        query = f"""
        SELECT 
            TRIM(CAST(CONTRACT_ID AS VARCHAR)) AS contract_id,
            TRIM(CAST(PLAN_ID AS VARCHAR)) AS plan_id,
            TRIM(CAST(SEGMENT_ID AS VARCHAR)) AS segment_id,
            TRY_CAST(TIER AS INTEGER) AS tier,
            TRY_CAST(DAYS_SUPPLY AS INTEGER) AS days_supply,
            TRIM(CAST(COST_TYPE_PREF AS VARCHAR)) AS cost_type_pref,
            TRY_CAST(COST_AMT_PREF AS DOUBLE) AS cost_amt_pref,
            TRIM(CAST(COST_TYPE_NONPREF AS VARCHAR)) AS cost_type_nonpref,
            TRY_CAST(COST_AMT_NONPREF AS DOUBLE) AS cost_amt_nonpref,
            TRIM(CAST(TIER_SPECIALTY_YN AS VARCHAR)) AS tier_specialty_flag
        FROM read_csv('{cost_file.as_posix()}', normalize_names=false, ignore_errors=true)
        """
        df = self.con.execute(query).df()
        out_parquet = CURATED_DIR / "beneficiary_cost.parquet"
        df.to_parquet(out_parquet, index=False)
        print(f"[canonical] Saved {len(df):,} BENEFICIARY_COST records to {out_parquet.name}")
        return df

    def build_canonical_pharmacy_network(self) -> pd.DataFrame:
        print("[canonical] Building canonical PHARMACY_NETWORK entity...")
        net_file = next((RAW_DIR / "dataset_1_cms_formulary").glob("pharmacy_network_data*.csv"), None)
        if not net_file:
            return pd.DataFrame()
        query = f"""
        SELECT 
            TRIM(CAST(CONTRACT_ID AS VARCHAR)) AS contract_id,
            TRIM(CAST(PLAN_ID AS VARCHAR)) AS plan_id,
            TRIM(CAST(SEGMENT_ID AS VARCHAR)) AS segment_id,
            TRIM(CAST(PHARMACY_NUMBER AS VARCHAR)) AS pharmacy_number,
            TRIM(CAST(PHARMACY_ZIPCODE AS VARCHAR)) AS pharmacy_zipcode,
            TRIM(CAST(PREFERRED_STATUS_RETAIL AS VARCHAR)) AS preferred_status_retail,
            TRIM(CAST(PREFERRED_STATUS_MAIL AS VARCHAR)) AS preferred_status_mail,
            TRY_CAST(BRAND_DISPENSING_FEE_30 AS DOUBLE) AS brand_fee_30,
            TRY_CAST(GENERIC_DISPENSING_FEE_30 AS DOUBLE) AS generic_fee_30
        FROM read_csv('{net_file.as_posix()}', normalize_names=false, ignore_errors=true)
        """
        df = self.con.execute(query).df()
        out_parquet = CURATED_DIR / "pharmacy_network.parquet"
        df.to_parquet(out_parquet, index=False)
        print(f"[canonical] Saved {len(df):,} PHARMACY_NETWORK records to {out_parquet.name}")
        return df

    def build_canonical_utilization(self) -> Dict[str, pd.DataFrame]:
        print("[canonical] Ingesting and aggregating CMS Prescriber Utilization (4GB)...")
        p_file = next((RAW_DIR / "dataset_2_prescriber_utilization").glob("*NPIBN.csv"))

        summary_query = f"""
        SELECT 
            UPPER(TRIM(CAST(Brnd_Name AS VARCHAR))) AS brand_name,
            UPPER(TRIM(CAST(Gnrc_Name AS VARCHAR))) AS generic_name,
            COUNT(DISTINCT Prscrbr_NPI) AS prescriber_count,
            COUNT(DISTINCT Prscrbr_State_Abrvtn) AS state_count,
            SUM(TRY_CAST(REPLACE(CAST(Tot_Clms AS VARCHAR), ',', '') AS DOUBLE)) AS total_claims,
            SUM(TRY_CAST(REPLACE(CAST(Tot_30day_Fills AS VARCHAR), ',', '') AS DOUBLE)) AS total_30day_fills,
            SUM(TRY_CAST(REPLACE(CAST(Tot_Day_Suply AS VARCHAR), ',', '') AS DOUBLE)) AS total_day_supply,
            SUM(TRY_CAST(REPLACE(CAST(Tot_Drug_Cst AS VARCHAR), ',', '') AS DOUBLE)) AS total_drug_cost,
            SUM(TRY_CAST(REPLACE(CAST(Tot_Benes AS VARCHAR), ',', '') AS DOUBLE)) AS total_beneficiaries,
            ROUND(SUM(TRY_CAST(REPLACE(CAST(Tot_Drug_Cst AS VARCHAR), ',', '') AS DOUBLE)) / NULLIF(SUM(TRY_CAST(REPLACE(CAST(Tot_Clms AS VARCHAR), ',', '') AS DOUBLE)), 0), 2) AS avg_cost_per_claim,
            ROUND(SUM(TRY_CAST(REPLACE(CAST(Tot_Drug_Cst AS VARCHAR), ',', '') AS DOUBLE)) / NULLIF(SUM(TRY_CAST(REPLACE(CAST(Tot_30day_Fills AS VARCHAR), ',', '') AS DOUBLE)), 0), 2) AS avg_cost_per_30day_fill,
            ROUND(SUM(TRY_CAST(REPLACE(CAST(Tot_Drug_Cst AS VARCHAR), ',', '') AS DOUBLE)) / NULLIF(SUM(TRY_CAST(REPLACE(CAST(Tot_Benes AS VARCHAR), ',', '') AS DOUBLE)), 0), 2) AS avg_cost_per_beneficiary,
            ROUND(SUM(TRY_CAST(REPLACE(CAST(Tot_Day_Suply AS VARCHAR), ',', '') AS DOUBLE)) / NULLIF(SUM(TRY_CAST(REPLACE(CAST(Tot_Clms AS VARCHAR), ',', '') AS DOUBLE)), 0), 1) AS avg_days_supply_per_claim
        FROM read_csv('{p_file.as_posix()}', ignore_errors=true)
        WHERE Brnd_Name IS NOT NULL AND TRIM(CAST(Brnd_Name AS VARCHAR)) != ''
        GROUP BY UPPER(TRIM(CAST(Brnd_Name AS VARCHAR))), UPPER(TRIM(CAST(Gnrc_Name AS VARCHAR)))
        ORDER BY total_drug_cost DESC
        """
        df_summary = self.con.execute(summary_query).df()
        summary_parquet = CURATED_DIR / "drug_utilization_summary.parquet"
        df_summary.to_parquet(summary_parquet, index=False)
        print(f"[canonical] Saved {len(df_summary):,} DRUG_UTILIZATION_SUMMARY records to {summary_parquet.name}")

        top_pres_query = f"""
        SELECT 
            TRIM(CAST(Prscrbr_NPI AS VARCHAR)) AS prescriber_npi,
            TRIM(CAST(Prscrbr_Last_Org_Name AS VARCHAR)) AS prescriber_last_name,
            TRIM(CAST(Prscrbr_First_Name AS VARCHAR)) AS prescriber_first_name,
            TRIM(CAST(Prscrbr_City AS VARCHAR)) AS prescriber_city,
            TRIM(CAST(Prscrbr_State_Abrvtn AS VARCHAR)) AS prescriber_state,
            TRIM(CAST(Prscrbr_Type AS VARCHAR)) AS prescriber_specialty,
            UPPER(TRIM(CAST(Brnd_Name AS VARCHAR))) AS brand_name,
            UPPER(TRIM(CAST(Gnrc_Name AS VARCHAR))) AS generic_name,
            TRY_CAST(REPLACE(CAST(Tot_Clms AS VARCHAR), ',', '') AS DOUBLE) AS total_claims,
            TRY_CAST(REPLACE(CAST(Tot_30day_Fills AS VARCHAR), ',', '') AS DOUBLE) AS total_30day_fills,
            TRY_CAST(REPLACE(CAST(Tot_Day_Suply AS VARCHAR), ',', '') AS DOUBLE) AS total_day_supply,
            TRY_CAST(REPLACE(CAST(Tot_Drug_Cst AS VARCHAR), ',', '') AS DOUBLE) AS total_drug_cost,
            TRY_CAST(REPLACE(CAST(Tot_Benes AS VARCHAR), ',', '') AS DOUBLE) AS total_beneficiaries,
            ROUND(TRY_CAST(REPLACE(CAST(Tot_Drug_Cst AS VARCHAR), ',', '') AS DOUBLE) / NULLIF(TRY_CAST(REPLACE(CAST(Tot_Clms AS VARCHAR), ',', '') AS DOUBLE), 0), 2) AS cost_per_claim
        FROM read_csv('{p_file.as_posix()}', ignore_errors=true)
        WHERE Tot_Drug_Cst IS NOT NULL AND Tot_Clms IS NOT NULL
        ORDER BY TRY_CAST(REPLACE(CAST(Tot_Drug_Cst AS VARCHAR), ',', '') AS DOUBLE) DESC
        LIMIT 10000
        """
        df_top_pres = self.con.execute(top_pres_query).df()
        pres_parquet = CURATED_DIR / "prescriber_utilization_top.parquet"
        df_top_pres.to_parquet(pres_parquet, index=False)
        print(f"[canonical] Saved {len(df_top_pres):,} top Prescriber records to {pres_parquet.name}")

        return {"summary": df_summary, "prescribers": df_top_pres}

    def build_canonical_synthea(self) -> Dict[str, pd.DataFrame]:
        print("[canonical] Building canonical Synthea PATIENT and MEDICATION_HISTORY entities...")
        syn_dir = RAW_DIR / "dataset_3_synthea"
        
        pat_file = syn_dir / "patients.csv"
        pat_query = f"""
        SELECT 
            TRIM(CAST(Id AS VARCHAR)) AS patient_id,
            TRIM(CAST(BIRTHDATE AS VARCHAR)) AS birthdate,
            TRIM(CAST(DEATHDATE AS VARCHAR)) AS deathdate,
            TRIM(CAST(GENDER AS VARCHAR)) AS gender,
            TRIM(CAST(RACE AS VARCHAR)) AS race,
            TRIM(CAST(ETHNICITY AS VARCHAR)) AS ethnicity,
            TRIM(CAST(CITY AS VARCHAR)) AS city,
            TRIM(CAST(STATE AS VARCHAR)) AS state,
            TRIM(CAST(ZIP AS VARCHAR)) AS zip_code,
            true AS is_synthetic
        FROM read_csv('{pat_file.as_posix()}', normalize_names=false, ignore_errors=true)
        """
        df_pat = self.con.execute(pat_query).df()
        pat_parquet = CURATED_DIR / "synthetic_patients.parquet"
        df_pat.to_parquet(pat_parquet, index=False)

        med_file = syn_dir / "medications.csv"
        med_query = f"""
        SELECT 
            TRIM(CAST(PATIENT AS VARCHAR)) AS patient_id,
            TRIM(CAST(CODE AS VARCHAR)) AS rxnorm_code,
            TRIM(CAST(DESCRIPTION AS VARCHAR)) AS medication_name,
            TRIM(CAST(START AS VARCHAR)) AS start_date,
            TRIM(CAST(STOP AS VARCHAR)) AS stop_date,
            TRY_CAST(DISPENSES AS INTEGER) AS dispenses,
            TRY_CAST(REPLACE(REPLACE(CAST(BASE_COST AS VARCHAR), '$', ''), ',', '') AS DOUBLE) AS base_cost,
            TRY_CAST(REPLACE(REPLACE(CAST(PAYER_COVERAGE AS VARCHAR), '$', ''), ',', '') AS DOUBLE) AS payer_coverage,
            TRY_CAST(REPLACE(REPLACE(CAST(TOTALCOST AS VARCHAR), '$', ''), ',', '') AS DOUBLE) AS total_cost,
            TRIM(CAST(REASONCODE AS VARCHAR)) AS reason_code,
            TRIM(CAST(REASONDESCRIPTION AS VARCHAR)) AS reason_description,
            true AS is_synthetic
        FROM read_csv('{med_file.as_posix()}', normalize_names=false, ignore_errors=true)
        """
        df_med = self.con.execute(med_query).df()
        med_parquet = CURATED_DIR / "synthetic_medication_history.parquet"
        df_med.to_parquet(med_parquet, index=False)
        print(f"[canonical] Saved {len(df_pat):,} synthetic patients and {len(df_med):,} synthetic medication records.")
        return {"patients": df_pat, "medications": df_med}

    def run_all(self):
        print("=== RUNNING CANONICAL DATA PIPELINE ===")
        plans = self.build_canonical_plans()
        formulary = self.build_canonical_formulary()
        costs = self.build_canonical_beneficiary_cost()
        network = self.build_canonical_pharmacy_network()
        util = self.build_canonical_utilization()
        synthea = self.build_canonical_synthea()
        print("=== CANONICAL DATA PIPELINE COMPLETE ===")


if __name__ == "__main__":
    pipeline = CanonicalDataPipeline()
    pipeline.run_all()
