# Updated COLINK test: ensure main app imports without errors

def test_import_main():
    import colink_core.api.main as main
    assert hasattr(main, "app")
