
import pandas as pd
from sklearn.datasets import load_iris

from iris_project.transformers.prepare_data import transform


def test_transform_creates_expected_train_test_split():
    df = load_iris(as_frame=True).frame

    result = transform(df)

    assert len(result) == 150
    assert (result["split"] == "train").sum() == 120
    assert (result["split"] == "test").sum() == 30


def test_transform_preserves_original_columns_and_values():
    df = load_iris(as_frame=True).frame

    result = transform(df)

    for column in df.columns:
        pd.testing.assert_series_equal(
            result[column],
            df[column]
        )

    assert "split" in result.columns


def test_transform_is_deterministic():
    df = load_iris(as_frame=True).frame

    first = transform(df)
    second = transform(df)

    assert first["split"].equals(second["split"])


def test_transform_stratifies_target_classes():
    df = load_iris(as_frame=True).frame

    result = transform(df)

    train = result[result["split"] == "train"]
    test = result[result["split"] == "test"]

    assert set(train["target"].unique()) == set(df["target"].unique())
    assert set(test["target"].unique()) == set(df["target"].unique())
