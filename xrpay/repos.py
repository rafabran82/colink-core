from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import json
from sqlalchemy import select, text
from .db import session_scope, Base, engine
from .models import IdempotencyKey, Webhook, Outbox, Quote, Invoice, PaymentIntent

def init_db():
    Base.metadata.create_all(bind=engine)

# Idempotency Store
class SQLIdemStore:
    async def get(self, key: str):
        with session_scope() as s:
            row = s.get(IdempotencyKey, key)
            if not row:
                return None
            return {
                "fingerprint": row.fingerprint,
                "status": row.status,
                "body_bytes": row.body_bytes,
                "media_type": row.media_type,
            }

    async def set(self, key: str, value: dict, ttl: int):
        with session_scope() as s:
            row = IdempotencyKey(
                key=key,
                fingerprint=value["fingerprint"],
                status=value["status"],
                body_bytes=value["body_bytes"],
                media_type=value.get("media_type","application/json"),
            )
            s.merge(row)

# Outbox/Webhook basic repos
def enqueue_outbox(topic: str, payload_json: str, webhook_id: int | None = None):
    with session_scope() as s:
        ob = Outbox(topic=topic, payload_json=payload_json, webhook_id=webhook_id)
        s.add(ob)

def next_pending_outbox():
    with session_scope() as s:
        row = s.execute(
            select(Outbox).options(joinedload(Outbox.webhook)).where(Outbox.status=="PENDING").order_by(Outbox.id.asc())
        ).scalars().first()
        if row:
            return row
        return None

def mark_delivered(outbox_id: int):
    with session_scope() as s:
        row = s.get(Outbox, outbox_id)
        if row:
            row.status = "DELIVERED"
            row.retries += 1
            s.add(row)

def requeue(outbox_id: int):
    with session_scope() as s:
        row = s.get(Outbox, outbox_id)
        if row:
            row.retries += 1
            row.next_attempt_at = datetime.utcnow() + timedelta(seconds=min(60, 2**row.retries))
            s.add(row)


def get_active_webhooks():
    """Return active Webhook rows."""
    with session_scope() as s:
        return s.query(Webhook).filter(Webhook.status == "ACTIVE").all()

def enqueue_to_all(topic: str, payload_json: str) -> int:
    """
    Fan-out to all active webhooks by creating Outbox rows.
    Falls back to a single no-op Outbox if none exist.
    """
    hooks = get_active_webhooks()
    try:
        # reuse existing enqueue_outbox from this module
        enqueue = enqueue_outbox
    except NameError:
        # If the symbol name changed, raise a clear error
        raise RuntimeError("enqueue_outbox() not found in xrpay.repos")

    if not hooks:
        enqueue(topic, payload_json, webhook_id=None)
        return 0

    for w in hooks:
        enqueue(topic, payload_json, webhook_id=w.id)
    return len(hooks)
