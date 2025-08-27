import importlib


def test_smoke_import_data_pipeline_features_build():
    mod = importlib.import_module("data_pipeline.features.build")
    assert mod is not None
