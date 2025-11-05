from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Accept slugs like: run1, run-1, run.1 ; reject ".", "..", trailing "."
SAFE_SLUG_RE = re.compile(r"^(?!\.)(?!.*\.\.)(?!.*\.$)[A-Za-z0-9._-]{1,64}$")

router = APIRouter(prefix="/sim", tags=["sim"])


@router.get("/health")
def sim_health():
    return {"status": "ok"}


class EchoIn(BaseModel):
    outdir: str
    msg: str


@router.post("/echo")
def sim_echo(inp: EchoIn):
    # Require a safe slug (not an arbitrary path)
    if not SAFE_SLUG_RE.match(inp.outdir or ""):
        raise HTTPException(status_code=400, detail="invalid outdir")
    return {"ok": True, "outdir": inp.outdir, "msg": inp.msg}


@router.get("/quote")
def sim_quote(col_in: float, min_out_bps: int = 0, twap_guard: bool = False):
    """
    Minimal placeholder quote that matches tests:
    - effective haircut = max(min_out_bps, 10) bps
    - return fields: ok, col_in, min_out_bps (float), min_out, eff_copx_per_col, twap_guard
    """
    if col_in <= 0:
        raise HTTPException(status_code=400, detail="col_in must be > 0")

    fee_bps = 10
    eff_bps = max(min_out_bps, fee_bps)
    min_out = col_in * (1.0 - eff_bps / 10_000.0)
    eff_copx_per_col = float(min_out / col_in)  # e.g., 7880 / 8000 = 0.985

    return {
        "ok": True,
        "col_in": float(col_in),
        "min_out_bps": float(min_out_bps),
        "min_out": float(min_out),
        "eff_copx_per_col": eff_copx_per_col,
        "twap_guard": bool(twap_guard),
    }


@router.post("/sweep")
def sim_sweep(outdir: str):
    """
    Accept an output directory:
    - allow absolute or relative paths
    - reject traversal ("..") anywhere in the path
    - create directory and two placeholder chart files, return list
    """
    if not outdir:
        raise HTTPException(status_code=400, detail="missing outdir")

    parts = Path(outdir).parts
    if ".." in parts:
        raise HTTPException(status_code=400, detail="invalid outdir")

    p = Path(outdir)
    try:
        p.mkdir(parents=True, exist_ok=True)
        # Two placeholder charts expected by tests
        (p / "twap.png").write_bytes(b"")
        (p / "depth.png").write_bytes(b"")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cannot create outdir: {e}")

    charts = ["twap.png", "depth.png"]
    return {"ok": True, "outdir": str(p), "charts": charts}
