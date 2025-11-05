import pathlib
import sys

# tests/ -> sim/ -> colink_core/ -> <repo root>
ROOT = pathlib.Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
