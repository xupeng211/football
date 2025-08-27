import importlib


def test_smoke_import_apps_api_main():
    mod = importlib.import_module("apps.api.main")
    assert mod is not None
