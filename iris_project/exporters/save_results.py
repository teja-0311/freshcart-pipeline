import os
import pandas as pd

try:
    from mage_ai.data_preparation.decorators import data_exporter, test
except ImportError:
    def data_exporter(func):
        return func

    def test(func):
        return func

OUTPUT_PATH = "iris_predictions.csv"


@data_exporter
def export_data(model_results, *args, **kwargs):
    """Save model predictions on the test set to a CSV file."""
    preds_df = model_results["predictions"]
    preds_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(preds_df)} predictions to {OUTPUT_PATH}")
    return preds_df


@test
def test_predictions_file_created(output, *args):
    """Verify that iris_predictions.csv exists and contains 30 test records."""
    assert os.path.exists(OUTPUT_PATH), f"Target predictions file '{OUTPUT_PATH}' was not created!"
    df = pd.read_csv(OUTPUT_PATH)
    assert len(df) == 30, f"Expected 30 test predictions in CSV, got {len(df)}"
