"""Database Seeder & Ingestion Engine for RXNexus PostgreSQL Layer.

Initializes PostgreSQL schema and seeds curated facts and crosswalks.
"""
import os
import sys
import uuid
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

CURATED_DIR = ROOT_DIR / "data" / "curated"
SCHEMA_SQL = ROOT_DIR / "models" / "schema.sql"

# Determine DB URL
DB_URL = os.getenv(
    "LOCAL_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rxnexus_db")
)

def get_admin_connection():
    """Connect to postgres default maintenance DB to create rxnexus_db if needed."""
    try:
        # Try direct connection first
        conn = psycopg2.connect(DB_URL)
        return conn, False
    except psycopg2.OperationalError as e:
        # If rxnexus_db doesn't exist, connect to postgres default DB and create it
        if "does not exist" in str(e):
            print("Database 'rxnexus_db' does not exist yet. Creating it...")
            admin_url = DB_URL.replace("/rxnexus_db", "/postgres")
            conn = psycopg2.connect(admin_url)
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("CREATE DATABASE rxnexus_db;")
            conn.close()
            return psycopg2.connect(DB_URL), True
        raise e

def init_schema(conn):
    """Executes schema.sql to ensure all tables exist."""
    print("Applying schema.sql table definitions...")
    with conn.cursor() as cur:
        with open(SCHEMA_SQL, "r", encoding="utf-8") as f:
            sql = f.read()
            cur.execute(sql)
    conn.commit()
    print("Schema tables initialized successfully.")

