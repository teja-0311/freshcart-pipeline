"""
scratch/run_all_screenshots.py
Connects to Snowflake and prints ALL screenshot-worthy outputs for the
FreshCart DE Assignment (Parts B1-B5).
Run: python scratch/run_all_screenshots.py > scratch/screenshots_output.txt
"""
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

import snowflake.connector
import pandas as pd

ACCOUNT   = os.environ["SNOWFLAKE_ACCOUNT"]
USER      = os.environ["SNOWFLAKE_USER"]
PASSWORD  = os.environ["SNOWFLAKE_PASSWORD"]
WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "FRESHCART_WH")
DATABASE  = os.environ.get("SNOWFLAKE_DATABASE", "FRESHCART")

print("Connecting to Snowflake …")
conn = snowflake.connector.connect(
    account=ACCOUNT,
    user=USER,
    password=PASSWORD,
    role="ACCOUNTADMIN",
    warehouse=WAREHOUSE,
    database=DATABASE,
)
print("Connected:", conn.cursor().execute("SELECT CURRENT_USER(), CURRENT_ACCOUNT()").fetchone())


def show(title, sql):
    sep = "=" * 72
    print(f"\n{sep}")
    print(f"  SCREENSHOT: {title}")
    print(sep)
    with conn.cursor() as cur:
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        if df.empty:
            print("  (no rows)")
        else:
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", 160)
            pd.set_option("display.max_colwidth", 60)
            pd.set_option("display.max_rows", 50)
            print(df.to_string(index=False))
    print()


# ===========================================================================
# B1: Layer Counts
# ===========================================================================
show("B1 – Layer Counts (bronze / silver_clean / quarantine / dedup / gold)", """
SELECT (SELECT COUNT(*) FROM bronze.orders_raw)      AS bronze_rows,
       (SELECT COUNT(*) FROM silver.orders_clean)    AS silver_clean_rows,
       (SELECT COUNT(*) FROM quarantine.orders)      AS quarantine_rows,
       (SELECT COUNT(*) FROM silver.orders_dedup)    AS silver_dedup_rows,
       (SELECT COUNT(*) FROM gold.fct_orders)        AS gold_rows,
       (SELECT SUM(amount_inr) FROM gold.fct_orders) AS total_revenue_inr,
       (SELECT SUM(loyalty_points) FROM gold.fct_orders) AS total_loyalty_points
""")

# ===========================================================================
# B1: Bronze raw records (first 20)
# ===========================================================================
show("B1 – Bronze Layer (raw ingested records, LIMIT 20)", """
SELECT ingest_seq, source, raw
FROM bronze.orders_raw
ORDER BY ingest_seq
LIMIT 20
""")

# ===========================================================================
# B1: Silver Clean
# ===========================================================================
show("B1 – Silver Clean Orders (all rows passing validation)", """
SELECT ingest_seq, source, order_id, email, name, order_date, amount, currency, pincode
FROM silver.orders_clean
ORDER BY ingest_seq
""")

# ===========================================================================
# B1: Quarantine
# ===========================================================================
show("B1 – Quarantine Orders (failed validation)", """
SELECT run_id, source, order_id, reasons
FROM quarantine.orders
""")

# ===========================================================================
# B1: Silver Dedup
# ===========================================================================
show("B1 – Silver Dedup (one surviving row per order_id)", """
SELECT order_id, ingest_seq, updated_at, amount
FROM silver.orders_dedup
ORDER BY order_id
""")

# ===========================================================================
# B1: Customer SCD2 Dimension
# ===========================================================================
show("B1 – Customer SCD2 Dimension (all rows)", """
SELECT *
FROM dim.customers_scd2
ORDER BY cust_id, valid_from
""")

# ===========================================================================
# B1: FX Daily Rates
# ===========================================================================
show("B1 – FX Daily Rates (USD->INR, first 10 dates)", """
SELECT *
FROM ref.fx_daily
WHERE currency = 'USD'
ORDER BY rate_date
LIMIT 10
""")

# ===========================================================================
# B1: Pincode Geo
# ===========================================================================
show("B1 – Pincode Geography (ref.pincode_geo)", """
SELECT *
FROM ref.pincode_geo
""")

# ===========================================================================
# B1: Gold Fact Orders (full detail)
# ===========================================================================
show("B1 – Gold Fact Orders (all columns)", """
SELECT order_id, order_date, tier, amount, currency, fx_rate,
       amount_inr, loyalty_points, is_high_value, city, region
FROM gold.fct_orders
ORDER BY order_id
""")

# ===========================================================================
# B1: Gold Summary Totals
# ===========================================================================
show("B1 – Gold Summary Totals", """
SELECT COUNT(*) AS orders,
       SUM(amount_inr)      AS revenue_inr,
       SUM(loyalty_points)  AS points
FROM gold.fct_orders
""")

