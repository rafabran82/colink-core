import json, os, asyncio, pytest
from httpx import AsyncClient
from main import app

def _sign(secret:str, body_json:str):
    import hmac, hashlib, time
    ts = str(int(time.time()))
    sig = hmac.new(secret.encode(), f"{ts}.{body_json}".encode(), hashlib.sha256).hexdigest()
    return {"X-Timestamp": ts, "X-Signature": sig, "Content-Type": "application/json"}

@pytest.mark.asyncio
async def test_no_cache_on_5xx(monkeypatch):
    secret = os.getenv("XRPAY_HMAC_SECRET", "dev_secret_change_me")
    body = {"base":"XRP","quote":"USD","amount":999}
    j = json.dumps(body, separators=(",",":"))
    h = _sign(secret, j); h["Idempotency-Key"]="fail-key"; h["Idempotency-TTL"]="3"

    # Monkeypatch the handler to raise once
    from xrpay.routes.quotes import create_quote as real
    called = {"n":0}
    async def boom(*args, **kwargs):
        if called["n"]==0:
            called["n"]+=1
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail="boom")
        return await real(*args, **kwargs)
    import xrpay.routes.quotes as mod
    orig = mod.create_quote
    mod.create_quote = boom
    try:
        async with AsyncClient(app=app, base_url="http://test") as c:
            r1 = await c.post("/quotes", headers=h, content=j)
            assert r1.status_code == 500
            # Retry: should NOT be served from cache (should recompute and succeed)
            mod.create_quote = orig
            r2 = await c.post("/quotes", headers=h, content=j)
            assert r2.status_code == 200
            assert r2.headers.get("X-Idempotency-Cache") == "miss"
    finally:
        mod.create_quote = orig

@pytest.mark.asyncio
async def test_tenant_scoped_keys():
    secret = os.getenv("XRPAY_HMAC_SECRET", "dev_secret_change_me")
    body = {"base":"XRP","quote":"USD","amount":7}
    j = json.dumps(body, separators=(",",":"))
    key = "same-key"
    async with AsyncClient(app=app, base_url="http://test") as c:
        # Tenant A
        hA = _sign(secret, j); hA.update({"Idempotency-Key":key,"Idempotency-TTL":"5","X-Account-ID":"A"})
        r1 = await c.post("/quotes", headers=hA, content=j); assert r1.headers.get("X-Idempotency-Cache")=="miss"
        r2 = await c.post("/quotes", headers=hA, content=j); assert r2.headers.get("X-Idempotency-Cache")=="hit"

        # Tenant B — same key, should be independent (MISS)
        hB = _sign(secret, j); hB.update({"Idempotency-Key":key,"Idempotency-TTL":"5","X-Account-ID":"B"})
        r3 = await c.post("/quotes", headers=hB, content=j); assert r3.headers.get("X-Idempotency-Cache")=="miss"
