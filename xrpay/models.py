from __future__ import annotations
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
import uuid
from .db import Base
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Numeric, Enum, UniqueConstraint, LargeBinary

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, default="OPEN")
    currency: Mapped[str] = mapped_column(String, nullable=True)
    amount: Mapped[str] = mapped_column(String, nullable=True)
    paid_amount: Mapped[str] = mapped_column(String, default="0")
    description: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    # UUID primary key generated client-side so SQLite is happy
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)

    status = Column(String, nullable=False, default="CREATED")

    # relationships
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    payment_currency = Column(String, nullable=False)

    # quote lock fields (nullable until /confirm)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=True)
    locked_price = Column(Float, nullable=True)
    fee_bps = Column(Integer, nullable=True)
    impact_bps = Column(Integer, nullable=True)
    expires_at = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    base: Mapped[str] = mapped_column(String)
    quote: Mapped[str] = mapped_column(String)
    side: Mapped[str] = mapped_column(String)
    amount: Mapped[str] = mapped_column(String)
    price: Mapped[str] = mapped_column(String)              # decimal string
    fee_bps: Mapped[int] = mapped_column(Integer, default=25)
    impact_bps: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[int] = mapped_column(Integer)        # unix ts
    status: Mapped[str] = mapped_column(String, default="VALID")  # VALID | EXPIRED | USED
    terms_hash: Mapped[str] = mapped_column(String, index=True)   # hash of request terms
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Outbox(Base):
    __tablename__ = "outbox"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String)
    payload_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    retries: Mapped[int] = mapped_column(Integer, default=0)
    webhook_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("webhooks.id"), nullable=True)
    webhook = relationship("Webhook")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Webhook(Base):
    __tablename__ = "webhooks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String)
    secret: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    method: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(String)
    body_digest: Mapped[str] = mapped_column(String)
    status_code: Mapped[int] = mapped_column(Integer)
    headers_json: Mapped[str] = mapped_column(Text)
    body_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)













