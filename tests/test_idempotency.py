import json
import time
import hmac
import hashlib
import os
import pytest
from httpx import AsyncClient
from main import app  # FastAPI instance

def _sign(secret: str, body_json: str) -> dict:
    ts = str(int(time.time()))
    msg = f"{ts}.{body_json}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return {"X-Timestamp": ts, "X-Signature": sig, "Content-Type": "application/json"}

@pytest.mark.asyncio
async def test_idempotency_hit_miss_and_conflict():
    # HMAC secret (fallback to dev default used in local runs)
    secret = os.getenv("XRPAY_HMAC_SECRET", "dev_secret_change_me")
    idem_key = "test-key-123"

    # --- MISS then HIT with the same body ---
    bodyA = {"base": "XRP", "quote": "USD", "amount": 100}
    jA = json.dumps(bodyA, separators=(",", ":"))
    hA = _sign(secret, jA)
    hA["Idempotency-Key"] = idem_key
    hA["Idempotency-TTL"] = "120"

    async with AsyncClient(app=app, base_url="http://test") as c:
        r1 = await c.post("/quotes", headers=hA, content=jA)
        assert r1.status_code == 200
        assert r1.headers.get("X-Idempotency-Cache") == "miss"
        j1 = r1.json()

        r2 = await c.post("/quotes", headers=hA, content=jA)
        assert r2.status_code == 200
        assert r2.headers.get("X-Idempotency-Cache") == "hit"
        assert r2.json() == j1  # identical cached payload

        # --- 409 on same key but different body ---
        bodyB = {"base": "XRP", "quote": "USD", "amount": 101}
        jB = json.dumps(bodyB, separators=(",", ":"))
        hB = _sign(secret, jB)
        hB["Idempotency-Key"] = idem_key  # SAME key intentionally
        hB["Idempotency-TTL"] = "120"

        r3 = await c.post("/quotes", headers=hB, content=jB)
        assert r3.status_code == 409
        assert r3.headers.get("X-Idempotency-Conflict") == "body-mismatch"
        assert "idempotency key reused" in r3.json().get("detail", "").lower()
