from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException
from sqlalchemy import select
from ..db import session_scope
from ..models import Invoice
from ..repos import enqueue_outbox

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.post("")
def create_invoice(payload: dict = Body(...)):
    inv_id = str(uuid4())
    currency = payload.get("currency","USD")
    amount = payload.get("amount","0")
    desc = payload.get("description","")
    with session_scope() as s:
        s.add(Invoice(id=inv_id, currency=currency, amount=amount, description=desc, status="OPEN"))
    return {"id": inv_id, "status": "OPEN"}

@router.get("/{invoice_id}")
def get_invoice(invoice_id: str):
    with session_scope() as s:
        row = s.get(Invoice, invoice_id)
        if not row:
            raise HTTPException(404, "Not found")
        return {
            "id": row.id, "status": row.status, "currency": row.currency,
            "amount": row.amount, "paid_amount": row.paid_amount, "description": row.description
        }
