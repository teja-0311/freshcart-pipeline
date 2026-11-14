import os
from stream.lakehouse_consumer import write_landing_batch


def test_write_landing_batch_generates_gzip_ndjson():
    mock_records = [
        {"id": "STREAM-001", "city": "bangalore", "zone": "koramangala", "amount": "500", "currency": "INR"},
        {"id": "STREAM-002", "city": "chennai", "zone": "tnagar", "amount": "750", "currency": "INR"}
    ]
    path = write_landing_batch("test_stream", mock_records, "test_run_01")
    assert os.path.exists(path)
    assert path.name.endswith(".json.gz")
    if os.path.exists(path):
        os.remove(path)
