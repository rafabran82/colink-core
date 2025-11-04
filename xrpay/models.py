from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Numeric, Enum, UniqueConstraint, LargeBinary
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .db import Base

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    body_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    media_type: Mapped[str] = mapped_column(String(64), default="application/json")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Webhook(Base):
    __tablename__ = "webhooks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")

class Outbox(Base):
    __tablename__ = "outbox"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    retries: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    webhook_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("webhooks.id"), nullable=True)
    webhook: Mapped["Webhook"] = relationship("Webhook")

class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    base: Mapped[str] = mapped_column(String(16))
    quote: Mapped[str] = mapped_column(String(16))
    side: Mapped[str] = mapped_column(String(8))
    amount: Mapped[str] = mapped_column(String(64))
    price: Mapped[str] = mapped_column(String(64))
    fee_bps: Mapped[int] = mapped_column(Integer, default=25)
    impact_bps: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime)

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    currency: Mapped[str] = mapped_column(String(16))
    amount: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="OPEN")
    paid_amount: Mapped[str] = mapped_column(String(64), default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PaymentIntent(Base):
    __tablename__ = "payment_intents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"))
    payment_currency: Mapped[str] = mapped_column(String(16))
    quote_id: Mapped[str | None] = mapped_column(String(36))
    quote_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="CREATED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



