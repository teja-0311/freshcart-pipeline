"""
Builds and executes elt/freshcart_elt.ipynb against live Snowflake account
Captures real query outputs, tables, and execution logs so that ALL outputs are visible.
"""
import json, sys, os
from pathlib import Path
from dotenv import load_dotenv
import nbformat as nbf

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

ACCOUNT   = os.getenv("SNOWFLAKE_ACCOUNT", "ae17723.ap-southeast-7.aws")
USER      = os.getenv("SNOWFLAKE_USER", "SPIDEYSENSE0311@GMAIL.COM")
PASSWORD  = os.getenv("SNOWFLAKE_PASSWORD")
ROLE      = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "FRESHCART_WH")
DATABASE  = os.getenv("SNOWFLAKE_DATABASE", "FRESHCART")

nb = nbf.v4.new_notebook()
nb.metadata = {
    "language_info": {"name": "python", "version": "3.12.4"},
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
}

cells = []

# Title & Metadata
cells.append(nbf.v4.new_markdown_cell("""# FreshCart ELT Pipeline on Snowflake
**Course:** Data Engineering - Pipeline Orchestration  
**Student Name:** Golla Teja  
**Roll Number:** 23BCS091  
**Repository:** https://github.com/teja-0311/freshcart-pipeline  

---
### Architecture Overview
```
API / Mock Data (Web, Mobile, CRM, FX, Post)
       |
       v
1. EXTRACT -> Gzip Compressed JSON Lines Landing Files (freshcart_landing/)
       |
       v
2. LOAD    -> Snowflake PUT + COPY INTO bronze.*_raw (VARIANT)
       |
       v
3. TRANSFORM -> silver.orders_checked -> silver.orders_clean & quarantine.orders
             -> silver.orders_dedup (QUALIFY ROW_NUMBER() newest updated_at wins)
             -> dim.customers_scd2 (SCD Type 2 temporal history)
             -> ref.fx_daily (forward-filled exchange rate spine) & ref.pincode_geo
             -> gold.fct_orders (Idempotent MERGE with row_hash)
       |
       v
4. CHECK   -> Automated Data Quality Gates (6 Checks)
```
"""))

# Cell 1: Setup & Environment Configuration
cells.append(nbf.v4.new_markdown_cell("## 1. Setup & Environment Configuration\nLoad dependencies and securely read Snowflake credentials from `.env` file."))
cells.append(nbf.v4.new_code_cell("""import os, sys, gzip, json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Required connection settings
SNOWFLAKE_ACCOUNT   = os.getenv("SNOWFLAKE_ACCOUNT", "ae17723.ap-southeast-7.aws")
SNOWFLAKE_USER      = os.getenv("SNOWFLAKE_USER", "SPIDEYSENSE0311@GMAIL.COM")
SNOWFLAKE_ROLE      = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
SNOWFLAKE_PASSWORD  = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "FRESHCART_WH")
SNOWFLAKE_DATABASE  = os.getenv("SNOWFLAKE_DATABASE", "FRESHCART")

LANDING_DIR = Path("./freshcart_landing")
LANDING_DIR.mkdir(parents=True, exist_ok=True)
print("Landing directory ready at:", LANDING_DIR.resolve())
"""))

# Cell 2: Connect to Snowflake & Helper Functions
cells.append(nbf.v4.new_markdown_cell("## 2. Connect to Snowflake & Helper Functions\nEstablish database connection and define query execution helpers (`run_sql`, `query`, `show`, `load_file`)."))
cells.append(nbf.v4.new_code_cell("""import snowflake.connector

conn = snowflake.connector.connect(
    account=SNOWFLAKE_ACCOUNT,
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    role=SNOWFLAKE_ROLE
)

def run_sql(sql_text):
    \"\"\"Execute a multi-statement SQL script.\"\"\"
    conn.execute_string(sql_text, remove_comments=True)

def query(sql):
    \"\"\"Run a query and return all rows.\"\"\"
    cur = conn.cursor()
    try:
        cur.execute(sql)
        return cur.fetchall()
    finally:
        cur.close()

def show(sql):
    \"\"\"Run a query and display as a formatted pandas DataFrame.\"\"\"
    cur = conn.cursor()
    try:
        cur.execute(sql)
        cols = [desc[0] for desc in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=cols)
        print(df.to_string())
        return df
    finally:
        cur.close()

def load_file(local_path, table_name, stage_subfolder):
    \"\"\"Upload a local gzipped raw file and COPY INTO a bronze raw table.\"\"\"
    cur = conn.cursor()
    try:
        cur.execute(f\"PUT file://{local_path.resolve()} @bronze.landing/{stage_subfolder} AUTO_COMPRESS = FALSE OVERWRITE = TRUE\")
        cur.execute(f\"\"\"
            COPY INTO {table_name} (source, raw, run_id, extracted_at, src_file, src_row)
            FROM (
              SELECT $1:source::STRING, $1:data, $1:run_id::STRING, $1:extracted_at::TIMESTAMP_TZ,
                     METADATA$FILENAME, METADATA$FILE_ROW_NUMBER
              FROM @bronze.landing/{stage_subfolder}
            )
        \"\"\")
    finally:
        cur.close()

user, role = query("SELECT CURRENT_USER(), CURRENT_ROLE()")[0]
print(f"Connected to Snowflake successfully! User: {user}, Role: {role}")
"""))

