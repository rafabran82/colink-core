import json
from fastapi import APIRouter, Body
from ..repos import enqueue_outbox

router = APIRouter(prefix="/hooks", tags=["hooks"])

@router.post("/xrpl")
def xrpl_hook(payload: dict = Body(...)):
    # Assume payload includes {"invoiceId": "...", "tx": "...", "amount": "..."}
    enqueue_outbox("invoice.payment_detected", json.dumps(payload), webhook_id=None)
    return {"status": "accepted"}
