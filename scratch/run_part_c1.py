"""
PART C1: Iris ML Pipeline Architecture & Execution
Shows all blocks (load_iris -> validate_data -> prepare_data -> train_model -> save_results & evaluate_model),
their block types, and execution of @test for each block.
"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from iris_project.data_loaders import load_iris
from iris_project.transformers import validate_data, prepare_data, train_model, evaluate_model
from iris_project.data_exporters import save_results
from iris_project.run_pipeline import run_block_tests

BANNER = "=" * 75

print(BANNER)
print("  PART C1: IRIS ML PIPELINE EXECUTION & BLOCK TESTS")
print("  Pipeline UUID: iris_classifier")
print(BANNER)
print("""
PIPELINE BLOCK GRAPH & TYPES:
  [Block 1: load_iris]      (Type: data_loader)   --> @test: test_output
         |
         v
  [Block 2: validate_data]  (Type: transformer)   --> @test: test_no_missing_values, test_exactly_three_classes
         |
         v
  [Block 3: prepare_data]   (Type: transformer)   --> @test: test_split
         |
         v
  [Block 4: train_model]    (Type: transformer)   --> @test: test_accuracy (Threshold: >= 90%)
        / \\
       /   \\
      v     v
  [Block 5: save_results]   [Block 6: evaluate_model]
  (Type: data_exporter)     (Type: transformer)
  @test: predictions_saved  @test: test_evaluation_shape
""")
print("-" * 75)
print("RUNNING PIPELINE BLOCKS WITH @test GATES (Default max_depth = 3):")
print("-" * 75)

# Block 1
print("\n--> [Block 1: load_iris (data_loader)]")
df_raw = load_iris.load_data()
print(f"    Loaded raw Iris dataset. Shape: {df_raw.shape}")
run_block_tests(load_iris, df_raw)

# Block 2
print("\n--> [Block 2: validate_data (transformer)]")
df_validated = validate_data.transform(df_raw)
print(f"    Validated data integrity. Shape: {df_validated.shape}")
run_block_tests(validate_data, df_validated)

# Block 3
print("\n--> [Block 3: prepare_data (transformer)]")
df_prepared = prepare_data.transform(df_validated)
train_count = (df_prepared["split"] == "train").sum()
test_count = (df_prepared["split"] == "test").sum()
print(f"    Split dataset 80/20. Train count: {train_count}, Test count: {test_count}")
run_block_tests(prepare_data, df_prepared)

# Block 4
print("\n--> [Block 4: train_model (transformer)]")
model_results = train_model.transform(df_prepared, max_depth=3)
acc = model_results["accuracy"]
print(f"    Trained DecisionTreeClassifier(max_depth=3). Test Accuracy: {acc:.4f} ({acc*100:.1f}%)")
run_block_tests(train_model, model_results)

# Block 5
print("\n--> [Block 5: save_results (data_exporter)]")
save_results.export_data(model_results)
run_block_tests(save_results, model_results)

# Block 6
print("\n--> [Block 6: evaluate_model (transformer - evaluation branch)]")
eval_results = evaluate_model.transform(model_results)
run_block_tests(evaluate_model, eval_results)

print("\n" + BANNER)
print("  PART C1: Pipeline executed successfully! All @test gates PASSED.")
print(BANNER)
