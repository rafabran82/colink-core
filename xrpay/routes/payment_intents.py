from fastapi import APIRouter, Body, HTTPException
import time
from ..repos import get_quote, attach_quote_to_intent
from ..db import session_scope
from ..models import PaymentIntent

router = APIRouter(prefix="/payments/intents", tags=["payment_intents"])

@router.post("")
def create_intent(payload: dict = Body(...)):
    # minimal create (assumes invoice already exists)
    from ..repos import _uuid
    with session_scope() as s:
        pi = PaymentIntent(
            id=_uuid(),
            invoice_id=payload.get("invoiceId"),
            payment_currency=payload.get("paymentCurrency", "XRP"),
            status="CREATED",
        )
        s.add(pi)
        s.flush()
        return {"id": pi.id, "status": pi.status}

@router.post("/{intent_id}/confirm")
def confirm_intent(intent_id: str, payload: dict = Body(...)):
    """
    Body: {"quoteId": "..."}
    Validates:
      - Quote exists and is VALID
      - Not expired (now <= expires_at)
    Locks price into the PaymentIntent (status -> CONFIRMED)
    """
    qid = payload.get("quoteId")
    if not qid:
        raise HTTPException(status_code=400, detail="quoteId required")
    q = get_quote(qid)
    if not q:
        raise HTTPException(status_code=404, detail="quote not found")
    now = int(time.time())
    if q.status != "VALID":
        raise HTTPException(status_code=409, detail=f"quote not valid: {q.status}")
    if now > q.expires_at:
        raise HTTPException(status_code=409, detail="quote expired")

    pi = attach_quote_to_intent(intent_id, qid, q.price)
    if not pi:
        raise HTTPException(status_code=404, detail="payment intent not found")

    # mark quote as used
    from ..repos import use_quote
    use_quote(q)

    return {"id": pi.id, "status": pi.status, "quoteId": qid, "locked_price": pi.locked_price}
