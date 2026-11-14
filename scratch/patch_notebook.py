"""
Patch freshcart_elt.ipynb:
  1. Insert 9 layer-inspection cell pairs (markdown + code) after cell index 18
     (the existing "Inspect Individual Pipeline Layers" markdown).
  2. Insert idempotency cell pair after B4 code cell (cell 24 original → shifted later).
"""
import json, copy, sys

NB_PATH = "elt/freshcart_elt.ipynb"

def md(source_lines):
    return {"cell_type": "markdown", "metadata": {}, "source": source_lines}

def code(source_lines):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source_lines}

# ---------------------------------------------------------------------------
# 9 Layer-inspection pairs (markdown + code) to insert after cell index 18
# (which is "### Inspect Individual Pipeline Layers")
# ---------------------------------------------------------------------------
layer_cells = [
    # B1 Bronze
    md(["### B1: Bronze Layer - Raw JSON\n"]),
    code([
        "print('--- B1: Bronze Layer (raw ingested records) ---')\n",
        "show('SELECT ingest_seq, source, raw FROM bronze.orders_raw ORDER BY ingest_seq LIMIT 20')\n"
    ]),
    # B1 Silver Clean
    md(["### B1: Silver Clean Layer\n"]),
    code([
        "print('--- B1: Silver Clean Orders (6 rows passed validation) ---')\n",
        "show('SELECT ingest_seq, source, order_id, email, name, order_date, amount, currency, pincode FROM silver.orders_clean ORDER BY ingest_seq')\n"
    ]),
    # B1 Quarantine
    md(["### B1: Quarantine Layer\n"]),
    code([
        "print('--- B1: Quarantine Orders (failed validation) ---')\n",
        "show('SELECT run_id, source, order_id, reasons FROM quarantine.orders')\n"
    ]),
    # B1 Silver Dedup
    md(["### B1: Silver Deduplicated Layer\n"]),
    code([
        "print('--- B1: Silver Dedup (one row per order_id) ---')\n",
        "show('SELECT order_id, ingest_seq, updated_at, amount FROM silver.orders_dedup ORDER BY order_id')\n"
    ]),
    # B1 SCD2 Dim
    md(["### B1: Customer SCD2 Dimension\n"]),
    code([
        "print('--- B1: Customer SCD2 Dimension ---')\n",
        "show('SELECT * FROM dim.customers_scd2 ORDER BY cust_id, valid_from')\n"
    ]),
    # B1 FX Daily
    md(["### B1: FX Daily Rates (REF)\n"]),
    code([
        "print('--- B1: FX Daily Rates (USD->INR spine, forward filled) ---')\n",
        "show(\"SELECT * FROM ref.fx_daily WHERE currency = 'USD' ORDER BY rate_date LIMIT 10\")\n"
    ]),
    # B1 Pincode Geo
    md(["### B1: Pincode Geography (REF)\n"]),
    code([
        "print('--- B1: Pincode Geography ---')\n",
        "show('SELECT * FROM ref.pincode_geo')\n"
    ]),
    # B1 Gold Fact Orders
    md(["### B1: Gold Fact Orders\n"]),
    code([
        "print('--- B1: Gold Fact Orders (final enriched orders) ---')\n",
        "show('SELECT order_id, order_date, tier, amount, currency, fx_rate, amount_inr, loyalty_points, is_high_value, city, region FROM gold.fct_orders ORDER BY order_id')\n"
    ]),
    # B1 Gold Totals
    md(["### B1: Gold Totals\n"]),
    code([
        "print('--- B1: Gold Summary Totals ---')\n",
        "show('SELECT COUNT(*) AS orders, SUM(amount_inr) AS revenue_inr, SUM(loyalty_points) AS points FROM gold.fct_orders')\n"
    ]),
]

# ---------------------------------------------------------------------------
# Idempotency cells to insert after B4 code cell
# ---------------------------------------------------------------------------
idempotency_cells = [
    md([
        "## B4 Continued: Idempotency - Run Pipeline Again\n",
        "Bronze grows by 8 rows on every run. Quarantine and Gold stay the same.\n"
    ]),
    code([
        "print('--- Running pipeline again to demonstrate idempotency ---')\n",
        "run_pipeline()\n",
        "\n",
        "show('''\n",
        "SELECT (SELECT COUNT(*) FROM bronze.orders_raw)  AS bronze_rows,\n",
        "       (SELECT COUNT(*) FROM quarantine.orders)  AS quarantine_rows,\n",
        "       (SELECT COUNT(*) FROM gold.fct_orders)    AS gold_orders,\n",
        "       (SELECT SUM(amount_inr) FROM gold.fct_orders)     AS revenue_inr,\n",
        "       (SELECT SUM(loyalty_points) FROM gold.fct_orders) AS points\n",
        "''')\n"
    ]),
]

# ---------------------------------------------------------------------------
# Load, patch, save
# ---------------------------------------------------------------------------
with open(NB_PATH, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]
print(f"Original cell count: {len(cells)}")

# Step 1: Insert layer inspection cells after index 18
# (cell 18 = existing "Inspect Individual Pipeline Layers" md)
# We REPLACE cell 18 (existing md) + cell 19 (existing lumped code) with:
#   cell 18 (existing md) + 18 new layer cells (keeping original lumped code too? No.)
# Actually the instructions say we keep the existing cells but ADD the layer cells.
# The existing cell 18 (md) says "Inspect Individual Pipeline Layers"
# and cell 19 (code) lumps quarantine+dedup+gold together.
# We KEEP cell 18 (md). Then insert the 18 new layer cells right after cell 18.
# Cell 19 onwards shift right.

insert_after = 18  # after "Inspect Individual Pipeline Layers" markdown
cells = cells[:insert_after+1] + layer_cells + cells[insert_after+1:]
print(f"After layer injection: {len(cells)} cells")

# Step 2: Find the B4 code cell (original index 24, now shifted by len(layer_cells))
# B4 code cell originally at index 24. After inserting 18 cells after index 18:
# new index = 24 + 18 = 42
b4_original_idx = 24
b4_new_idx = b4_original_idx + len(layer_cells)
print(f"B4 code cell now at index: {b4_new_idx}")

# Insert idempotency cells right after B4 code cell
cells = cells[:b4_new_idx+1] + idempotency_cells + cells[b4_new_idx+1:]
print(f"After idempotency injection: {len(cells)} cells")

nb["cells"] = cells

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)

print("Notebook patched and saved successfully!")

# Verify JSON is valid by re-reading
with open(NB_PATH, encoding="utf-8") as f:
    nb2 = json.load(f)
print(f"Notebook JSON valid. Total cells: {len(nb2['cells'])}")
print("Cell index -> type (source preview):")
for i, c in enumerate(nb2["cells"]):
    src_preview = repr("".join(c["source"])[:55])
    print(f"  [{i:02d}] {c['cell_type']:8s} {src_preview}")
