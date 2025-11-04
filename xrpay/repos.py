from __future__ import annotations
import json, hashlib, time, uuid
from typing import Optional
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from .db import session_scope, Base, engine
from .models import Invoice, PaymentIntent, Quote, Outbox, Webhook

def _uuid() -> str:
    return str(uuid.uuid4())

# ----- Outbox helpers -----
def enqueue_outbox(topic: str, payload_json: str, webhook_id: Optional[int]=None):
    with session_scope() as s:
        ob = Outbox(topic=topic, payload_json=payload_json, webhook_id=webhook_id, status="PENDING")
        s.add(ob)

def next_pending_outbox():
    with session_scope() as s:
        row = s.execute(
            select(Outbox).options(joinedload(Outbox.webhook))
            .where(Outbox.status=="PENDING")
            .order_by(Outbox.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        return row

def mark_delivered(outbox_id: int):
    with session_scope() as s:
        s.execute(update(Outbox).where(Outbox.id==outbox_id).values(status="DELIVERED"))

def requeue(outbox_id: int):
    with session_scope() as s:
        s.execute(update(Outbox).where(Outbox.id==outbox_id).values(retries=Outbox.retries+1, status="PENDING"))

def get_active_webhooks():
    with session_scope() as s:
        return s.query(Webhook).filter(Webhook.status == "ACTIVE").all()

def enqueue_to_all(topic: str, payload_json: str) -> int:
    hooks = get_active_webhooks()
    if not hooks:
        enqueue_outbox(topic, payload_json, webhook_id=None)
        return 0
    for w in hooks:
        enqueue_outbox(topic, payload_json, webhook_id=w.id)
    return len(hooks)

# ----- Quote helpers -----
def terms_hash(base:str, quote:str, side:str, amount:str) -> str:
    src = f"{base}|{quote}|{side}|{amount}".encode()
    return hashlib.sha256(src).hexdigest()

def create_quote(base:str, quote:str, side:str, amount:str, price:str, fee_bps:int, impact_bps:int, ttl_sec:int=30) -> Quote:
    qid = _uuid()
    th = terms_hash(base,quote,side,amount)
    exp = int(time.time()) + ttl_sec
    with session_scope() as s:
        q = Quote(
            id=qid, base=base, quote=quote, side=side, amount=amount,
            price=price, fee_bps=fee_bps, impact_bps=impact_bps,
            expires_at=exp, status="VALID", terms_hash=th
        )
        s.add(q)
        s.flush()
        return q

def get_quote(qid:str) -> Optional[Quote]:
    with session_scope() as s:
        return s.get(Quote, qid)

def expire_quote(q: Quote):
    with session_scope() as s:
        s.execute(update(Quote).where(Quote.id==q.id).set({"status":"EXPIRED"}))

def use_quote(q: Quote):
    with session_scope() as s:
        s.execute(update(Quote).where(Quote.id==q.id).set({"status":"USED"}))

# ----- PaymentIntent helpers -----
def attach_quote_to_intent(intent_id:str, quote_id:str, locked_price:str) -> Optional[PaymentIntent]:
    with session_scope() as s:
        pi = s.get(PaymentIntent, intent_id)
        if not pi:
            return None
        pi.quote_id = quote_id
        pi.locked_price = locked_price
        pi.status = "CONFIRMED"
        s.add(pi)
        s.flush()
        return pi
