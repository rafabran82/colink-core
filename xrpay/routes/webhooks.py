from fastapi import APIRouter, Body, HTTPException
from ..db import session_scope
from ..models import Webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("")
def create_webhook(payload: dict = Body(...)):
    url = payload.get("url")
    secret = payload.get("secret")
    if not url:
        raise HTTPException(status_code=400, detail="url required")
    with session_scope() as s:
        wh = Webhook(url=url, secret=secret or None, status="ACTIVE")
        s.add(wh)
        s.flush()
        return {"id": wh.id, "url": wh.url, "status": wh.status}

@router.get("")
def list_webhooks():
    with session_scope() as s:
        rows = s.query(Webhook).order_by(Webhook.id.asc()).all()
        return [{"id": r.id, "url": r.url, "status": r.status} for r in rows]