# ===========================================================================
# B2: Record Trace ORD-1003
# ===========================================================================
show("B2 – Record Trace: ORD-1003 in Bronze (both source copies)", """
SELECT ingest_seq, source, raw
FROM bronze.orders_raw
WHERE raw:order_id::STRING = 'ORD-1003'
   OR raw:orderId::STRING  = 'ORD-1003'
ORDER BY ingest_seq
""")

show("B2 – Record Trace: ORD-1003 in Silver Clean", """
SELECT ingest_seq, source, order_id, email, name, order_date, amount, currency, pincode, updated_at
FROM silver.orders_clean
WHERE order_id = 'ORD-1003'
ORDER BY ingest_seq
""")

show("B2 – Record Trace: ORD-1003 in Silver Dedup (surviving copy)", """
SELECT order_id, ingest_seq, source, email, amount, updated_at
FROM silver.orders_dedup
WHERE order_id = 'ORD-1003'
""")

show("B2 – Record Trace: ORD-1001 / ORD-1003 / ORD-1005 in Gold", """
SELECT order_id, order_date, email, tier, multiplier, amount_inr, loyalty_points
FROM gold.fct_orders
WHERE order_id IN ('ORD-1001', 'ORD-1003', 'ORD-1005')
ORDER BY order_id
""")

# ===========================================================================
# B3: Currency Validation – quarantine ORD-1006
# ===========================================================================
show("B3 – Currency Validation: ORD-1006 quarantine record (reasons include unsupported_currency)", """
SELECT order_id, source, reasons, row_data:CURRENCY::STRING AS currency
FROM quarantine.orders
WHERE order_id = 'ORD-1006'
""")

show("B3 – Full Quarantine (all rejected orders & reasons)", """
SELECT run_id, source, order_id, reasons
FROM quarantine.orders
ORDER BY order_id
""")

# ===========================================================================
# B4: SCD2 for CUST-02 (Arjun – after Gold tier upgrade)
# ===========================================================================
show("B4 – SCD2 History for CUST-02 (Arjun)", """
SELECT *
FROM dim.customers_scd2
WHERE cust_id = 'CUST-02'
ORDER BY valid_from
""")

show("B4 – Gold Fact Orders after SCD2 update (loyalty points)", """
SELECT order_id, cust_id, tier, multiplier, amount_inr, loyalty_points, published_at
FROM gold.fct_orders
ORDER BY order_id
""")

# ===========================================================================
# B5: Data Quality Check – deliberate failure then recovery
# ===========================================================================
print("\n" + "=" * 72)
print("  SCREENSHOT: B5 – Quality Check: Insert bad row, run checks, delete, re-check")
print("=" * 72)

# Insert bad row
print("\n[1] Inserting deliberate bad row (amount NOT NULL, amount_inr NULL) …")
with conn.cursor() as cur:
    cur.execute("""
        INSERT INTO gold.fct_orders (order_id, order_date, cust_id, amount, currency, amount_inr, loyalty_points)
        VALUES ('MOCK-FAIL-01', '2026-09-01', 'CUST-99', 100.00, 'INR', NULL, 0)
    """)
print("  Row inserted.")

# Run quality checks (manual queries)
quality_queries = {
    "rows gained/lost while enriching":
        "SELECT (SELECT COUNT(*) FROM silver.orders_enriched) - (SELECT COUNT(*) FROM silver.orders_dedup)",
    "duplicate orders in gold":
        "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM gold.fct_orders",
    "orders with no customer match":
        "SELECT COUNT_IF(cust_id IS NULL) FROM silver.orders_enriched",
    "orders with an amount but no FX rate":
        "SELECT COUNT_IF(amount IS NOT NULL AND fx_rate IS NULL) FROM silver.orders_enriched",
    "orders with no city":
        "SELECT COUNT_IF(city IS NULL) FROM silver.orders_enriched",
    "gold orders with amount but missing INR (B5 check)":
        "SELECT COUNT_IF(amount IS NOT NULL AND amount_inr IS NULL) FROM gold.fct_orders",
}

print("\n[2] Quality checks WITH deliberate failure:")
print(f"{'Check name':<45} {'Value':>6}  Status")
print("-" * 60)
for name, sql in quality_queries.items():
    with conn.cursor() as cur:
        cur.execute(sql)
        val = cur.fetchone()[0]
    status = "OK" if val == 0 else "*** PROBLEM ***"
    print(f"  {name:<43} {val:>6}  {status}")

# Delete bad row
print("\n[3] Removing deliberate bad row …")
with conn.cursor() as cur:
    cur.execute("DELETE FROM gold.fct_orders WHERE order_id = 'MOCK-FAIL-01'")
print("  Row deleted.")

print("\n[4] Quality checks AFTER removing bad row:")
print(f"{'Check name':<45} {'Value':>6}  Status")
print("-" * 60)
for name, sql in quality_queries.items():
    with conn.cursor() as cur:
        cur.execute(sql)
        val = cur.fetchone()[0]
    status = "OK" if val == 0 else "*** PROBLEM ***"
    print(f"  {name:<43} {val:>6}  {status}")

print()
conn.close()
print("=" * 72)
print("Done. All screenshot-worthy outputs printed above.")
print("=" * 72)
