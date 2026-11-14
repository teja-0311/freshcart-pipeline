import os
import pandas as pd
from sklearn.datasets import load_iris

from iris_project.data_loaders.load_iris import load_data
from iris_project.transformers.validate_data import transform as validate_transform
from iris_project.transformers.prepare_data import transform as prepare_transform
from iris_project.transformers.train_model import transform as train_transform
from iris_project.transformers.evaluate_model import transform as evaluate_transform
from iris_project.data_exporters.save_results import export_data


def test_load_iris_data():
    df = load_data()
    assert len(df) == 150
    assert "target" in df.columns
    assert df.isnull().sum().sum() == 0


def test_validate_data_passes_on_valid_dataset():
    df = load_data()
    out = validate_transform(df)
    assert len(out) == 150
    assert len(out["target"].unique()) == 3


def test_train_model_accuracy_gate():
    df = load_data()
    val_df = validate_transform(df)
    split_df = prepare_transform(val_df)

    # depth=1 should get ~66.7% accuracy
    res_depth_1 = train_transform(split_df, max_depth=1)
    assert res_depth_1["accuracy"] < 0.90

    # depth=3 should exceed 90% accuracy
    res_depth_3 = train_transform(split_df, max_depth=3)
    assert res_depth_3["accuracy"] >= 0.90


def test_evaluation_branch_produces_matrix_and_metrics():
    df = load_data()
    split_df = prepare_transform(validate_transform(df))
    model_output = train_transform(split_df, max_depth=3)
    eval_res = evaluate_transform(model_output)

    assert len(eval_res["confusion_matrix"]) == 3
    assert len(eval_res["confusion_matrix"][0]) == 3
    assert "metrics_table" in eval_res


def test_save_results_exports_csv():
    df = load_data()
    split_df = prepare_transform(validate_transform(df))
    model_output = train_transform(split_df, max_depth=3)

    csv_path = "iris_predictions.csv"
    if os.path.exists(csv_path):
        os.remove(csv_path)

    export_data(model_output)
    assert os.path.exists(csv_path)
    saved_df = pd.read_csv(csv_path)
    assert len(saved_df) == 30
    if os.path.exists(csv_path):
        os.remove(csv_path)
