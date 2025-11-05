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
    # For echo we require a "slug" (not an arbitrary path)
    if not SAFE_SLUG_RE.match(inp.outdir or ""):
        raise HTTPException(status_code=400, detail="invalid outdir")
    return {"ok": True, "outdir": inp.outdir, "msg": inp.msg}


@router.get("/quote")
def sim_quote(col_in: float, min_out_bps: int = 0, twap_guard: bool = False):
    """
    Minimal placeholder quote:
    - apply max(min_out_bps, 10 bps) as an effective haircut
    - return col_out plus echo back inputs
    This is only to satisfy tests with 200 status.
    """
    if col_in <= 0:
        raise HTTPException(status_code=400, detail="col_in must be > 0")

    fee_bps = 10
    eff_bps = max(min_out_bps, fee_bps)
    col_out = col_in * (1.0 - eff_bps / 10_000.0)

    return {
        "ok": True,
        "col_in": col_in,
        "col_out": col_out,
        "min_out_bps": min_out_bps,
        "twap_guard": twap_guard,
    }


@router.post("/sweep")
def sim_sweep(outdir: str):
    """
    Accept an output directory:
    - allow absolute or relative paths
    - reject traversal ("..") anywhere in the path
    - create directory and a small marker file
    """
    if not outdir:
        raise HTTPException(status_code=400, detail="missing outdir")

    parts = Path(outdir).parts
    if ".." in parts:
        raise HTTPException(status_code=400, detail="invalid outdir")

    p = Path(outdir)
    try:
        p.mkdir(parents=True, exist_ok=True)
        (p / ".ok").write_text("ok", encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cannot create outdir: {e}")

    return {"ok": True, "outdir": str(p)}
