import json
from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, Body
from ..db import session_scope
from ..models import Invoice
from ..repos import enqueue_to_all

router = APIRouter(prefix="/hooks", tags=["hooks"])

@router.post("/xrpl")
def xrpl_hook(payload: dict = Body(...)):
    # expected: {"invoiceId":"...","tx":"...","amount":"25.00"}
    inv_id = payload.get("invoiceId")
    amt_raw = payload.get("amount","0")
    try:
        amt = Decimal(str(amt_raw))
    except InvalidOperation:
        amt = Decimal("0")

    applied = False
    new_status = None

    if inv_id:
        with session_scope() as s:
            inv = s.get(Invoice, inv_id)
            if inv:
                try:
                    paid = Decimal(inv.paid_amount or "0") + amt
                    inv.paid_amount = format(paid, "f")
                    total = Decimal(inv.amount or "0")
                    if total > 0:
                        if paid >= total:
                            inv.status = "PAID"
                        elif paid > 0:
                            inv.status = "PARTIALLY_PAID"
                    new_status = inv.status
                    s.add(inv)
                    applied = True
                except InvalidOperation:
                    pass

    # Always enqueue event for webhooks
    enqueue_to_all("invoice.payment_detected", json.dumps(payload))
    return {"status": "accepted", "applied": applied, "newStatus": new_status}