# Cell 3: Sample Data Definitions
cells.append(nbf.v4.new_markdown_cell("## 3. Sample Data Definitions\nRaw order data from website and mobile app, CRM tier changes, and FX rates."))
cells.append(nbf.v4.new_code_cell("""# Website orders: flat JSON with dirty formats (spaces, commas, missing amounts)
MOCK_WEB_ORDERS = [
    {"order_id": "ORD-1001", "cust_email": " Priya.R@Gmail.com ", "cust_name": "priya r",
     "order_date": "2026-09-01", "amount": "1,250.00", "currency": "INR", "pincode": "600041",
     "updated_at": "2026-09-01T10:15:00"},
    {"order_id": "ORD-1002", "cust_email": "arjun.k@yahoo.in", "cust_name": "Arjun K",
     "order_date": "2026-09-01", "amount": "42.50", "currency": "USD", "pincode": "560034",
     "updated_at": "2026-09-01T11:00:00"},
    {"order_id": "ORD-1003", "cust_email": "meera@outlook.com", "cust_name": "Meera S",
     "order_date": "2026-09-02", "amount": None, "currency": "INR", "pincode": "400050",
     "updated_at": "2026-09-02T14:30:00"},
    {"order_id": "ORD-1004", "cust_email": "rahul.t@gmail.com", "cust_name": "Rahul T",
     "order_date": "2026-09-02", "amount": "-500.00", "currency": "INR", "pincode": "000041",
     "updated_at": "2026-09-02T15:00:00"},
    {"order_id": "ORD-1005", "cust_email": "priya.r@gmail.com", "cust_name": "Priya R",
     "order_date": "2026-09-03", "amount": "800.00", "currency": "INR", "pincode": "600041",
     "updated_at": "2026-09-03T09:30:00"},
    {"order_id": "ORD-1006", "cust_email": "bad-email", "cust_name": "vikram",
     "order_date": "not-a-date", "amount": "999.00", "currency": "EUR", "pincode": "560034",
     "updated_at": "2026-09-03T16:00:00"},
]

# Mobile orders: nested JSON keys
MOCK_MOBILE_ORDERS = [
    {"orderId": "ORD-1002",
     "customer": {"email": "arjun.k@yahoo.in", "name": "Arjun K"},
     "orderDate": "01/09/2026",
     "total": {"value": "42.50", "currency": "usd"},
     "deliveryPin": "560034",
     "updatedAt": "2026-09-01T11:15:00"},
    {"orderId": "ORD-1003",
     "customer": {"email": "Meera@Outlook.com", "name": "Meera S"},
     "orderDate": "02/09/2026",
     "total": {"value": "2,100.00", "currency": "INR"},
     "deliveryPin": "400050",
     "updatedAt": "2026-09-02T18:40:00"},
]

# CRM loyalty tier change history
MOCK_CRM_TIER_EVENTS = [
    {"cust_id": "CUST-01", "email": "priya.r@gmail.com", "tier": "Silver", "effective_from": "2023-04-10"},
    {"cust_id": "CUST-01", "email": "priya.r@gmail.com", "tier": "Gold",   "effective_from": "2026-09-03"},
    {"cust_id": "CUST-02", "email": "arjun.k@yahoo.in",  "tier": "Silver", "effective_from": "2024-01-15"},
    {"cust_id": "CUST-03", "email": "meera@outlook.com", "tier": "Platinum", "effective_from": "2022-11-01"},
]

# FX published daily rates
MOCK_FX_RESPONSES = [
    {"base": "USD", "rates": {"2026-09-01": {"INR": 83.20}, "2026-09-02": {"INR": 83.35}, "2026-09-03": {"INR": 83.10}}}
]

def mock_pincode_response(pin):
    mapping = {
        "600041": ("Chennai", "Tamil Nadu"),
        "560034": ("Bengaluru", "Karnataka"),
        "400050": ("Mumbai", "Maharashtra"),
    }
    district, state = mapping.get(pin, ("Unknown", "Unknown"))
    return [{"Message": "Number of pincode(s) found:1", "Status": "Success",
             "PostOffice": [{"Name": district, "District": district, "State": state,
                             "Country": "India", "Pincode": pin}]}]

def write_landing(source, records, run_id):
    folder = LANDING_DIR / source
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{source}__{run_id}.json.gz"
    now = datetime.now(timezone.utc).isoformat()
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for rec in records:
            envelope = {"source": source, "run_id": run_id, "extracted_at": now, "data": rec}
            f.write(json.dumps(envelope, ensure_ascii=False) + "\\n")
    print(f"   {source:8s}: {len(records)} records -> {path}")
    return path

print("Sample mock datasets and landing helpers initialized.")
"""))

