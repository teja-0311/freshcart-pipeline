import pandas as pd

try:
    from mage_ai.data_preparation.decorators import transformer, test
except ImportError:
    def transformer(func):
        return func

    def test(func):
        return func


@transformer
def transform(df, *args, **kwargs):
    """Validate data quality: checks for nulls, dimensions, and target classes."""
    if df.isnull().values.any():
        raise ValueError("Dataset contains unexpected missing/null values")
    if len(df["target"].unique()) != 3:
        raise ValueError(f"Expected exactly 3 target classes, found {len(df['target'].unique())}")
    return df


@test
def test_no_missing_values(output, *args):
    """Verify that there are zero missing values in the entire dataset."""
    assert output.isnull().sum().sum() == 0, "Missing values detected in Iris dataset"


@test
def test_exactly_three_classes(output, *args):
    """Verify that exactly 3 distinct target classes exist."""
    classes = output["target"].unique()
    assert len(classes) == 3, f"Expected 3 target classes, found {len(classes)}: {classes}"
