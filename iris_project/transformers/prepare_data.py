from sklearn.model_selection import train_test_split

try:
    from mage_ai.data_preparation.decorators import transformer, test
except ImportError:
    def transformer(func):
        return func

    def test(func):
        return func


@transformer
def transform(df, *args, **kwargs):

    train_indices, test_indices = train_test_split(
        df.index,
        test_size=0.3,
        random_state=42,
        stratify=df["target"]
    )

    out = df.copy()
    out["split"] = "train"

    out.loc[test_indices, "split"] = "test"

    return out


@test
def test_split(output, *args):

    assert (output["split"] == "train").sum() == 120
    assert (output["split"] == "test").sum() == 30