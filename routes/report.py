from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from colink_core.sim.report_zip import build_report

router = APIRouter(prefix="/sim", tags=["sim"])


@router.get("/report")
def sim_report():
    try:
        z = build_report()
        return FileResponse(z, media_type="application/zip", filename=Path(z).name)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
