from sklearn.datasets import load_iris
import pandas as pd

try:
    from mage_ai.data_preparation.decorators import data_loader, test
except ImportError:
    def data_loader(func):
        return func

    def test(func):
        return func


@data_loader
def load_data(*args, **kwargs):
    """Load the standard Iris classification dataset from scikit-learn."""
    iris = load_iris(as_frame=True)
    df = iris.frame
    return df


@test
def test_output(output, *args):
    """Validate that the dataset loaded with expected schema and rows."""
    assert output is not None, "Output is undefined"
    assert len(output) == 150, f"Expected 150 rows, got {len(output)}"
    assert "target" in output.columns, "Missing 'target' column"
    assert len(output.columns) == 5, f"Expected 5 columns, got {len(output.columns)}"
