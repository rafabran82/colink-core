from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from ..db import session_scope
from ..models import Invoice, PaymentIntent, Quote


router = APIRouter(prefix="/payments/intents", tags=["payment_intents"])


class CreatePIIn(BaseModel):
    invoiceId: str
    paymentCurrency: str


class CreatePIOut(BaseModel):
    id: str
    invoiceId: str
    paymentCurrency: str
    status: str


@router.post("", response_model=CreatePIOut)
def create_payment_intent(payload: CreatePIIn):
    with session_scope() as s:
        inv = s.get(Invoice, payload.invoiceId)
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")

        pi = PaymentIntent(
            invoice_id=inv.id,
            payment_currency=payload.paymentCurrency,
            status="CREATED",
        )
        s.add(pi)
        s.flush()

        return {
            "id": pi.id,
            "invoiceId": pi.invoice_id,
            "paymentCurrency": pi.payment_currency,
            "status": pi.status,
        }


class ConfirmIn(BaseModel):
    quoteId: int = Field(..., description="Persisted Quote id to lock")


class ConfirmOut(BaseModel):
    id: str
    status: str
    locked_price: float
    fee_bps: int
    impact_bps: int
    expiresAt: int


@router.post("/{intent_id}/confirm", response_model=ConfirmOut)
def confirm_intent( payload: ConfirmIn, intent_id: str = Path(...)):
    with session_scope() as s:
        pi = s.get(PaymentIntent, intent_id)
        if not pi:
            raise HTTPException(status_code=404, detail="PaymentIntent not found")

        qt = s.get(Quote, payload.quoteId)
        if not qt:
            raise HTTPException(status_code=404, detail="Quote not found")

        # (Optional) expiry/consistency checks go here
        # e.g., if qt.expires_at < int(time.time()): raise HTTPException(...)

        # Lock!
        pi.locked_price = float(qt.price)
        pi.fee_bps = int(qt.fee_bps or 0)
        pi.impact_bps = int(qt.impact_bps or 0)
        pi.expires_at = int(qt.expires_at or 0)
        pi.status = "LOCKED"

        s.add(pi)
        s.flush()

        return {
            "id": pi.id,
            "status": pi.status,
            "locked_price": pi.locked_price,
            "fee_bps": pi.fee_bps,
            "impact_bps": pi.impact_bps,
            "expiresAt": pi.expires_at,
        }

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..db import session_scope
from ..models import PaymentIntent, Quote

class ConfirmRequest(BaseModel):
    quoteId: int

# If you already have a router, reuse it; otherwise ensure this is attached to the same router you use for PIs.
from fastapi import HTTPException
from pydantic import BaseModel, Field
from ..db import session_scope
from ..models import PaymentIntent, Quote

class ConfirmRequest(BaseModel):
    quoteId: int = Field(..., gt=0)

@router.post("/payments/intents/{pi_id}/confirm")
def confirm_payment_intent(pi_id: str, payload: ConfirmRequest):
    with session_scope() as s:
        pi = s.get(PaymentIntent, pi_id)
        if not pi:
            raise HTTPException(status_code=404, detail="PaymentIntent not found")

        q = s.get(Quote, int(payload.quoteId))
        if not q:
            raise HTTPException(status_code=404, detail="Quote not found")

        pi.quote_id     = q.id
        pi.locked_price = q.price
        pi.fee_bps      = q.fee_bps
        pi.impact_bps   = q.impact_bps
        pi.expires_at   = q.expires_at
        s.flush()

        return {
            "payment_intent_id": pi.id,
            "locked": True,
            "quote_id": q.id,
            "locked_price": pi.locked_price,
            "fee_bps": pi.fee_bps,
            "impact_bps": pi.impact_bps,
            "expires_at": pi.expires_at,
        }
