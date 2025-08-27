import importlib


def test_smoke_import_models_predictor():
    mod = importlib.import_module("models.predictor")
    assert mod is not None
