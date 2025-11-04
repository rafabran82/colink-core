from colink_core.sim.json_cli import cmd_quote
import json
from argparse import Namespace

def test_quote_keys_shape():
    ns = Namespace(col_in=8000.0, min_out_bps=150.0, twap_guard=True)
    # reuse the CLI function and capture stdout
    from io import StringIO
    import sys
    old = sys.stdout
    try:
        buf = StringIO()
        sys.stdout = buf
        cmd_quote(ns)
        data = json.loads(buf.getvalue())
    finally:
        sys.stdout = old
    required = {"col_in","copx_out","eff_copx_per_col","min_out_bps","min_out","twap_guard","raw"}
    assert required.issubset(data.keys())