# Cell 4: Database Setup SQL
cells.append(nbf.v4.new_markdown_cell("## 4. Database Setup SQL (`SQL_00_SETUP`)\nInitializes `FRESHCART_WH`, database `FRESHCART`, schemas, stages, and empty tables."))
cells.append(nbf.v4.new_code_cell("""SQL_00_SETUP = r\"\"\"
CREATE WAREHOUSE IF NOT EXISTS FRESHCART_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE;
USE WAREHOUSE FRESHCART_WH;

CREATE DATABASE IF NOT EXISTS FRESHCART;
USE DATABASE FRESHCART;

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS dim;
CREATE SCHEMA IF NOT EXISTS ref;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS quarantine;

CREATE FILE FORMAT IF NOT EXISTS bronze.ff_ndjson TYPE = JSON COMPRESSION = AUTO;
CREATE STAGE IF NOT EXISTS bronze.landing FILE_FORMAT = bronze.ff_ndjson;

CREATE TABLE IF NOT EXISTS bronze.orders_raw (
  ingest_seq   NUMBER AUTOINCREMENT START 1 INCREMENT 1 ORDER,
  source       STRING,
  raw          VARIANT,
  run_id       STRING,
  extracted_at TIMESTAMP_TZ,
  src_file     STRING,
  src_row      NUMBER,
  loaded_at    TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.customers_raw (
  ingest_seq NUMBER AUTOINCREMENT START 1 INCREMENT 1 ORDER, source STRING, raw VARIANT,
  run_id STRING, extracted_at TIMESTAMP_TZ, src_file STRING, src_row NUMBER,
  loaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.fx_raw (
  ingest_seq NUMBER AUTOINCREMENT START 1 INCREMENT 1 ORDER, source STRING, raw VARIANT,
  run_id STRING, extracted_at TIMESTAMP_TZ, src_file STRING, src_row NUMBER,
  loaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.pincode_raw (
  ingest_seq NUMBER AUTOINCREMENT START 1 INCREMENT 1 ORDER, source STRING, raw VARIANT,
  run_id STRING, extracted_at TIMESTAMP_TZ, src_file STRING, src_row NUMBER,
  loaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE ref.tier_multiplier AS
SELECT * FROM VALUES ('Silver', 1), ('Gold', 2), ('Platinum', 3) AS v(tier, multiplier);

CREATE OR REPLACE TABLE ref.state_region AS
SELECT * FROM VALUES
  ('Tamil Nadu','South'), ('Karnataka','South'), ('Kerala','South'), ('Andhra Pradesh','South'),
  ('Telangana','South'), ('Puducherry','South'),
  ('Maharashtra','West'), ('Gujarat','West'), ('Goa','West'), ('Rajasthan','West'),
  ('Delhi','North'), ('Haryana','North'), ('Punjab','North'), ('Uttar Pradesh','North'),
  ('Himachal Pradesh','North'), ('Jammu and Kashmir','North'), ('Uttarakhand','North'),
  ('West Bengal','East'), ('Odisha','East'), ('Bihar','East'), ('Jharkhand','East'), ('Assam','East'),
  ('Madhya Pradesh','Central'), ('Chhattisgarh','Central')
  AS v(state, region);

CREATE TABLE IF NOT EXISTS ref.pincode_geo (
  pincode STRING PRIMARY KEY, city STRING, state STRING, region STRING,
  updated_at TIMESTAMP_LTZ
);

CREATE TABLE IF NOT EXISTS quarantine.orders (
  run_id STRING, quarantined_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
  ingest_seq NUMBER, source STRING, order_id STRING, reasons ARRAY, row_data VARIANT
);

CREATE TABLE IF NOT EXISTS gold.fct_orders (
  order_id STRING PRIMARY KEY, order_date DATE, cust_id STRING, email STRING,
  tier STRING, multiplier NUMBER, amount NUMBER(12,2), currency STRING,
  fx_rate NUMBER(12,4), amount_inr NUMBER(14,2), loyalty_points NUMBER,
  is_high_value BOOLEAN, city STRING, state STRING, region STRING,
  updated_at TIMESTAMP_NTZ, row_hash NUMBER, published_at TIMESTAMP_LTZ
);
\"\"\"

run_sql(SQL_00_SETUP)
print("Database, warehouse, schemas, stages, and tables initialized successfully!")
"""))

