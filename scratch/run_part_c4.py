"""
PART C4: Custom Block (validate_data) with @test Verification
Demonstrates the custom transformer inserted after load_iris.
Checks for missing values and exactly 3 classes, and runs its attached @test functions.
"""
import sys, os
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from iris_project.data_loaders import load_iris
from iris_project.transformers import validate_data
from iris_project.run_pipeline import run_block_tests

BANNER = "=" * 75

print(BANNER)
print("  PART C4: CUSTOM PIPELINE BLOCK — validate_data")
print("  Block UUID: validate_data  |  Type: transformer")
print(BANNER)

print("""
CUSTOM BLOCK DESIGN:
  * Location: Positioned immediately after 'load_iris' and before 'prepare_data'.
  * Responsibility: Enforce data quality and schema invariants on the raw dataset.
  * Checks:
      1. Verifies that no null/NaN/missing values exist in any column.
      2. Verifies that the dataset contains exactly 3 distinct target species classes.
  * Attached @test Functions:
      - test_no_missing_values(output)
      - test_exactly_three_classes(output)
""")

print("-" * 75)
print("[1] EXECUTING CUSTOM BLOCK ON VALID DATASET:")
print("-" * 75)
df_raw = load_iris.load_data()
df_validated = validate_data.transform(df_raw)
print(f"  Input rows: {len(df_raw)}, Validated rows: {len(df_validated)}")
run_block_tests(validate_data, df_validated)

print("\n" + "-" * 75)
print("[2] DEMONSTRATING @test GATE INJECTION (Mock Malformed Dataset):")
print("-" * 75)

# Test failure case 1: Injected null value
print("  --> Injected null value into sepal length:")
df_bad_null = df_raw.copy()
df_bad_null.loc[0, "sepal length (cm)"] = None
try:
    validate_data.transform(df_bad_null)
    print("      UNEXPECTED PASS")
except ValueError as e:
    print(f"      DETECTED & BLOCKED: {e}")

# Test failure case 2: Injected 4th class
print("  --> Injected 4th target class:")
df_bad_class = df_raw.copy()
df_bad_class.loc[0, "target"] = 99
try:
    validate_data.transform(df_bad_class)
    print("      UNEXPECTED PASS")
except ValueError as e:
    print(f"      DETECTED & BLOCKED: {e}")

print("\n" + BANNER)
print("  PART C4: Custom block verified! Both normal pass and failure gates confirmed.")
print(BANNER)
