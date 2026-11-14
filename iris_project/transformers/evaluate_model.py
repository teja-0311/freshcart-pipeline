import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report

try:
    from mage_ai.data_preparation.decorators import transformer, test
except ImportError:
    def transformer(func):
        return func

    def test(func):
        return func


@transformer
def transform(model_results, *args, **kwargs):
    """Compute confusion matrix and classification report metrics table."""
    y_true = model_results["y_true"]
    y_pred = model_results["y_pred"]

    cm = confusion_matrix(y_true, y_pred)
    report_dict = classification_report(y_true, y_pred, output_dict=True)
    report_df = pd.DataFrame(report_dict).transpose()

    print("=== Model Evaluation ===")
    print("Confusion Matrix:")
    print(cm)
    print("\nMetrics Table:")
    print(report_df)

    return {
        "confusion_matrix": cm.tolist(),
        "metrics_table": report_df.to_dict(),
        "accuracy": model_results["accuracy"],
    }


@test
def test_evaluation_shape(output, *args):
    """Verify that confusion matrix has shape 3x3 for the 3 Iris classes."""
    cm = output["confusion_matrix"]
    assert len(cm) == 3 and len(cm[0]) == 3, f"Expected 3x3 confusion matrix, got {len(cm)}x{len(cm[0])}"
    assert "metrics_table" in output, "Missing metrics table in evaluation output"
