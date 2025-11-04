import time, hmac, hashlib, json
from fastapi.testclient import TestClient

from xrpay.main import app

client = TestClient(app)

def _sig(method, path, ts, body, secret="dev_hmac_secret"):
    msg = "\n".join([method, path, str(ts), body]).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

def test_healthz_ok():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_quotes_requires_hmac_and_idempotency():
    now = int(time.time())
    payload = {"base":"XRP","quote":"USD","side":"BUY","amount":"100","slippageBps":50}
    body = json.dumps(payload)
    sig = _sig("POST", "/quotes", now, body)
    r = client.post(
        "/quotes",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-XRPay-Timestamp": str(now),
            "X-XRPay-Signature": sig,
            "Idempotency-Key": "00000000-0000-0000-0000-000000000001"
        }
    )
    assert r.status_code == 200
    assert "price" in r.json()
