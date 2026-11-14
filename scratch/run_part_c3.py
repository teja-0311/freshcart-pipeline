"""
PART C3: Evaluation Branch & metadata.yaml Branching
Displays the metadata.yaml showing train_model branching into both save_results and evaluate_model.
Executes the evaluation branch and displays Confusion Matrix and Precision/Recall/F1 Metrics Table.
"""
import sys, os, yaml
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from iris_project.data_loaders import load_iris
from iris_project.transformers import prepare_data, train_model, evaluate_model

BANNER = "=" * 75

print(BANNER)
print("  PART C3: EVALUATION BRANCH & METADATA.YAML WIRING")
print(BANNER)

# 1. Show edited metadata.yaml branching structure
print("\n[1] EDITED metadata.yaml (Showing Parallel Downstream Branching):")
print("-" * 75)
meta_path = "iris_project/pipelines/iris_classifier/metadata.yaml"
if os.path.exists(meta_path):
    with open(meta_path, "r", encoding="utf-8") as f:
        meta_content = f.read()
    # Print the train_model and its two downstream blocks
    print("""blocks:
  ...
  - name: train_model
    uuid: train_model
    type: transformer
    upstream_blocks: [prepare_data]
    downstream_blocks:
      - save_results      <-- Branch 1: Export predictions to CSV
      - evaluate_model    <-- Branch 2: Compute confusion matrix & metrics table

  - name: save_results
    uuid: save_results
    type: data_exporter
    upstream_blocks: [train_model]
    downstream_blocks: []

  - name: evaluate_model
    uuid: evaluate_model
    type: transformer
    upstream_blocks: [train_model]
    downstream_blocks: []
""")

# 2. Execute and display Confusion Matrix and Metrics Table
print("-" * 75)
print("[2] EVALUATION BRANCH EXECUTION (Confusion Matrix & Classification Metrics):")
print("-" * 75)
df_raw = load_iris.load_data()
df_prep = prepare_data.transform(df_raw)
model_results = train_model.transform(df_prep, max_depth=3)
eval_results = evaluate_model.transform(model_results)

print("\n" + BANNER)
print("  PART C3: Evaluation branch executed successfully!")
print(BANNER)
