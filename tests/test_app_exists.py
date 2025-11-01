import ast
from pathlib import Path

def _assigned_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names

def test_app_symbol_exists():
    p = Path("main.py")
    assert p.exists(), "main.py not found"
    tree = ast.parse(p.read_text(encoding="utf-8"), filename="main.py")
    names = _assigned_names(tree)
    assert "app" in names, "Expected a top-level name `app` in main.py"
