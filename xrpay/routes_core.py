# xrpay/routes_core.py
from __future__ import annotations
from uuid import uuid4
from fastapi import APIRouter, Body
from pydantic import BaseModel

router = APIRouter()

@router.post("/_echo")
async def echo(payload: dict = Body(...)):
    # Return exactly what came in; handy for HMAC + idempotency tests
    return {"ok": True, "echo": payload}

class QuoteIn(BaseModel):
    base: str
    quote: str
    amount: float

class QuoteOut(BaseModel):
    id: str
    base: str
    quote: str
    amount: float
    price: float
    total: float

@router.post("/quotes", response_model=QuoteOut)
async def quotes(req: QuoteIn):
    # Dummy quote engine (replace with your real price source)
    # Use a stable pseudo-price so idempotency is observable
    price = 0.50 if (req.base.upper(), req.quote.upper()) == ("XRP", "USD") else 1.00
    qid = f"q_{uuid4().hex[:12]}"
    total = round(req.amount * price, 8)
    return QuoteOut(id=qid, base=req.base, quote=req.quote, amount=req.amount, price=price, total=total)