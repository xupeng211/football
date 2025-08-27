import importlib


def test_smoke_import_data_pipeline_ingest_base():
    mod = importlib.import_module("data_pipeline.ingest.base")
    assert mod is not None