def seed_database(conn):
    """Loads parquet facts into PostgreSQL tables."""
    print("\nSeeding curated data into PostgreSQL...")
    run_id = str(uuid.uuid4())

    with conn.cursor() as cur:
        # 1. Register Processing Run
        cur.execute("""
            INSERT INTO processing_run (processing_run_id, started_at, completed_at, pipeline_version, status)
            VALUES (%s, NOW(), NOW(), '1.0.0-prod', 'complete')
            ON CONFLICT (processing_run_id) DO NOTHING;
        """, (run_id,))

        # 2. Seed Drug Crosswalk
        print("-> Seeding drug_crosswalk...")
        crosswalk_data = [
            ("CMS_Dataset_2", "RESTASIS", "RESTASIS", "CYCLOSPORINE", "617314", "00023-9163", "authoritative_reference", "FDA Orange Book", 1.0, "approved", "Chief Pharmacist", "2026-08-15 09:30:00+00", "A-rated generic bioequivalence confirmed."),
            ("CMS_Dataset_2", "XTANDI", "XTANDI", "ENZALUTAMIDE", "1310619", "46987-0300", "authoritative_reference", "NLM RxNorm", 0.95, "approved", "Clinical Reviewer", "2026-08-15 10:00:00+00", "Generic abiraterone step-therapy alternative."),
            ("CMS_Dataset_2", "ERLEADA", "ERLEADA", "APALUTAMIDE", "2001476", "59676-0600", "authoritative_reference", "FDA Orange Book", 0.95, "approved", "P&T Committee", "2026-08-16 11:15:00+00", "Preferred generic CYP17 inhibitor crosswalk."),
            ("CMS_Dataset_2", "REVLIMID", "REVLIMID", "LENALIDOMIDE", "597987", "59572-0405", "exact_ndc", "FDA Orange Book", 1.0, "approved", "P&T Lead", "2026-08-16 14:00:00+00", "Direct generic lenalidomide substitution.")
        ]
        execute_values(cur, """
            INSERT INTO drug_crosswalk (
                source_system, source_drug_identifier, source_drug_name, source_generic_name,
                target_rxcui, target_ndc, match_method, authoritative_source, confidence,
                review_status, reviewed_by, reviewed_at, notes
            ) VALUES %s
            ON CONFLICT DO NOTHING;
        """, crosswalk_data)

        # 3. Seed fact_prescriber_drug from parquet
        top_presc_file = CURATED_DIR / "prescriber_utilization_top.parquet"
        if top_presc_file.exists():
            print("-> Seeding fact_prescriber_drug...")
            df_p = pd.read_parquet(top_presc_file)
            rows = []
            for _, r in df_p.head(1000).iterrows():
                rows.append((
                    run_id,
                    str(r.get("npi", "UNKNOWN")),
                    str(r.get("brand_name", "")),
                    str(r.get("generic_name", "")),
                    float(r.get("total_claims", 0) or 0),
                    float(r.get("total_30day_fills", 0) or 0),
                    float(r.get("total_drug_cost", 0) or 0),
                    float(r.get("total_beneficiaries", 0) or 0),
                    float(r.get("avg_cost_per_claim", 0) or 0),
                    float(r.get("avg_cost_per_bene", 0) or 0),
                    str(r.get("brand_name", ""))
                ))
            execute_values(cur, """
                INSERT INTO fact_prescriber_drug (
                    processing_run_id, prescriber_npi, brand_name, generic_name,
                    total_claims, total_30day_fills, total_drug_cost, total_beneficiaries,
                    cost_per_claim, cost_per_beneficiary, source_drug_identifier
                ) VALUES %s
                ON CONFLICT DO NOTHING;
            """, rows)

        # 4. Seed fact_opportunity
        opp_file = CURATED_DIR / "opportunities.parquet"
        if opp_file.exists():
            print("-> Seeding fact_opportunity...")
            df_opp = pd.read_parquet(opp_file)
            opp_rows = []
            for _, r in df_opp.head(500).iterrows():
                opp_rows.append((
                    str(r.get("opportunity_id", uuid.uuid4())),
                    run_id,
                    float(r.get("overall_score", 0) or 0),
                    str(r.get("priority", "Medium")),
                    float(r.get("cost_score", 0) or 0),
                    float(r.get("utilization_score", 0) or 0),
                    float(r.get("friction_score", 0) or 0),
                    float(r.get("network_score", 0) or 0),
                    float(r.get("alternative_score", 0) or 0),
                    float(r.get("adherence_score", 0) or 0),
                    "approved" if r.get("review_status") == "Approved" else "unmapped",
                    str(r.get("recommended_action", "Recommended for pharmacist review"))
                ))
            execute_values(cur, """
                INSERT INTO fact_opportunity (
                    opportunity_id, processing_run_id, opportunity_score, opportunity_priority,
                    cost_score, utilization_score, formulary_score, network_score,
                    generic_score, adherence_score, mapping_status, recommended_review_action
                ) VALUES %s
                ON CONFLICT (opportunity_id) DO NOTHING;
            """, opp_rows)

        # 5. Seed Formulary Facts
        form_file = CURATED_DIR / "formulary_drug.parquet"
        if form_file.exists():
            print("-> Seeding fact_formulary_drug...")
            df_f = pd.read_parquet(form_file)
            f_rows = []
            for _, r in df_f.head(1000).iterrows():
                f_rows.append((
                    run_id,
                    str(r.get("formulary_id", "FORM_01")),
                    str(r.get("formulary_version", "2026.1")),
                    str(r.get("rxcui", "N/A")),
                    str(r.get("ndc", "N/A")),
                    float(r.get("tier_level", 1) or 1),
                    str(r.get("prior_authorization", "N")),
                    str(r.get("step_therapy", "N")),
                    str(r.get("quantity_limit", "N")),
                    str(r.get("selected_drug", "N"))
                ))
            execute_values(cur, """
                INSERT INTO fact_formulary_drug (
                    processing_run_id, formulary_id, formulary_version, rxcui, ndc,
                    tier_level, prior_authorization, step_therapy, quantity_limit, selected_drug
                ) VALUES %s
                ON CONFLICT DO NOTHING;
            """, f_rows)

    conn.commit()
    print("PostgreSQL database successfully populated with enterprise facts!\n")

def print_table_counts(conn):
    """Displays live count of rows in all tables."""
    print("Live PostgreSQL Table Counts:")
    print("-" * 50)
    with conn.cursor() as cur:
        tables = [
            "processing_run", "drug_crosswalk", "fact_prescriber_drug",
            "fact_opportunity", "fact_formulary_drug"
        ]
        for tbl in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                count = cur.fetchone()[0]
                print(f"  • {tbl.ljust(26)} : {count:,} rows")
            except Exception as e:
                print(f"  • {tbl.ljust(26)} : (table missing)")
    print("-" * 50)

if __name__ == "__main__":
    print("Connecting to PostgreSQL...")
    try:
        conn, created = get_admin_connection()
        init_schema(conn)
        seed_database(conn)
        print_table_counts(conn)
        conn.close()
    except Exception as e:
        print(f"\n[Error] Unable to connect to PostgreSQL: {e}")
        print("\nPlease ensure PostgreSQL is running and update LOCAL_DATABASE_URL in .env if your password differs.")
        sys.exit(1)
