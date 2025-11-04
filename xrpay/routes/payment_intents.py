from uuid import uuid4
from datetime import datetime, timedelta
from fastapi import APIRouter, Body, HTTPException
from ..db import session_scope
from ..models import PaymentIntent, Invoice, Quote
from ..repos import enqueue_outbox

router = APIRouter(prefix="/payments/intents", tags=["payment_intents"])

@router.post("")
def create_intent(payload: dict = Body(...)):
    inv_id = payload.get("invoiceId")
    pay_ccy = payload.get("paymentCurrency","XRP")
    quote_id = payload.get("quoteId")
    if not inv_id:
        raise HTTPException(400, "invoiceId required")
    intent_id = str(uuid4())

    with session_scope() as s:
        inv = s.get(Invoice, inv_id)
        if not inv:
            raise HTTPException(404, "Invoice not found")
        expires = None
        if quote_id:
            q = s.get(Quote, quote_id)
            if not q:
                raise HTTPException(400, "Quote not found")
            expires = q.expires_at
        s.add(PaymentIntent(
            id=intent_id, invoice_id=inv_id, payment_currency=pay_ccy,
            quote_id=quote_id, quote_expires_at=expires, status="CREATED"
        ))
    return {"id": intent_id, "status": "CREATED"}
