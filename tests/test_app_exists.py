import importlib.util

def test_app_exists():
    spec = importlib.util.spec_from_file_location("main", "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "app"), "main.app not found"
