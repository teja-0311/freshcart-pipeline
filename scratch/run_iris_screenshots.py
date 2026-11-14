"""
Part C Screenshot Runner - Iris ML Pipeline
Run this script and take screenshots of the two clearly labelled sections.
"""
import sys, os, subprocess
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BANNER = "=" * 70

def banner(title):
    print(f"\n{BANNER}")
    print(f"  {title}")
    print(f"{BANNER}\n")

# ── Run 1: max_depth = 1  (gate MUST FAIL) ──────────────────────────────────
banner("SCREENSHOT C1 — Run with max_depth=1  >>>  @test gate FAILS (accuracy 66.7% < 90%)")

result1 = subprocess.run(
    [sys.executable, "iris_project/run_pipeline.py", "--max-depth", "1"]
)

print(f"\n>>> Exit code: {result1.returncode}  (1 = test gate blocked pipeline — expected)")

# ── Run 2: max_depth = 3  (gate MUST PASS + evaluation branch runs) ─────────
banner("SCREENSHOT C2 — Run with max_depth=3  >>>  @test gate PASSES (accuracy 96.7% >= 90%)")

result2 = subprocess.run(
    [sys.executable, "iris_project/run_pipeline.py", "--max-depth", "3"]
)

print(f"\n>>> Exit code: {result2.returncode}  (0 = pipeline completed successfully — expected)")

# ── Summary ──────────────────────────────────────────────────────────────────
banner("SCREENSHOT GUIDE FOR PART C")
print("Take 2 screenshots from the output above:")
print()
print("  C1 → Scroll up to 'SCREENSHOT C1' section:")
print("       Capture Block 4 showing:  'test_accuracy... FAILED'")
print("       and the line:  '[PIPELINE BLOCKED BY TEST GATE]'")
print()
print("  C2 → Scroll to 'SCREENSHOT C2' section:")
print("       Capture Block 4: 'test_accuracy... PASSED'")
print("       Block 5: 'Saved 30 predictions to iris_predictions.csv'")
print("       Block 6: Confusion Matrix table + Metrics Table")
print("       Final: 'Pipeline Execution Completed Successfully!'")
print()
print("Optionally save as:")
print("  screenshots/part_c_test_gate_fail.png")
print("  screenshots/part_c_test_gate_pass.png")
print("  screenshots/part_c_evaluation_metrics.png")