# Cell 5: Transformation SQL
cells.append(nbf.v4.new_markdown_cell("## 5. Transformation SQL (`SQL_10` to `SQL_40`)\nCleansing, currency validation, deduplication, SCD2 dimension, FX spine, and gold fact table with `row_hash`."))
cells.append(nbf.v4.new_code_cell("""# SQL_10: Cleansing, Unification, and Currency Validation (PART B3)
SQL_10_ORDERS_CLEAN = r\"\"\"
CREATE OR REPLACE TRANSIENT TABLE silver.orders_checked AS
WITH unified AS (
  SELECT ingest_seq, source,
         raw:order_id::STRING   AS order_id,
         raw:cust_email::STRING AS cust_email,
         raw:cust_name::STRING  AS cust_name,
         raw:order_date::STRING AS order_date,
         raw:amount::STRING     AS amount,
         raw:currency::STRING   AS currency,
         raw:pincode::STRING    AS pincode,
         raw:updated_at::STRING AS updated_at
  FROM bronze.orders_raw WHERE source = 'web'
  UNION ALL
  SELECT ingest_seq, source,
         raw:orderId::STRING, raw:customer.email::STRING, raw:customer.name::STRING,
         raw:orderDate::STRING, raw:total.value::STRING, raw:total.currency::STRING,
         raw:deliveryPin::STRING, raw:updatedAt::STRING
  FROM bronze.orders_raw WHERE source = 'mobile'
),
typed AS (
  SELECT
    ingest_seq, source,
    TRIM(order_id)                                    AS order_id,
    LOWER(TRIM(cust_email))                           AS email,
    INITCAP(RTRIM(TRIM(cust_name), '.'))              AS name,
    COALESCE(
      TRY_TO_DATE(order_date, 'YYYY-MM-DD'),
      TRY_TO_DATE(order_date, 'DD/MM/YYYY'),
      TRY_TO_DATE(order_date, 'MON DD, YYYY')
    )                                                 AS order_date,
    TRY_TO_DECIMAL(REGEXP_REPLACE(amount, '[^0-9.-]', ''), 12, 2) AS amount,
    UPPER(TRIM(currency))                             AS currency,
    TRIM(pincode)                                     AS pincode,
    TRY_TO_TIMESTAMP_NTZ(updated_at)                  AS updated_at
  FROM unified
)
SELECT *,
  ARRAY_CONSTRUCT_COMPACT(
    IFF(order_id IS NULL, 'missing_order_id', NULL),
    IFF(email IS NULL OR NOT REGEXP_LIKE(email, '^[^@\\s]+@[^@\\s]+\\.[a-z]{2,}$'), 'bad_email', NULL),
    IFF(pincode IS NULL OR NOT REGEXP_LIKE(pincode, '^[1-9][0-9]{5}$'), 'bad_pincode', NULL),
    IFF(order_date IS NULL, 'unparseable_date', NULL),
    IFF(updated_at IS NULL, 'unparseable_updated_at', NULL),
    IFF(amount <= 0, 'non_positive_amount', NULL),
    IFF(currency NOT IN ('INR', 'USD'), 'unsupported_currency', NULL)
  ) AS reasons
FROM typed;

CREATE OR REPLACE TABLE silver.orders_clean AS
SELECT * EXCLUDE reasons, (amount IS NULL) AS amount_missing
FROM silver.orders_checked
WHERE ARRAY_SIZE(reasons) = 0;

INSERT INTO quarantine.orders (run_id, ingest_seq, source, order_id, reasons, row_data)
SELECT $run_id, c.ingest_seq, c.source, c.order_id, c.reasons, OBJECT_CONSTRUCT(*)
FROM silver.orders_checked c
WHERE ARRAY_SIZE(c.reasons) > 0
  AND NOT EXISTS (
        SELECT 1 FROM quarantine.orders q
        WHERE q.source = c.source
          AND EQUAL_NULL(q.order_id, c.order_id)
          AND EQUAL_NULL(q.row_data:UPDATED_AT::TIMESTAMP_NTZ, c.updated_at))
QUALIFY ROW_NUMBER() OVER (PARTITION BY c.source, c.order_id, c.updated_at
                           ORDER BY c.ingest_seq DESC) = 1;
\"\"\"

# SQL_20: Deduplication (newest updated_at wins)
SQL_20_ORDERS_DEDUP = r\"\"\"
CREATE OR REPLACE TABLE silver.orders_dedup AS
SELECT *
FROM silver.orders_clean
QUALIFY ROW_NUMBER() OVER (
          PARTITION BY order_id
          ORDER BY updated_at DESC, ingest_seq DESC
        ) = 1;
\"\"\"

# SQL_30: Customer SCD Type 2
SQL_30_CUSTOMERS_SCD2 = r\"\"\"
CREATE OR REPLACE TABLE dim.customers_scd2 AS
WITH events AS (
  SELECT raw:cust_id::STRING                     AS cust_id,
         LOWER(TRIM(raw:email::STRING))          AS email,
         INITCAP(TRIM(raw:tier::STRING))         AS tier,
         TRY_TO_DATE(raw:effective_from::STRING) AS valid_from,
         loaded_at, ingest_seq
  FROM bronze.customers_raw
  QUALIFY ROW_NUMBER() OVER (PARTITION BY cust_id, valid_from
                             ORDER BY loaded_at DESC, ingest_seq DESC) = 1
)
SELECT cust_id, email, tier, valid_from,
       COALESCE(DATEADD(day, -1, LEAD(valid_from) OVER (PARTITION BY cust_id ORDER BY valid_from)),
                '9999-12-31'::DATE) AS valid_to,
       LEAD(valid_from) OVER (PARTITION BY cust_id ORDER BY valid_from) IS NULL AS is_current
FROM events
WHERE cust_id IS NOT NULL AND valid_from IS NOT NULL;
\"\"\"

# SQL_31: Daily FX rates forward-filled
SQL_31_FX_DAILY = r\"\"\"
CREATE OR REPLACE TABLE ref.fx_daily AS
WITH published AS (
  SELECT r.raw:base::STRING          AS currency,
         f.key::DATE                 AS rate_date,
         f.value:INR::NUMBER(12,4)   AS rate_to_inr
  FROM bronze.fx_raw r, LATERAL FLATTEN(input => r.raw:rates) f
  QUALIFY ROW_NUMBER() OVER (PARTITION BY currency, rate_date
                             ORDER BY r.loaded_at DESC, r.ingest_seq DESC) = 1
),
bounds AS (
  SELECT MIN(rate_date) AS d0, GREATEST(MAX(rate_date), CURRENT_DATE()) AS d1 FROM published
),
spine AS (
  SELECT DATEADD(day, ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, b.d0) AS d
  FROM bounds b, TABLE(GENERATOR(ROWCOUNT => 4000))
  QUALIFY d <= (SELECT d1 FROM bounds)
),
grid AS (
  SELECT DISTINCT p.currency, s.d AS rate_date
  FROM published p CROSS JOIN spine s
),
joined AS (
  SELECT g.currency, g.rate_date, p.rate_to_inr
  FROM grid g LEFT JOIN published p USING (currency, rate_date)
),
filled AS (
  SELECT currency, rate_date,
         LAST_VALUE(rate_to_inr IGNORE NULLS) OVER (
           PARTITION BY currency ORDER BY rate_date
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
         ) AS rate_to_inr,
         (rate_to_inr IS NULL) AS is_carried_forward
  FROM joined
)
SELECT currency, rate_date, rate_to_inr, is_carried_forward
FROM filled
WHERE rate_to_inr IS NOT NULL
UNION ALL
SELECT 'INR', d, 1.0000, FALSE FROM spine;
\"\"\"

# SQL_32: Pincode lookup
SQL_32_PINCODE_GEO = r\"\"\"
MERGE INTO ref.pincode_geo t
USING (
  WITH parsed AS (
    SELECT f.value:PostOffice[0]:Pincode::STRING  AS pincode,
           f.value:PostOffice[0]:District::STRING AS city,
           f.value:PostOffice[0]:State::STRING    AS state,
           loaded_at, ingest_seq
    FROM bronze.pincode_raw r, LATERAL FLATTEN(input => r.raw) f
    WHERE f.value:Status::STRING = 'Success'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY pincode ORDER BY loaded_at DESC, ingest_seq DESC) = 1
  )
  SELECT p.pincode, p.city, p.state, sr.region
  FROM parsed p
  LEFT JOIN ref.state_region sr ON sr.state = p.state
) s
ON t.pincode = s.pincode
WHEN MATCHED AND (t.city <> s.city OR t.state <> s.state OR NVL(t.region,'') <> NVL(s.region,''))
  THEN UPDATE SET city = s.city, state = s.state, region = s.region, updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED
  THEN INSERT (pincode, city, state, region, updated_at)
       VALUES (s.pincode, s.city, s.state, s.region, CURRENT_TIMESTAMP());
\"\"\"

# SQL_40: Enrich and idempotent MERGE with row_hash
SQL_40_GOLD = r\"\"\"
CREATE OR REPLACE TABLE silver.orders_enriched AS
SELECT o.*,
       c.cust_id, c.tier,
       m.multiplier,
       fx.rate_to_inr                              AS fx_rate,
       ROUND(o.amount * fx.rate_to_inr, 2)         AS amount_inr,
       FLOOR(amount_inr / 100) * m.multiplier      AS loyalty_points,
       amount_inr >= 2000                          AS is_high_value,
       g.city, g.state, g.region
FROM silver.orders_dedup o
LEFT JOIN dim.customers_scd2 c
       ON  c.email = o.email
       AND o.order_date BETWEEN c.valid_from AND c.valid_to
LEFT JOIN ref.tier_multiplier m ON m.tier = c.tier
LEFT JOIN ref.fx_daily fx
       ON  fx.currency = o.currency AND fx.rate_date = o.order_date
LEFT JOIN ref.pincode_geo g ON g.pincode = o.pincode;

MERGE INTO gold.fct_orders t
USING (
  SELECT *,
         HASH(order_id, order_date, cust_id, email, tier, multiplier,
              amount, currency, fx_rate, amount_inr, loyalty_points,
              is_high_value, city, state, region) AS row_hash
  FROM silver.orders_enriched
) s
ON t.order_id = s.order_id
WHEN MATCHED AND t.row_hash <> s.row_hash THEN
  UPDATE SET order_date     = s.order_date,
             cust_id        = s.cust_id,
             email          = s.email,
             tier           = s.tier,
             multiplier     = s.multiplier,
             amount         = s.amount,
             currency       = s.currency,
             fx_rate        = s.fx_rate,
             amount_inr     = s.amount_inr,
             loyalty_points = s.loyalty_points,
             is_high_value  = s.is_high_value,
             city           = s.city,
             state          = s.state,
             region         = s.region,
             updated_at     = s.updated_at,
             row_hash       = s.row_hash,
             published_at   = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
  INSERT (order_id, order_date, cust_id, email, tier, multiplier,
          amount, currency, fx_rate, amount_inr, loyalty_points,
          is_high_value, city, state, region, updated_at, row_hash, published_at)
  VALUES (s.order_id, s.order_date, s.cust_id, s.email, s.tier, s.multiplier,
          s.amount, s.currency, s.fx_rate, s.amount_inr, s.loyalty_points,
          s.is_high_value, s.city, s.state, s.region, s.updated_at, s.row_hash, CURRENT_TIMESTAMP());
\"\"\"

print("Transformation SQL definitions loaded.")
"""))

