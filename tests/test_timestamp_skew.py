import json, os, time, pytest
from httpx import AsyncClient
from main import app

def _sign(secret, body_json, ts=None):
    import hmac, hashlib, time as _t
    if ts is None: ts = int(_t.time())
    sig = hmac.new(secret.encode(), f"{ts}.{body_json}".encode(), hashlib.sha256).hexdigest()
    return {"X-Timestamp": str(ts), "X-Signature": sig, "Content-Type": "application/json"}

@pytest.mark.asyncio
async def test_skew_enforced():
    secret = os.getenv("XRPAY_HMAC_SECRET", "dev_secret_change_me")
    j = json.dumps({"base":"XRP","quote":"USD","amount":1}, separators=(",",":"))
    key = "skew-key"

    async with AsyncClient(app=app, base_url="http://test") as c:
        # Past
        h = _sign(secret, j, ts=int(time.time()) - 10000); h.update({"Idempotency-Key":key,"Idempotency-TTL":"3"})
        r = await c.post("/quotes", headers=h, content=j); assert r.status_code == 401

        # Future
        h = _sign(secret, j, ts=int(time.time()) + 10000); h.update({"Idempotency-Key":key,"Idempotency-TTL":"3"})
        r = await c.post("/quotes", headers=h, content=j); assert r.status_code == 401

        # Fresh
        h = _sign(secret, j); h.update({"Idempotency-Key":key,"Idempotency-TTL":"3"})
        r = await c.post("/quotes", headers=h, content=j); assert r.status_code == 200
