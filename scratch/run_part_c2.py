"""
PART C2: Runtime Parameter Experiments & Test Gate Invariant
Runs max_depth = 1, 2, 3, 4, 5.
Shows how failing @test at max_depth=1 (accuracy 66.7% < 90%) blocks save_results
from creating iris_predictions.csv, while max_depth 2..5 pass and write predictions.
"""
import sys, os, subprocess
sys.stdout.reconfigure(encoding="utf-8")

BANNER = "=" * 75

print(BANNER)
print("  PART C2: RUNTIME PARAMETER EXPERIMENTS & TEST GATE INVARIANT")
print("  Parameters: max_depth = 1, 2, 3, 4, 5  | Quality Gate Threshold: >= 90%")
print(BANNER)
print()

results = []

for depth in range(1, 6):
    pred_file = "iris_predictions.csv"
    if os.path.exists(pred_file):
        os.remove(pred_file)

    proc = subprocess.run(
        [sys.executable, "iris_project/run_pipeline.py", "--max-depth", str(depth)],
        capture_output=True, text=True
    )

    output = proc.stdout + proc.stderr
    gate_passed = proc.returncode == 0
    csv_created = os.path.exists(pred_file)

    accuracy = None
    for line in output.splitlines():
        if "Test Accuracy:" in line:
            try:
                acc_str = line.split("Test Accuracy:")[1].split("(")[0].strip()
                accuracy = float(acc_str)
            except Exception:
                pass

    results.append({
        "max_depth": depth,
        "accuracy": accuracy,
        "gate_passed": gate_passed,
        "csv_created": csv_created,
        "raw_error": "AssertionError: Model accuracy < 90%" if not gate_passed else "None"
    })

    print(f"--- Experiment: max_depth = {depth} ---")
    if not gate_passed:
        print(f"  Accuracy: {accuracy*100:.1f}%  -->  @test Gate: FAILED ✗")
        print(f"  Downstream Status: save_results BLOCKED (iris_predictions.csv NOT created)")
    else:
        print(f"  Accuracy: {accuracy*100:.1f}%  -->  @test Gate: PASSED ✓")
        print(f"  Downstream Status: save_results EXECUTED (iris_predictions.csv created successfully)")
    print()

print(BANNER)
print("  PART C2: EXPERIMENT COMPARISON TABLE")
print(BANNER)
print(f"  {'max_depth':>10}  {'Test Accuracy':>15}  {'test_accuracy passed?':>25}  {'iris_predictions.csv created?':>30}")
print(f"  {'-'*10}  {'-'*15}  {'-'*25}  {'-'*30}")
for r in results:
    acc_text = f"{r['accuracy']:.4f} ({r['accuracy']*100:.1f}%)" if r['accuracy'] else "N/A"
    gate_text = "PASSED ✓" if r['gate_passed'] else "FAILED (blocked) ✗"
    csv_text = "YES ✓" if r['csv_created'] else "NO (file blocked) ✗"
    print(f"  {r['max_depth']:>10}  {acc_text:>15}  {gate_text:>25}  {csv_text:>30}")

print("\n" + "-" * 75)
print("ENGINEERING EXPLANATION (For Report):")
print("""  1. How failing @test stops save_results:
     In Mage DAG orchestration, each block defines upstream and downstream dependencies.
     When train_model's @test decorator raises AssertionError (accuracy 66.7% < 90%),
     the runner catches the exception, marks train_model as FAILED, and halts execution.
     Downstream blocks ('save_results' and 'evaluate_model') are never invoked.

  2. Why this is superior to checking afterwards:
     Post-hoc checking risks corrupted or low-accuracy predictions leaking into production
     databases, BI dashboards, or downstream consumers. Halting at the gate ensures zero
     dirty outputs are ever persisted or published.""")
print(BANNER)

# Re-run at depth 3 to leave predictions intact
subprocess.run([sys.executable, "iris_project/run_pipeline.py", "--max-depth", "3"],
               capture_output=True, text=True)
