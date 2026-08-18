"""High-performance format-specific dataset parsers for PayerRx Optimizer.

Implements DuckDB and chunked streaming readers to project required fields,
preserve source field names, and build the 3-layer data architecture:
- Raw -> Staging -> Curated
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Generator, Optional
import duckdb
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
STAGING_DIR = ROOT_DIR / "data" / "staging"
CURATED_DIR = ROOT_DIR / "data" / "curated"

STAGING_DIR.mkdir(parents=True, exist_ok=True)
CURATED_DIR.mkdir(parents=True, exist_ok=True)


class CMSFormularyParser:
    """Parser for CMS Medicare Part D Formulary files."""

    def __init__(self, raw_path: Path = RAW_DIR / "dataset_1_cms_formulary"):
        self.raw_path = raw_path
        self.con = duckdb.connect()

    def parse_plans(self) -> pd.DataFrame:
        plan_file = next(self.raw_path.glob("plan_information*.csv"), None)
        if not plan_file:
            raise FileNotFoundError("plan_information CSV not found")
        
        query = f"""
        SELECT 
            TRIM(CONTRACT_ID) AS contract_id,
            TRIM(PLAN_ID) AS plan_id,
            TRIM(SEGMENT_ID) AS segment_id,
            TRIM(CONTRACT_NAME) AS contract_name,
            TRIM(PLAN_NAME) AS plan_name,
            TRIM(FORMULARY_ID) AS formulary_id,
            TRY_CAST(REPLACE(REPLACE(PREMIUM, '$', ''), ',', '') AS DOUBLE) AS premium,
            TRY_CAST(REPLACE(REPLACE(DEDUCTIBLE, '$', ''), ',', '') AS DOUBLE) AS deductible,
            TRIM(STATE) AS state,
            TRIM(SNP) AS snp_flag,
            TRIM(PLAN_SUPPRESSED_YN) AS suppressed_flag
        FROM read_csv_auto('{plan_file.as_posix()}', normalize_names=false, ignore_errors=true)
        """
        df = self.con.execute(query).df()
        return df

    def parse_basic_formulary(self, limit: Optional[int] = None) -> pd.DataFrame:
        form_file = next(self.raw_path.glob("basic_drugs_formulary_file*.csv"), None)
        if not form_file:
            raise FileNotFoundError("basic_drugs_formulary_file CSV not found")

        limit_clause = f"LIMIT {limit}" if limit else ""
        query = f"""
        SELECT 
            TRIM(FORMULARY_ID) AS formulary_id,
            TRIM(FORMULARY_VERSION) AS formulary_version,
            TRIM(CONTRACT_YEAR) AS contract_year,
            TRIM(RXCUI) AS rxcui,
            TRIM(NDC) AS ndc,
            TRY_CAST(TIER_LEVEL_VALUE AS INTEGER) AS tier_level,
            CASE WHEN UPPER(TRIM(QUANTITY_LIMIT_YN)) IN ('Y', 'YES', '1') THEN 1 ELSE 0 END AS quantity_limit_flag,
            TRY_CAST(QUANTITY_LIMIT_AMOUNT AS DOUBLE) AS quantity_limit_amount,
            TRY_CAST(QUANTITY_LIMIT_DAYS AS INTEGER) AS quantity_limit_days,
            CASE WHEN UPPER(TRIM(PRIOR_AUTHORIZATION_YN)) IN ('Y', 'YES', '1') THEN 1 ELSE 0 END AS prior_authorization_flag,
            CASE WHEN UPPER(TRIM(STEP_THERAPY_YN)) IN ('Y', 'YES', '1') THEN 1 ELSE 0 END AS step_therapy_flag,
            CASE WHEN UPPER(TRIM(SELECTED_DRUG_YN)) IN ('Y', 'YES', '1') THEN 1 ELSE 0 END AS selected_drug_flag
        FROM read_csv_auto('{form_file.as_posix()}', normalize_names=false, ignore_errors=true)
        {limit_clause}
        """
        df = self.con.execute(query).df()
        return df

    def parse_beneficiary_cost(self, limit: Optional[int] = None) -> pd.DataFrame:
        cost_file = next(self.raw_path.glob("beneficiary_cost_file*.csv"), None)
        if not cost_file:
            return pd.DataFrame()
        limit_clause = f"LIMIT {limit}" if limit else ""
        query = f"""
        SELECT 
            TRIM(CONTRACT_ID) AS contract_id,
            TRIM(PLAN_ID) AS plan_id,
            TRIM(SEGMENT_ID) AS segment_id,
            TRY_CAST(TIER AS INTEGER) AS tier,
            TRY_CAST(DAYS_SUPPLY AS INTEGER) AS days_supply,
            TRIM(COST_TYPE_PREF) AS cost_type_pref,
            TRY_CAST(COST_AMT_PREF AS DOUBLE) AS cost_amt_pref,
            TRIM(COST_TYPE_NONPREF) AS cost_type_nonpref,
            TRY_CAST(COST_AMT_NONPREF AS DOUBLE) AS cost_amt_nonpref,
            TRIM(TIER_SPECIALTY_YN) AS tier_specialty_flag
        FROM read_csv_auto('{cost_file.as_posix()}', normalize_names=false, ignore_errors=true)
        {limit_clause}
        """
        return self.con.execute(query).df()

    def parse_pharmacy_network(self, limit: Optional[int] = None) -> pd.DataFrame:
        net_file = next(self.raw_path.glob("pharmacy_network_data*.csv"), None)
        if not net_file:
            return pd.DataFrame()
        limit_clause = f"LIMIT {limit}" if limit else ""
        query = f"""
        SELECT 
            TRIM(CONTRACT_ID) AS contract_id,
            TRIM(PLAN_ID) AS plan_id,
            TRIM(SEGMENT_ID) AS segment_id,
            TRIM(PHARMACY_NUMBER) AS pharmacy_number,
            TRIM(PHARMACY_ZIPCODE) AS pharmacy_zipcode,
            TRIM(PREFERRED_STATUS_RETAIL) AS preferred_status_retail,
            TRIM(PREFERRED_STATUS_MAIL) AS preferred_status_mail,
            TRY_CAST(BRAND_DISPENSING_FEE_30 AS DOUBLE) AS brand_fee_30,
            TRY_CAST(GENERIC_DISPENSING_FEE_30 AS DOUBLE) AS generic_fee_30
        FROM read_csv_auto('{net_file.as_posix()}', normalize_names=false, ignore_errors=true)
        {limit_clause}
        """
        return self.con.execute(query).df()


class CMSPrescriberUtilizationParser:
    """Parser and projection engine for CMS Part D Prescriber Utilization (4GB)."""

    def __init__(self, raw_path: Path = RAW_DIR / "dataset_2_prescriber_utilization"):
        self.raw_path = raw_path
        self.con = duckdb.connect()

    def get_prescriber_file(self) -> Path:
        p_file = next(self.raw_path.glob("*NPIBN.csv"), None)
        if not p_file:
            raise FileNotFoundError("CMS NPI Prescriber Utilization CSV not found")
        return p_file

    def compute_drug_aggregations(self) -> pd.DataFrame:
        """Aggregates the 4GB prescriber dataset down to drug-level national benchmarks."""
        p_file = self.get_prescriber_file()
        print(f"[PrescriberParser] Aggregating CMS prescriber dataset ({p_file.name}) using DuckDB...")
        
        query = f"""
        SELECT 
            UPPER(TRIM(Brnd_Name)) AS brand_name,
            UPPER(TRIM(Gnrc_Name)) AS generic_name,
            COUNT(DISTINCT Prscrbr_NPI) AS prescriber_count,
            COUNT(DISTINCT Prscrbr_State_Abrvtn) AS state_count,
            SUM(TRY_CAST(REPLACE(Tot_Clms, ',', '') AS DOUBLE)) AS total_claims,
            SUM(TRY_CAST(REPLACE(Tot_30day_Fills, ',', '') AS DOUBLE)) AS total_30day_fills,
            SUM(TRY_CAST(REPLACE(Tot_Day_Suply, ',', '') AS DOUBLE)) AS total_day_supply,
            SUM(TRY_CAST(REPLACE(Tot_Drug_Cst, ',', '') AS DOUBLE)) AS total_drug_cost,
            SUM(TRY_CAST(REPLACE(Tot_Benes, ',', '') AS DOUBLE)) AS total_beneficiaries,
            ROUND(SUM(TRY_CAST(REPLACE(Tot_Drug_Cst, ',', '') AS DOUBLE)) / NULLIF(SUM(TRY_CAST(REPLACE(Tot_Clms, ',', '') AS DOUBLE)), 0), 2) AS avg_cost_per_claim,
            ROUND(SUM(TRY_CAST(REPLACE(Tot_Drug_Cst, ',', '') AS DOUBLE)) / NULLIF(SUM(TRY_CAST(REPLACE(Tot_30day_Fills, ',', '') AS DOUBLE)), 0), 2) AS avg_cost_per_30day_fill,
            ROUND(SUM(TRY_CAST(REPLACE(Tot_Drug_Cst, ',', '') AS DOUBLE)) / NULLIF(SUM(TRY_CAST(REPLACE(Tot_Benes, ',', '') AS DOUBLE)), 0), 2) AS avg_cost_per_beneficiary,
            ROUND(SUM(TRY_CAST(REPLACE(Tot_Day_Suply, ',', '') AS DOUBLE)) / NULLIF(SUM(TRY_CAST(REPLACE(Tot_Clms, ',', '') AS DOUBLE)), 0), 1) AS avg_days_supply_per_claim
        FROM read_csv_auto('{p_file.as_posix()}', ignore_errors=true)
        WHERE Brnd_Name IS NOT NULL AND TRIM(Brnd_Name) != ''
        GROUP BY UPPER(TRIM(Brnd_Name)), UPPER(TRIM(Gnrc_Name))
        ORDER BY total_drug_cost DESC
        """
        df = self.con.execute(query).df()
        print(f"[PrescriberParser] Aggregated {len(df):,} unique Brand x Generic pairs.")
        return df

    def compute_state_aggregations(self) -> pd.DataFrame:
        """Aggregates utilization by State and Drug for geographic drill-downs."""
        p_file = self.get_prescriber_file()
        query = f"""
        SELECT 
            TRIM(Prscrbr_State_Abrvtn) AS state,
            UPPER(TRIM(Brnd_Name)) AS brand_name,
            UPPER(TRIM(Gnrc_Name)) AS generic_name,
            COUNT(DISTINCT Prscrbr_NPI) AS prescriber_count,
            SUM(TRY_CAST(REPLACE(Tot_Clms, ',', '') AS DOUBLE)) AS total_claims,
            SUM(TRY_CAST(REPLACE(Tot_30day_Fills, ',', '') AS DOUBLE)) AS total_30day_fills,
            SUM(TRY_CAST(REPLACE(Tot_Drug_Cst, ',', '') AS DOUBLE)) AS total_drug_cost,
            SUM(TRY_CAST(REPLACE(Tot_Benes, ',', '') AS DOUBLE)) AS total_beneficiaries,
            ROUND(SUM(TRY_CAST(REPLACE(Tot_Drug_Cst, ',', '') AS DOUBLE)) / NULLIF(SUM(TRY_CAST(REPLACE(Tot_Clms, ',', '') AS DOUBLE)), 0), 2) AS cost_per_claim
        FROM read_csv_auto('{p_file.as_posix()}', ignore_errors=true)
        WHERE Prscrbr_State_Abrvtn IS NOT NULL AND TRIM(Prscrbr_State_Abrvtn) != ''
        GROUP BY TRIM(Prscrbr_State_Abrvtn), UPPER(TRIM(Brnd_Name)), UPPER(TRIM(Gnrc_Name))
        ORDER BY total_drug_cost DESC
        """
        df = self.con.execute(query).df()
        return df

    def get_top_prescriber_opportunities(self, limit: int = 5000) -> pd.DataFrame:
        """Extracts top prescriber-drug records for opportunity queue."""
        p_file = self.get_prescriber_file()
        query = f"""
        SELECT 
            TRIM(Prscrbr_NPI) AS prescriber_npi,
            TRIM(Prscrbr_Last_Org_Name) AS prescriber_last_name,
            TRIM(Prscrbr_First_Name) AS prescriber_first_name,
            TRIM(Prscrbr_City) AS prescriber_city,
            TRIM(Prscrbr_State_Abrvtn) AS prescriber_state,
            TRIM(Prscrbr_Type) AS prescriber_specialty,
            UPPER(TRIM(Brnd_Name)) AS brand_name,
            UPPER(TRIM(Gnrc_Name)) AS generic_name,
            TRY_CAST(REPLACE(Tot_Clms, ',', '') AS DOUBLE) AS total_claims,
            TRY_CAST(REPLACE(Tot_30day_Fills, ',', '') AS DOUBLE) AS total_30day_fills,
            TRY_CAST(REPLACE(Tot_Day_Suply, ',', '') AS DOUBLE) AS total_day_supply,
            TRY_CAST(REPLACE(Tot_Drug_Cst, ',', '') AS DOUBLE) AS total_drug_cost,
            TRY_CAST(REPLACE(Tot_Benes, ',', '') AS DOUBLE) AS total_beneficiaries,
            ROUND(TRY_CAST(REPLACE(Tot_Drug_Cst, ',', '') AS DOUBLE) / NULLIF(TRY_CAST(REPLACE(Tot_Clms, ',', '') AS DOUBLE), 0), 2) AS cost_per_claim
        FROM read_csv_auto('{p_file.as_posix()}', ignore_errors=true)
        WHERE Tot_Drug_Cst IS NOT NULL AND Tot_Clms IS NOT NULL
        ORDER BY TRY_CAST(REPLACE(Tot_Drug_Cst, ',', '') AS DOUBLE) DESC
        LIMIT {limit}
        """
        df = self.con.execute(query).df()
        return df


class SyntheaClinicalParser:
    """Parser for Synthea synthetic patient clinical & medication history."""

    def __init__(self, raw_path: Path = RAW_DIR / "dataset_3_synthea"):
        self.raw_path = raw_path
        self.con = duckdb.connect()

    def parse_patients(self) -> pd.DataFrame:
        pat_file = self.raw_path / "patients.csv"
        if not pat_file.exists():
            return pd.DataFrame()
        query = f"""
        SELECT 
            TRIM(Id) AS patient_id,
            TRIM(BIRTHDATE) AS birthdate,
            TRIM(DEATHDATE) AS deathdate,
            TRIM(GENDER) AS gender,
            TRIM(RACE) AS race,
            TRIM(ETHNICITY) AS ethnicity,
            TRIM(CITY) AS city,
            TRIM(STATE) AS state,
            TRIM(ZIP) AS zip_code,
            true AS is_synthetic
        FROM read_csv_auto('{pat_file.as_posix()}', normalize_names=false, ignore_errors=true)
        """
        return self.con.execute(query).df()

    def parse_medications(self) -> pd.DataFrame:
        med_file = self.raw_path / "medications.csv"
        if not med_file.exists():
            return pd.DataFrame()
        query = f"""
        SELECT 
            TRIM(PATIENT) AS patient_id,
            TRIM(CODE) AS rxnorm_code,
            TRIM(DESCRIPTION) AS medication_name,
            TRIM(START) AS start_date,
            TRIM(STOP) AS stop_date,
            TRY_CAST(DISPENSES AS INTEGER) AS dispenses,
            TRY_CAST(REPLACE(REPLACE(BASE_COST, '$', ''), ',', '') AS DOUBLE) AS base_cost,
            TRY_CAST(REPLACE(REPLACE(PAYER_COVERAGE, '$', ''), ',', '') AS DOUBLE) AS payer_coverage,
            TRY_CAST(REPLACE(REPLACE(TOTALCOST, '$', ''), ',', '') AS DOUBLE) AS total_cost,
            TRIM(REASONCODE) AS reason_code,
            TRIM(REASONDESCRIPTION) AS reason_description,
            true AS is_synthetic
        FROM read_csv_auto('{med_file.as_posix()}', normalize_names=false, ignore_errors=true)
        """
        return self.con.execute(query).df()

    def parse_conditions(self) -> pd.DataFrame:
        cond_file = self.raw_path / "conditions.csv"
        if not cond_file.exists():
            return pd.DataFrame()
        query = f"""
        SELECT 
            TRIM(PATIENT) AS patient_id,
            TRIM(CODE) AS snomed_code,
            TRIM(DESCRIPTION) AS condition_name,
            TRIM(START) AS onset_date,
            TRIM(STOP) AS resolved_date,
            true AS is_synthetic
        FROM read_csv_auto('{cond_file.as_posix()}', normalize_names=false, ignore_errors=true)
        """
        return self.con.execute(query).df()


if __name__ == "__main__":
    print("[parsers.py] Testing parsers...")
    fp = CMSFormularyParser()
    plans = fp.parse_plans()
    print(f"Plans parsed: {len(plans):,} rows")
