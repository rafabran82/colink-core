def test_package_only_colink_core():
    import pkgutil

    names = {m.name for m in pkgutil.iter_modules()}
    assert "colink_core" in names
