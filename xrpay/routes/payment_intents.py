from fastapi import APIRouter, Body, HTTPException, Path
from ..db import session_scope
from ..models import PaymentIntent, Quote

router = APIRouter(prefix="/payments/intents", tags=["payment_intents"])

@router.post("")
def create_intent(payload: dict = Body(...)):
    invoice_id = payload.get("invoiceId")
    pay_ccy    = payload.get("paymentCurrency") or "XRP"
    with session_scope() as s:
        row = PaymentIntent(invoice_id=invoice_id, payment_currency=pay_ccy, status="CREATED")
        s.add(row); s.flush()
        return {"id": row.id, "status": row.status}

@router.post("/{intent_id}/confirm")
def confirm_intent(intent_id: str = Path(...), payload: dict = Body(...)):
    quote_id = payload.get("quoteId")
    if not quote_id:
        raise HTTPException(status_code=400, detail="quoteId required")
    with session_scope() as s:
        intent = s.get(PaymentIntent, intent_id)
        if not intent:
            raise HTTPException(status_code=404, detail="intent not found")
        q = s.get(Quote, quote_id)
        if not q:
            raise HTTPException(status_code=404, detail="quote not found")

        # lock price + mark CONFIRMED
        intent.locked_quote_id = q.id
        intent.locked_price = q.price
        intent.status = "CONFIRMED"
        s.add(intent)
        return {
            "id": intent.id,
            "status": intent.status,
            "lockedQuoteId": intent.locked_quote_id,
            "lockedPrice": float(intent.locked_price),
        }