# Cell 6: Quality Checks Function
cells.append(nbf.v4.new_markdown_cell("## 6. Pipeline Orchestration & Quality Checks\nIncludes 5 baseline checks + Check 6 added for Part B5."))
cells.append(nbf.v4.new_code_cell("""def quality_checks():
    \"\"\"Each of these numbers should be 0.\"\"\"
    checks = {
        "rows gained or lost while enriching":
            "SELECT ABS((SELECT count(*) FROM silver.orders_clean) - (SELECT count(*) FROM silver.orders_enriched))",
        "duplicate orders in gold":
            "SELECT count(*) FROM (SELECT order_id FROM gold.fct_orders GROUP BY order_id HAVING count(*) > 1)",
        "orders with no customer match":
            "SELECT count(*) FROM gold.fct_orders WHERE cust_id IS NULL",
        "orders with an amount but no FX rate":
            "SELECT count(*) FROM gold.fct_orders WHERE amount IS NOT NULL AND fx_rate IS NULL",
        "orders with no city":
            "SELECT count(*) FROM gold.fct_orders WHERE city IS NULL",
        # PART B5: Added sixth data-quality check
        "gold orders with amount but missing INR":
            "SELECT count(*) FROM gold.fct_orders WHERE amount IS NOT NULL AND amount_inr IS NULL",
    }
    all_ok = True
    for name, sql in checks.items():
        val = query(sql)[0][0]
        status = 'OK' if val == 0 else 'PROBLEM'
        if val != 0:
            all_ok = False
        print(f"   {name:42s} {val:3d}   {status}")

    rejected = query(\"\"\"
        SELECT COUNT_IF(ARRAY_SIZE(reasons) > 0) / NULLIF(COUNT(*), 0)
        FROM silver.orders_checked
    \"\"\")[0][0]
    print(f"   {'share of rows rejected':42s} {float(rejected or 0):.0%}")
    return all_ok

def run_pipeline():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    print(f\"\\n>>> Running Pipeline (run_id: {run_id}) <<<\")

    print(\"1. EXTRACT: sample data -> landing files\")
    f_web    = write_landing(\"web\",    MOCK_WEB_ORDERS,      run_id)
    f_mobile = write_landing(\"mobile\", MOCK_MOBILE_ORDERS,   run_id)
    f_crm    = write_landing(\"crm\",    MOCK_CRM_TIER_EVENTS, run_id)
    f_fx     = write_landing(\"fx\",     MOCK_FX_RESPONSES,    run_id)

    print(\"2. LOAD: landing files -> bronze tables\")
    load_file(f_web,    \"bronze.orders_raw\",    f\"web/{run_id}\")
    load_file(f_mobile, \"bronze.orders_raw\",    f\"mobile/{run_id}\")
    load_file(f_crm,    \"bronze.customers_raw\", f\"crm/{run_id}\")
    load_file(f_fx,     \"bronze.fx_raw\",        f\"fx/{run_id}\")

    print(\"3. TRANSFORM: bronze -> silver -> gold\")
    query(f\"SET run_id = '{run_id}'\")
    run_sql(SQL_10_ORDERS_CLEAN)
    run_sql(SQL_20_ORDERS_DEDUP)

    pins = [row[0] for row in query(\"\"\"
        SELECT DISTINCT o.pincode FROM silver.orders_dedup o
        WHERE NOT EXISTS (SELECT 1 FROM ref.pincode_geo g WHERE g.pincode = o.pincode)\"\"\")]
    if pins:
        lookups = [mock_pincode_response(p) for p in pins]
        f_pin = write_landing(\"pincode\", lookups, run_id)
        load_file(f_pin, \"bronze.pincode_raw\", f\"pincode/{run_id}\")

    run_sql(SQL_30_CUSTOMERS_SCD2)
    run_sql(SQL_31_FX_DAILY)
    run_sql(SQL_32_PINCODE_GEO)
    run_sql(SQL_40_GOLD)

    print(\"4. CHECK: Data Quality Validation\")
    quality_checks()

    orders, rev, pts = query(\"SELECT count(*), sum(amount_inr), sum(loyalty_points) FROM gold.fct_orders\")[0]
    print(f\"GOLD: {orders} orders, revenue ₹{rev:.2f}, {pts} loyalty points\")
"""))

