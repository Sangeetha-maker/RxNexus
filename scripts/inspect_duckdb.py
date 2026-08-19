"""Inspect all DuckDB / Parquet curated tables, row counts, and top sample data."""
import os
import duckdb
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CURATED_DIR = ROOT_DIR / "data" / "curated"

pd.set_option('display.max_columns', 15)
pd.set_option('display.width', 1000)

def inspect_all():
    con = duckdb.connect()
    parquet_files = sorted(CURATED_DIR.glob("*.parquet"))

    print("=" * 80)
    print(" [DUCKDB] LIVE CURATED STORAGE INVENTORY")
    print("=" * 80)

    for p in parquet_files:
        row_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{p.as_posix()}')").fetchone()[0]
        schema_df = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{p.as_posix()}')").df()
        columns = schema_df["column_name"].tolist()
        
        print(f"\n* Table: {p.name}")
        print(f"   - Row Count : {row_count:,}")
        print(f"   - Columns ({len(columns)}) : {', '.join(columns[:7])}{' ...' if len(columns) > 7 else ''}")

    print("\n" + "=" * 80)
    print(" [QUERY SAMPLE] TOP 5 HIGHEST COST OPPORTUNITIES")
    print("=" * 80)
    
    opp_file = CURATED_DIR / "opportunities.parquet"
    if opp_file.exists():
        top_df = con.execute(f"""
            SELECT brand_name, generic_name, overall_score, priority,
                   total_drug_cost, total_claims, avg_cost_per_claim, tier_level
            FROM read_parquet('{opp_file.as_posix()}')
            ORDER BY total_drug_cost DESC
            LIMIT 5
        """).df()
        
        # Format currency for display
        top_df["total_drug_cost"] = top_df["total_drug_cost"].apply(lambda x: f"${x:,.2f}")
        top_df["avg_cost_per_claim"] = top_df["avg_cost_per_claim"].apply(lambda x: f"${x:,.2f}")
        top_df["total_claims"] = top_df["total_claims"].apply(lambda x: f"{x:,.0f}")
        print(top_df.to_string(index=False))
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    inspect_all()
