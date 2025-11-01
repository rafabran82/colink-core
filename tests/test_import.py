def test_import_main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "app"), "FastAPI app not found in main.py"
