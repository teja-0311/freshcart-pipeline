import os, sys
import snowflake.connector
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

ctx = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account="ae17723.ap-southeast-7.aws",
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE")
)
cs = ctx.cursor()

def run_checks(label):
    print(f"\n--- {label} ---")
    queries = [
        ("rows gained or lost while enriching",
         "SELECT ABS((SELECT count(*) FROM silver.orders_clean) - (SELECT count(*) FROM silver.orders_enriched))"),
        ("duplicate orders in gold",
         "SELECT count(*) FROM (SELECT order_id FROM gold.fct_orders GROUP BY order_id HAVING count(*) > 1)"),
        ("orders with no customer match",
         "SELECT count(*) FROM gold.fct_orders WHERE cust_id IS NULL"),
        ("orders with an amount but no FX rate",
         "SELECT count(*) FROM gold.fct_orders WHERE amount IS NOT NULL AND fx_rate IS NULL"),
        ("orders with no city",
         "SELECT count(*) FROM gold.fct_orders WHERE city IS NULL"),
        ("gold orders with amount but missing INR",
         "SELECT count(*) FROM gold.fct_orders WHERE amount IS NOT NULL AND amount_inr IS NULL")
    ]
    for name, q in queries:
        val = cs.execute(q).fetchone()[0]
        status = "OK" if val == 0 else "PROBLEM"
        print(f"   {name:40s} {val:3d}   {status}")

# 1. Insert deliberate bad record to demonstrate failure
cs.execute("""
INSERT INTO gold.fct_orders (order_id, order_date, cust_id, amount, currency, amount_inr)
VALUES ('ORD-MOCK-BAD', '2026-09-01', 'CUST-01', 500, 'INR', NULL)
""")
run_checks("DEMONSTRATION: Check 6 Failure (Bad Record Injected)")

# 2. Cleanup mock record to demonstrate recovery
cs.execute("DELETE FROM gold.fct_orders WHERE order_id = 'ORD-MOCK-BAD'")
run_checks("DEMONSTRATION: Quality Check Recovery (After Cleanup)")

cs.close()
ctx.close()