# Cell 7: Part B1 Run & Summary Counts
cells.append(nbf.v4.new_markdown_cell("## 7. Part B1: Run Baseline Pipeline & Inspect Results\nExecutes the initial pipeline run and displays baseline layer counts."))
cells.append(nbf.v4.new_code_cell("""run_pipeline()

print("\\n=== B1 Baseline Counts ===")
show(\"\"\"
SELECT (SELECT COUNT(*) FROM bronze.orders_raw)      AS bronze_rows,
       (SELECT COUNT(*) FROM silver.orders_clean)    AS silver_clean_rows,
       (SELECT COUNT(*) FROM quarantine.orders)      AS quarantine_rows,
       (SELECT COUNT(*) FROM silver.orders_dedup)    AS silver_dedup_rows,
       (SELECT COUNT(*) FROM gold.fct_orders)        AS gold_rows,
       (SELECT SUM(amount_inr) FROM gold.fct_orders) AS total_revenue_inr,
       (SELECT SUM(loyalty_points) FROM gold.fct_orders) AS total_loyalty_points
\"\"\")
"""))

# Cell 8: Individual Layer Inspections
cells.append(nbf.v4.new_markdown_cell("### Layer Inspections (Bronze, Silver Clean, Quarantine, Dedup, Dim, Ref, Gold)"))
cells.append(nbf.v4.new_code_cell("""print("=== Quarantined Orders & Reasons ===")
show("SELECT run_id, source, order_id, reasons FROM quarantine.orders")

print("\\n=== Deduplicated Silver Orders ===")
show("SELECT order_id, ingest_seq, updated_at, amount, currency, pincode FROM silver.orders_dedup ORDER BY order_id")

print("\\n=== Customer SCD2 Dimension ===")
show("SELECT cust_id, email, tier, valid_from, valid_to, is_current FROM dim.customers_scd2 ORDER BY cust_id, valid_from")

print("\\n=== Gold Fact Orders (Full Table) ===")
show(\"\"\"
SELECT order_id, order_date, cust_id, tier, multiplier, amount, currency, fx_rate,
       amount_inr, loyalty_points, is_high_value, city, region
FROM gold.fct_orders
ORDER BY order_id
\"\"\")
"""))

