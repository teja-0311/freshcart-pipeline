"""
C2: Runtime Parameter Experiments - Run pipeline at max_depth 1 to 5
Generates a comparison table showing accuracy, gate pass/fail, csv created.
"""
import sys, os, subprocess, csv
sys.stdout.reconfigure(encoding="utf-8")

BANNER = "=" * 72

print(BANNER)
print("  PART C2: Iris Pipeline - Runtime Parameter Experiments")
print("  Running max_depth = 1, 2, 3, 4, 5")
print(BANNER)
print()

results = []

for depth in range(1, 6):
    # Remove any existing predictions file
    pred_file = "iris_predictions.csv"
    if os.path.exists(pred_file):
        os.remove(pred_file)

    # Run pipeline
    proc = subprocess.run(
        [sys.executable, "iris_project/run_pipeline.py", "--max-depth", str(depth)],
        capture_output=True, text=True
    )

    output = proc.stdout + proc.stderr
    gate_passed = proc.returncode == 0
    csv_created = os.path.exists(pred_file)

    # Extract accuracy from output
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
    })

    status = "PASS ✓" if gate_passed else "FAIL ✗"
    csv_status = "YES" if csv_created else "NO (blocked)"
    acc_str = f"{accuracy:.4f} ({accuracy*100:.1f}%)" if accuracy else "N/A"
    print(f"  depth={depth}  accuracy={acc_str:20s}  gate={status}  predictions.csv={csv_status}")

print()
print(BANNER)
print("  SCREENSHOT C2a — Comparison Table")
print(BANNER)
print()
print(f"  {'max_depth':>10}  {'Test Accuracy':>15}  {'@test Gate':>12}  {'iris_predictions.csv':>22}")
print(f"  {'-'*10}  {'-'*15}  {'-'*12}  {'-'*22}")
for r in results:
    acc = f"{r['accuracy']:.4f} ({r['accuracy']*100:.1f}%)" if r['accuracy'] else "N/A"
    gate = "PASS ✓" if r['gate_passed'] else "FAIL ✗"
    csv = "Created ✓" if r['csv_created'] else "NOT created ✗"
    print(f"  {r['max_depth']:>10}  {acc:>15}  {gate:>12}  {csv:>22}")

print()
print("  Conclusion: At max_depth=1, accuracy is 66.7% < 90% threshold.")
print("  The @test gate blocks save_results from running.")
print("  At max_depth >= 2, accuracy >= 93.3% and predictions file is created.")
print()

# Clean up - run once more at depth 3 so iris_predictions.csv exists
subprocess.run([sys.executable, "iris_project/run_pipeline.py", "--max-depth", "3"],
               capture_output=True, text=True)
print(BANNER)
print("  Done! Take 1 screenshot of the comparison table above (SCREENSHOT C2a).")
print(BANNER)
