import argparse
import inspect
import json
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from iris_project.data_loaders import load_iris
from iris_project.data_exporters import save_results
from iris_project.transformers import evaluate_model, prepare_data, train_model, validate_data


def run_block_tests(module, output):
    """Find and execute all functions decorated with @test in the given module."""
    test_funcs = [
        obj for name, obj in inspect.getmembers(module, inspect.isfunction)
        if name.startswith("test_")
    ]
    for func in test_funcs:
        print(f"   Running @test: {func.__name__}...", end=" ")
        try:
            func(output)
            print("PASSED")
        except AssertionError as e:
            print("FAILED")
            print(f"      Assertion Error: {e}")
            raise


def execute_pipeline(max_depth=3):
    """Execute the Iris classification DAG step by step."""
    print("=" * 60)
    print(f"Executing Iris Pipeline (max_depth={max_depth})")
    print("=" * 60)

    # Step 1: Data Loader
    print("\n[Block 1: load_iris (data_loader)]")
    raw_df = load_iris.load_data()
    print(f"   Loaded dataset shape: {raw_df.shape}")
    run_block_tests(load_iris, raw_df)

    # Step 2: Validate Data (Custom Block C4)
    print("\n[Block 2: validate_data (transformer - custom)]")
    validated_df = validate_data.transform(raw_df)
    run_block_tests(validate_data, validated_df)

    # Step 3: Prepare Data (Transformer)
    print("\n[Block 3: prepare_data (transformer)]")
    split_df = prepare_data.transform(validated_df)
    print(f"   Train split: {(split_df['split'] == 'train').sum()}, Test split: {(split_df['split'] == 'test').sum()}")
    run_block_tests(prepare_data, split_df)

    # Step 4: Train Model (Transformer)
    print("\n[Block 4: train_model (transformer)]")
    model_output = train_model.transform(split_df, max_depth=max_depth)
    acc = model_output["accuracy"]
    print(f"   Model Accuracy: {acc:.4f} ({acc*100:.1f}%)")

    # Quality Gate Test on train_model
    try:
        run_block_tests(train_model, model_output)
    except AssertionError:
        print("\n[PIPELINE BLOCKED BY TEST GATE]")
        print("   Downstream blocks ('save_results' and 'evaluate_model') will NOT be executed!")
        return {
            "max_depth": max_depth,
            "accuracy": acc,
            "test_passed": False,
            "file_created": os.path.exists("iris_predictions.csv"),
        }

    # Step 5: Save Results (Data Exporter) - executed only if gate passes
    print("\n[Block 5: save_results (data_exporter)]")
    save_results.export_data(model_output)
    run_block_tests(save_results, model_output["predictions"])

    # Step 6: Evaluate Model (Transformer - Evaluation Branch C3)
    print("\n[Block 6: evaluate_model (transformer - evaluation branch)]")
    eval_output = evaluate_model.transform(model_output)
    run_block_tests(evaluate_model, eval_output)

    print("\n" + "=" * 60)
    print("Pipeline Execution Completed Successfully!")
    print("=" * 60)

    return {
        "max_depth": max_depth,
        "accuracy": acc,
        "test_passed": True,
        "file_created": os.path.exists("iris_predictions.csv"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Iris Mage Pipeline")
    parser.add_argument("--runtime-vars", type=str, default=None, help="JSON string with runtime variables")
    parser.add_argument("--max-depth", type=int, default=3, help="Decision tree maximum depth")
    args = parser.parse_args()

    depth = args.max_depth
    if args.runtime_vars:
        try:
            vars_dict = json.loads(args.runtime_vars)
            if "max_depth" in vars_dict:
                depth = int(vars_dict["max_depth"])
        except Exception as err:
            print(f"Warning: Failed to parse --runtime-vars ({err}). Using max_depth={depth}")

    res = execute_pipeline(max_depth=depth)
    if not res["test_passed"]:
        sys.exit(1)
