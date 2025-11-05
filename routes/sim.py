from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import re

# single source of truth for slug validation
SAFE_SLUG_RE = re.compile(r'^[A-Za-z0-9._-]{1,64}$')

router = APIRouter(prefix="/sim", tags=["sim"])

class EchoIn(BaseModel):
    outdir: str | None = None
    msg: str = "ok"

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/echo")
def echo(payload: EchoIn):
    outdir = payload.outdir or ""
    if outdir and not SAFE_SLUG_RE.match(outdir):
        raise HTTPException(status_code=400, detail="invalid outdir")
    return {"ok": True, "outdir": outdir, "msg": payload.msg}