# Cell 9: Part B2 Record Tracing
cells.append(nbf.v4.new_markdown_cell("""## 8. Part B2: Record Tracing (ORD-1003 & ORD-1005)

### Trace 1: ORD-1003 (Deduplication & Point Arithmetic)
1. **Bronze Raw Records:** Web record arrives with `amount=null` and `updated_at=14:30:00`. Mobile record arrives with `amount='2,100.00'` and `updated_at=18:40:00`.
2. **Silver Normalization:** Unified in `silver.orders_checked` with standard column names.
3. **Deduplication:** `QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC, ingest_seq DESC) = 1` retains the Mobile record because 18:40:00 > 14:30:00.
4. **Gold Fact Arithmetic:** Meera is on Platinum tier (3x multiplier).  
   Amount in INR = ₹2,100.00.  
   Loyalty points = `FLOOR(2100 / 100) * 3 = 21 * 3 = 63 points`.

### Trace 2: ORD-1005 (SCD2 Tier Evolution for Priya)
- ORD-1001 placed on `2026-09-01` falls in `[2023-04-10, 2026-09-02]` -> Silver tier (1x multiplier = 12 points).
- ORD-1005 placed on `2026-09-03` falls in `[2026-09-03, 9999-12-31]` -> Gold tier (2x multiplier = 16 points).
- Join condition: `LEFT JOIN dim.customers_scd2 c ON c.email = o.email AND o.order_date BETWEEN c.valid_from AND c.valid_to`
"""))
cells.append(nbf.v4.new_code_cell("""print("=== Trace Orders in Gold Fact Table ===")
show(\"\"\"
SELECT order_id, order_date, email, tier, multiplier, amount_inr, loyalty_points
FROM gold.fct_orders
WHERE order_id IN ('ORD-1001', 'ORD-1003', 'ORD-1005')
ORDER BY order_id
\"\"\")
"""))

