import importlib


def test_smoke_import_data_pipeline_features_rolling():
    mod = importlib.import_module("data_pipeline.features.rolling")
    assert mod is not None
