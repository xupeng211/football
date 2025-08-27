import importlib


def test_smoke_import_data_pipeline_ingest_csv_adapter():
    mod = importlib.import_module("data_pipeline.ingest.csv_adapter")
    assert mod is not None
