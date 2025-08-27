import importlib


def test_smoke_import_trainer_fit_xgb():
    mod = importlib.import_module("trainer.fit_xgb")
    assert mod is not None
