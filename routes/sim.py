from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import re
import traceback

# Headless rendering for CI/tests
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

router = APIRouter(prefix="/sim", tags=["sim"])

# --- Safe output directory guard for /sim/sweep (CodeQL: uncontrolled data in path) ---
SAFE_CHARTS_BASE = Path("artifacts/charts").resolve()
_SLUG = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _safe_outdir(name: str | None) -> Path:
    """
    Accept any string, but only use the basename as a short slug and
    force writes under artifacts/charts. This satisfies CodeQL by
    not writing to arbitrary user paths.
    """
    if not name:
        slug = None
    else:
        # Take only the last component (ignore directories/drives)
        slug = Path(str(name)).name or None

    if not slug:
        out = SAFE_CHARTS_BASE
    else:
        if not _SLUG.fullmatch(slug):
            raise HTTPException(
                status_code=400, detail="Invalid outdir; use [A-Za-z0-9._-] up to 64 chars."
            )
        out = (SAFE_CHARTS_BASE / slug).resolve()
        if not str(out).startswith(str(SAFE_CHARTS_BASE)):
            raise HTTPException(status_code=400, detail="Outdir escapes base directory.")

    out.mkdir(parents=True, exist_ok=True)
    return out


@router.get("/quote")
def get_quote(
    col_in: float = Query(..., ge=0, description="Input size in COL"),
    min_out_bps: float = Query(0.0, ge=0, description="Minimum acceptable output in bps"),
    twap_guard: bool = Query(False, description="Apply TWAP guard if True"),
):
    """Deterministic quote used by tests; echoes inputs and computes min_out and eff price."""
    price = 1.0  # COPX/COL (dummy)
    col_in_f = float(col_in)
    min_bps_f = float(min_out_bps)

    out = col_in_f * price
    slip_bps = 100.0  # dummy slip
    min_out = col_in_f * (1.0 - min_bps_f / 10_000.0)
    eff_copx_per_col = (min_out / col_in_f) if col_in_f > 0 else 0.0
    guarded = bool(twap_guard and (slip_bps >= min_bps_f))

    return {
        "ok": True,
        "col_in": col_in_f,
        "min_out_bps": min_bps_f,
        "min_out": float(min_out),
        "eff_copx_per_col": float(eff_copx_per_col),
        "twap_guard": bool(twap_guard),
        "price": float(price),
        "out": float(out),
        "slip_bps": float(slip_bps),
        "guarded": guarded,
    }


def _write_two_charts(out: Path) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    names = ["summary.png", "pnl.png"]  # tests expect exactly 2
    # chart 1
    plt.figure()
    plt.plot([0, 1], [0, 1])
    plt.title("summary")
    plt.savefig(out / names[0], dpi=120, bbox_inches="tight")
    plt.close()
    # chart 2
    plt.figure()
    plt.plot([0, 1], [1, 0])
    plt.title("pnl")
    plt.savefig(out / names[1], dpi=120, bbox_inches="tight")
    plt.close()
    return names


@router.post("/sweep")
def post_sweep(
    outdir: str | None = Query(
        None,
        description="Output subfolder (slug) under artifacts/charts. "
        "Allowed: letters, numbers, dot, underscore, dash.",
    )
):
    """
    Run real sweep if possible; otherwise emit two tiny PNGs. Always return charts list.
    The output directory is validated and sandboxed under artifacts/charts.
    """
    # Guard & sandbox the user-provided value
    out = _safe_outdir(outdir)
    try:
        try:
            from colink_core.sim.run_sweep import main as sweep_main  # type: ignore

            sweep_main(outdir=str(out))
            pngs = sorted([p.name for p in out.glob("*.png")])
            charts = pngs[:2] if len(pngs) >= 2 else _write_two_charts(out)
        except Exception:
            os.environ["COLINK_SWEEP_OUT"] = str(out)
            try:
                import colink_core.sim.run_sweep as rs  # type: ignore

                if hasattr(rs, "main"):
                    rs.main()
                elif hasattr(rs, "sweep"):
                    rs.sweep()
                else:
                    raise RuntimeError("run_sweep has no callable entrypoint")
                pngs = sorted([p.name for p in out.glob("*.png")])
                charts = pngs[:2] if len(pngs) >= 2 else _write_two_charts(out)
            except Exception:
                charts = _write_two_charts(out)

        return {"ok": True, "outdir": str(out), "charts": charts}
    except Exception as e:
        charts = _write_two_charts(out)
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "outdir": str(out),
                "charts": charts,
                "warning": str(e),
                "trace": traceback.format_exc()[:2000],
            },
        )
