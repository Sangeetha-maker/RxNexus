"""PostgreSQL Database Client & Service Layer for RXNexus API.

Provides connection pooling, table query helpers, health checks,
and human-in-the-loop audit logging in PostgreSQL.
"""
import os
import time
from typing import Dict, Any, List, Optional
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    HAS_PSYCOPG2 = False


from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DB_URL = os.getenv(
    "LOCAL_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rxnexus_db")
)

def get_connection():
    """Returns a new psycopg2 connection with dictionary cursor if available."""
    if not HAS_PSYCOPG2 or psycopg2 is None:
        raise ConnectionError("psycopg2 is not installed or available.")
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def get_database_status() -> Dict[str, Any]:
    """Tests connection to PostgreSQL and returns latency and table metrics."""
    if not HAS_PSYCOPG2 or psycopg2 is None:
        return {
            "status": "offline",
            "message": "PostgreSQL driver (psycopg2) not loaded. Operating in high-speed Parquet/DuckDB fallback mode.",
            "latency_ms": 0.0,
            "counts": {}
        }
    start_time = time.time()
    try:
        conn = get_connection()

        latency_ms = round((time.time() - start_time) * 1000, 2)
        with conn.cursor() as cur:
            # Query server version
            cur.execute("SELECT version();")
            ver = cur.fetchone()["version"]

            # Query table counts
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM drug_crosswalk) AS crosswalk_count,
                    (SELECT COUNT(*) FROM fact_prescriber_drug) AS prescriber_facts_count,
                    (SELECT COUNT(*) FROM fact_opportunity) AS opportunity_count,
                    (SELECT COUNT(*) FROM fact_formulary_drug) AS formulary_facts_count;
            """)
            counts = cur.fetchone()

        conn.close()
        return {
            "status": "connected",
            "database_engine": "PostgreSQL 16/18 (Enterprise Relational)",
            "latency_ms": latency_ms,
            "version": ver.split(",")[0] if ver else "PostgreSQL",
            "is_live": True,
            "counts": counts
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "database_engine": "PostgreSQL (Offline/Standby)",
            "latency_ms": None,
            "error": str(e),
            "is_live": False,
            "fallback_mode": "Curated Parquet In-Memory Engine (Active)"
        }

def log_review_decision_pg(opportunity_id: str, status: str, reviewer: str, notes: str) -> bool:
    """Persists a clinical review decision into PostgreSQL audit log."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE fact_opportunity
                SET mapping_status = %s,
                    recommended_review_action = %s
                WHERE opportunity_id = %s;
            """, (status, f"Reviewed by {reviewer}: {notes}", opportunity_id))
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB Error] Failed to log review in PostgreSQL: {e}")
        return False
