from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from ..db import session_scope
from ..models import Invoice, PaymentIntent, Quote

router = APIRouter(prefix="/payments/intents", tags=["payments:intents"])

class CreateIntentIn(BaseModel):
    invoiceId: str = Field(..., alias="invoiceId")
    paymentCurrency: str = Field(..., alias="paymentCurrency")

class CreateIntentOut(BaseModel):
    id: str
    status: str

class ConfirmIn(BaseModel):
    quoteId: int = Field(..., alias="quoteId")

class ConfirmOut(BaseModel):
    id: str
    status: str
    locked_price: float | None = None
    fee_bps: int | None = None
    impact_bps: int | None = None
    expiresAt: int | None = None

@router.post("", response_model=CreateIntentOut)
def create_intent(payload: CreateIntentIn):
    with session_scope() as s:
        inv = s.get(Invoice, payload.invoiceId)
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        intent = PaymentIntent(
            invoice_id=inv.id,
            payment_currency=payload.paymentCurrency,
            status="CREATED",
            locked_price=None,
            fee_bps=None,
            impact_bps=None,
            expires_at=None,
        )
        s.add(intent)
        s.flush()
        return {"id": intent.id, "status": intent.status}

@router.post("/{intent_id}/confirm", response_model=ConfirmOut)
def confirm_intent(intent_id: str, payload: ConfirmIn):
    now = datetime.now(timezone.utc)
    with session_scope() as s:
        intent = s.get(PaymentIntent, intent_id)
        if not intent:
            raise HTTPException(status_code=404, detail="Intent not found")

        q = s.get(Quote, payload.quoteId)
        if not q:
            raise HTTPException(status_code=404, detail="Quote not found")

        # Expiry check (quotes.expires_at stored as epoch seconds, UTC)
        if q.expires_at is not None:
            if int(q.expires_at) < int(now.timestamp()):
                raise HTTPException(status_code=400, detail="Quote expired")

        # Lock values onto the intent
        intent.locked_price = float(q.price) if q.price is not None else None
        intent.fee_bps = int(q.fee_bps) if q.fee_bps is not None else None
        intent.impact_bps = int(q.impact_bps) if q.impact_bps is not None else None
        intent.expires_at = int(q.expires_at) if q.expires_at is not None else None
        intent.status = "CONFIRMED"
        s.add(intent)

        return {
            "id": intent.id,
            "status": intent.status,
            "locked_price": intent.locked_price,
            "fee_bps": intent.fee_bps,
            "impact_bps": intent.impact_bps,
            "expiresAt": intent.expires_at,
        }
