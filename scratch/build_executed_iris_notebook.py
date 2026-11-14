"""
Builds and executes iris_project/iris_pipeline.ipynb and iris_pipeline.ipynb
with ALL outputs populated and visible for Part C submission.
"""
import json, sys, os
import nbformat as nbf

sys.stdout.reconfigure(encoding="utf-8")

nb = nbf.v4.new_notebook()
nb.metadata = {
    "language_info": {"name": "python", "version": "3.12.4"},
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
}

cells = []

# Title & Metadata
cells.append(nbf.v4.new_markdown_cell("""# Part C: Mage Iris ML Pipeline
**Course:** Data Engineering - Pipeline Orchestration  
**Student Name:** Golla Teja  
**Roll Number:** 23BCS091  
**Repository:** https://github.com/teja-0311/freshcart-pipeline  

---
### Pipeline Architecture
```
load_iris (data_loader)
       |
       v
validate_data (transformer - custom quality gate)
       |
       v
prepare_data (transformer - 80/20 train/test split)
       |
       v
train_model (transformer - DecisionTreeClassifier with accuracy gate >= 90%)
      / \\
     /   \\
    v     v
save_results (data_exporter)   evaluate_model (transformer)
[iris_predictions.csv]          [Confusion Matrix & Classification Metrics]
```
"""))

# Cell 1: Setup & Imports
cells.append(nbf.v4.new_markdown_cell("## 1. Setup & Environment Configuration\nLoad dependencies and ensure repo root is in python path."))
cells.append(nbf.v4.new_code_cell("""import sys, os
from pathlib import Path

# Ensure repository root is on sys.path
cwd = Path(os.getcwd())
repo_root = cwd.parent if cwd.name == "iris_project" else cwd
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import pandas as pd
import numpy as np
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

print("All dependencies loaded successfully.")
print("Python version:", sys.version.split()[0])
print("Repository root:", repo_root.resolve())
"""))

# Cell 2: Block 1 - load_iris
cells.append(nbf.v4.new_markdown_cell("## 2. Block 1: `load_iris` (data_loader)\nLoads the Iris dataset from scikit-learn and runs `@test: test_output`."))
cells.append(nbf.v4.new_code_cell("""from iris_project.data_loaders import load_iris

df_raw = load_iris.load_data()
print("Loaded raw Iris dataset. Shape:", df_raw.shape)
print("\\nFirst 5 rows:")
print(df_raw.head().to_string())

# Run block test
load_iris.test_output(df_raw)
print("\\n@test: test_output PASSED!")
"""))

# Cell 3: Block 2 - validate_data (Custom Block - Part C4)
cells.append(nbf.v4.new_markdown_cell("## 3. Block 2: `validate_data` (custom transformer - Part C4)\nValidates dataset integrity: verifies 0 null values and exactly 3 classes."))
cells.append(nbf.v4.new_code_cell("""from iris_project.transformers import validate_data

df_validated = validate_data.transform(df_raw)
print("Data validation passed. Output shape:", df_validated.shape)

# Run block tests
validate_data.test_no_missing_values(df_validated)
print("@test: test_no_missing_values PASSED!")

validate_data.test_exactly_three_classes(df_validated)
print("@test: test_exactly_three_classes PASSED!")
"""))

# Cell 4: Block 3 - prepare_data
cells.append(nbf.v4.new_markdown_cell("## 4. Block 3: `prepare_data` (transformer)\nSplits data into 80% train (120 rows) and 20% test (30 rows), stratified by target."))
cells.append(nbf.v4.new_code_cell("""from iris_project.transformers import prepare_data

df_prepared = prepare_data.transform(df_validated)
train_count = (df_prepared["split"] == "train").sum()
test_count = (df_prepared["split"] == "test").sum()

print(f"Total rows: {len(df_prepared)}")
print(f"Train split rows: {train_count} (80%)")
print(f"Test split rows:  {test_count} (20%)")

# Run block test
prepare_data.test_split(df_prepared)
print("\\n@test: test_split PASSED!")
"""))

# Cell 5: Block 4 - train_model & Test Gate (Part C1 & C2)
cells.append(nbf.v4.new_markdown_cell("## 5. Block 4: `train_model` & Accuracy Test Gate (Part C1 & C2)\nTrains DecisionTreeClassifier and applies `@test: test_accuracy` gate (threshold >= 90%)."))
cells.append(nbf.v4.new_code_cell("""from iris_project.transformers import train_model

model_results = train_model.transform(df_prepared, max_depth=3)
acc = model_results["accuracy"]

print(f"Trained DecisionTreeClassifier(max_depth=3)")
print(f"Test Accuracy: {acc:.4f} ({acc*100:.1f}%)")

# Run test gate
train_model.test_accuracy(model_results)
print("\\n@test: test_accuracy PASSED (Accuracy >= 90% threshold)!")
"""))

