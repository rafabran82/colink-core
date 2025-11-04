from fastapi import APIRouter
from ..db import session_scope
from ..models import Outbox, Invoice

router = APIRouter(prefix="/_debug", tags=["_debug"])

@router.get("/outbox")
def list_outbox():
    with session_scope() as s:
        rows = s.query(Outbox).order_by(Outbox.id.desc()).limit(50).all()
        return [
            {"id": r.id, "topic": r.topic, "status": r.status, "retries": r.retries, "webhook_id": r.webhook_id}
            for r in rows
        ]

@router.get("/invoices")
def list_invoices():
    with session_scope() as s:
        rows = s.query(Invoice).order_by(Invoice.created_at.desc()).limit(50).all()
        return [
            {"id": r.id, "status": r.status, "amount": r.amount, "paid_amount": r.paid_amount, "desc": r.description}
            for r in rows
        ]
