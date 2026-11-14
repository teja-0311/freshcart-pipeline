import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

try:
    from mage_ai.data_preparation.decorators import transformer, test
except ImportError:
    def transformer(func):
        return func

    def test(func):
        return func


@transformer
def transform(df, *args, **kwargs):
    """Train a DecisionTreeClassifier on the train split and evaluate on the test split."""
    # Retrieve max_depth from runtime parameters or kwargs, defaulting to 3
    runtime_vars = kwargs.get("runtime_vars", {})
    max_depth = kwargs.get("max_depth", runtime_vars.get("max_depth", 3))
    if isinstance(max_depth, str):
        try:
            max_depth = int(max_depth)
        except ValueError:
            max_depth = 3

    train_df = df[df["split"] == "train"]
    test_df = df[df["split"] == "test"]

    features = [c for c in df.columns if c not in ["target", "split"]]
    X_train = train_df[features]
    y_train = train_df["target"]
    X_test = test_df[features]
    y_test = test_df["target"]

    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))

    test_predictions = test_df.copy()
    test_predictions["predicted_target"] = y_pred

    print(f"Model trained with max_depth={max_depth}. Test Accuracy: {accuracy:.4f} ({accuracy*100:.1f}%)")

    return {
        "model": clf,
        "accuracy": accuracy,
        "max_depth": max_depth,
        "predictions": test_predictions,
        "y_true": y_test.tolist(),
        "y_pred": y_pred.tolist(),
        "features": features,
    }


@test
def test_accuracy(output, *args):
    """Quality gate: enforce minimum accuracy of 90%."""
    accuracy = output["accuracy"]
    assert accuracy >= 0.90, f"Model accuracy {accuracy:.2%} failed quality gate threshold of 90%"