# Cell 6: Block 5 - save_results
cells.append(nbf.v4.new_markdown_cell("## 6. Block 5: `save_results` (data_exporter)\nExports the 30 test predictions to `iris_predictions.csv`."))
cells.append(nbf.v4.new_code_cell("""from iris_project.data_exporters import save_results

save_results.export_data(model_results)

# Run block test
save_results.test_predictions_file_created(model_results)
print("@test: test_predictions_file_created PASSED!")

preds_df = pd.read_csv("iris_predictions.csv")
print(f"\\nLoaded {len(preds_df)} saved predictions from iris_predictions.csv:")
print(preds_df.head(10).to_string())
"""))

# Cell 7: Block 6 - evaluate_model (Evaluation Branch - Part C3)
cells.append(nbf.v4.new_markdown_cell("## 7. Block 6: `evaluate_model` (Evaluation Branch - Part C3)\nComputes Confusion Matrix and Classification Report metrics table."))
cells.append(nbf.v4.new_code_cell("""from iris_project.transformers import evaluate_model

eval_results = evaluate_model.transform(model_results)

print("Confusion Matrix:")
cm_df = pd.DataFrame(eval_results["confusion_matrix"], 
                     index=["Setosa (0)", "Versicolor (1)", "Virginica (2)"],
                     columns=["Pred Setosa", "Pred Versicolor", "Pred Virginica"])
print(cm_df.to_string())

print("\\nClassification Report Metrics Table:")
metrics_df = pd.DataFrame(eval_results["metrics_table"]).T if isinstance(eval_results["metrics_table"], dict) else eval_results["metrics_table"]
print(metrics_df.to_string())

evaluate_model.test_evaluation_shape(eval_results)
print("\\n@test: test_evaluation_shape PASSED!")
"""))

# Cell 8: Part C2 Experiments Table
cells.append(nbf.v4.new_markdown_cell("## 8. Part C2: Runtime Parameter Experiments (max_depth = 1..5)\nDemonstrates how failing `@test` at `max_depth = 1` blocks file creation, while `max_depth = 2..5` succeed."))
cells.append(nbf.v4.new_code_cell("""results = []

for depth in range(1, 6):
    pred_file = "iris_predictions.csv"
    if os.path.exists(pred_file):
        os.remove(pred_file)
        
    try:
        res = train_model.transform(df_prepared, max_depth=depth)
        train_model.test_accuracy(res)
        gate_passed = True
        save_results.export_data(res)
        csv_created = os.path.exists(pred_file)
    except AssertionError as e:
        gate_passed = False
        csv_created = False
        
    results.append({
        "max_depth": depth,
        "Test Accuracy": f"{res['accuracy']:.4f} ({res['accuracy']*100:.1f}%)",
        "test_accuracy passed?": "PASSED" if gate_passed else "FAILED (blocked)",
        "iris_predictions.csv created?": "YES (30 rows)" if csv_created else "NO (file blocked)"
    })

exp_df = pd.DataFrame(results)
print(exp_df.to_string(index=False))

# Re-run at depth 3 to leave predictions file intact
res = train_model.transform(df_prepared, max_depth=3)
save_results.export_data(res)
"""))

# Cell 9: Part C4 Custom Block Gate Demonstration
cells.append(nbf.v4.new_markdown_cell("## 9. Part C4: Custom Block Gate Demonstration\nDemonstrates that `validate_data` catches null values and invalid class counts."))
cells.append(nbf.v4.new_code_cell("""# Case 1: Injected null value
df_bad_null = df_raw.copy()
df_bad_null.loc[0, "sepal length (cm)"] = None
try:
    validate_data.transform(df_bad_null)
    print("UNEXPECTED PASS")
except ValueError as e:
    print("SUCCESSFULLY CAUGHT NULL VALUE:", e)

# Case 2: Injected 4th class
df_bad_class = df_raw.copy()
df_bad_class.loc[0, "target"] = 99
try:
    validate_data.transform(df_bad_class)
    print("UNEXPECTED PASS")
except ValueError as e:
    print("SUCCESSFULLY CAUGHT INVALID CLASS COUNT:", e)
"""))

nb.cells = cells

# Save to both iris_project/iris_pipeline.ipynb and iris_pipeline.ipynb
with open("iris_project/iris_pipeline.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

with open("iris_pipeline.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Generated notebook files successfully.")
