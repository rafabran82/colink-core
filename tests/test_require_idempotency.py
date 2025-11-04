import json, os, pytest
from httpx import AsyncClient
from main import app

def _sign(secret, body_json):
    import hmac, hashlib, time
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}.{body_json}".encode(), hashlib.sha256).hexdigest()
    return {"X-Timestamp": ts, "X-Signature": sig, "Content-Type": "application/json"}

@pytest.mark.asyncio
async def test_quotes_requires_idempotency_headers():
    secret = os.getenv("XRPAY_HMAC_SECRET", "dev_secret_change_me")
    body = {"base":"XRP","quote":"USD","amount":2}
    j = json.dumps(body, separators=(",",":"))
    h = _sign(secret, j)  # missing Idempotency-Key on purpose
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.post("/quotes", headers=h, content=j)
        assert r.status_code == 422
        assert "Idempotency-Key" in r.text