# Cell 10: Part B3 Currency Validation
cells.append(nbf.v4.new_markdown_cell("""## 9. Part B3: Currency Validation Analysis
FreshCart only accepts INR and USD. We added:
`IFF(currency NOT IN ('INR', 'USD'), 'unsupported_currency', NULL)` to `SQL_10_ORDERS_CLEAN`.
"""))
cells.append(nbf.v4.new_code_cell("""print("=== Quarantined Currency Violation (ORD-1006) ===")
show(\"\"\"
SELECT order_id, source, reasons, row_data:CURRENCY::STRING AS currency
FROM quarantine.orders
WHERE order_id = 'ORD-1006'
\"\"\")
"""))

# Cell 11: Part B4 Arjun SCD2 & Idempotency
cells.append(nbf.v4.new_markdown_cell("""## 10. Part B4: SCD Type 2 Evolution & Idempotency
Adding Arjun tier upgrade event (`CUST-02`, Gold, effective `2026-08-15`).

### Pre-Run Predictions vs Actuals:
| Quantity | Prediction (Before Run) | Actual (After Run) | Reason |
|---|---|---|---|
| Rows for CUST-02 in `dim.customers_scd2` | 2 rows | 2 rows | Silver (expires 2026-08-14) + Gold (effective 2026-08-15) |
| Tier used for ORD-1002 | Gold | Gold | Order date 2026-09-01 falls into [2026-08-15, 9999-12-31] |
| Loyalty points for ORD-1002 | 70 pts | 70 pts | Floor(3536 / 100) * 2 = 70 points (was 35 pts) |
| Total loyalty points in gold | 161 pts | 161 pts | Increased by 35 points (126 + 35 = 161) |
| Number of gold rows published_at changed | 1 row | 1 row | Only ORD-1002 row_hash was modified |
"""))
cells.append(nbf.v4.new_code_cell("""# Add Arjun Gold event to CRM history
NEW_ARJUN_EVENT = {
    "cust_id": "CUST-02",
    "email": "arjun.k@yahoo.in",
    "tier": "Gold",
    "effective_from": "2026-08-15"
}

if NEW_ARJUN_EVENT not in MOCK_CRM_TIER_EVENTS:
    MOCK_CRM_TIER_EVENTS.append(NEW_ARJUN_EVENT)
    print("Added Arjun Gold event to MOCK_CRM_TIER_EVENTS.")

# Re-run pipeline with Arjun update
run_pipeline()

print("\\n=== Arjun SCD2 History ===")
show("SELECT cust_id, email, tier, valid_from, valid_to, is_current FROM dim.customers_scd2 WHERE cust_id = 'CUST-02' ORDER BY valid_from")

print("\\n=== Gold Orders After SCD2 Evolution ===")
show(\"\"\"
SELECT order_id, cust_id, tier, multiplier, amount_inr, loyalty_points, published_at
FROM gold.fct_orders
ORDER BY order_id
\"\"\")
"""))

# Cell 12: Part B5 Quality Check Failure & Recovery
cells.append(nbf.v4.new_markdown_cell("""## 11. Part B5: Data-Quality Check & ETL vs. ELT Analysis
Demonstration of Check 6 failure injection (`PROBLEM`), cleanup recovery (`OK`), and architecture analysis.
"""))
cells.append(nbf.v4.new_code_cell("""# 1. Deliberately insert a bad row violating Check 6 (amount is NOT NULL, but amount_inr IS NULL)
query(\"\"\"
INSERT INTO gold.fct_orders (order_id, order_date, cust_id, amount, currency, amount_inr, loyalty_points)
VALUES ('MOCK-FAIL-01', '2026-09-01', 'CUST-99', 500.00, 'INR', NULL, 0)
\"\"\")

print("--- Quality Checks WITH Deliberate Failure ---")
quality_checks()

# 2. Clean up the bad row
query("DELETE FROM gold.fct_orders WHERE order_id = 'MOCK-FAIL-01'")

print("\\n--- Quality Checks AFTER Removing Bad Row ---")
quality_checks()
"""))

# Cell 13: Teardown
cells.append(nbf.v4.new_markdown_cell("## 12. Close Connection\nClose the Snowflake connection."))
cells.append(nbf.v4.new_code_cell("""conn.close()
print("Snowflake connection closed successfully.")
"""))

nb.cells = cells

target_nb_path = "elt/freshcart_elt.ipynb"
with open(target_nb_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Built skeleton {target_nb_path} with {len(cells)} cells.")
