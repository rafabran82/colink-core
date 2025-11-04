import os, time, json, hmac, hashlib, sqlite3, requests

BASE = os.environ.get("XR_BASE_URL", "http://127.0.0.1:8010")
SECRET = os.environ.get("XRPAY_HMAC_SECRET", "devsecret")  # override in env for real runs

def sign_headers(secret: str, body_json: str):
    ts = str(int(time.time()))
    msg = f"{ts}.{body_json}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return {"X-Timestamp": ts, "X-Signature": sig, "Content-Type": "application/json"}

def seed_paper():
    payload = {
        "base": "XRP", "quote": "USD",
        "mid": 0.5, "spreadBps": 20,
        "levels": 5, "depthPerLevel": 1000
    }
    r = requests.post(f"{BASE}/_paper/seed", json=payload, timeout=5)
    assert r.status_code == 200

def test_quotes_idempotency_flow():
    seed_paper()

    body = {"base":"XRP","quote":"USD","side":"BUY","amount":3,"slippageBps":50}
    body_json = json.dumps(body, separators=(",",":"))
    hdr = sign_headers(SECRET, body_json)
    idk = os.urandom(12).hex()
    hdr["Idempotency-Key"] = idk
    hdr["Idempotency-TTL"] = "5"

    # MISS
    r1 = requests.post(f"{BASE}/quotes", data=body_json, headers=hdr, timeout=5)
    assert r1.status_code == 200
    assert r1.headers.get("X-Idempotency-Cache") == "miss"

    # HIT (same key+body)
    r2 = requests.post(f"{BASE}/quotes", data=body_json, headers=hdr, timeout=5)
    assert r2.status_code == 200
    assert r2.headers.get("X-Idempotency-Cache") == "hit"

    # CONFLICT (same key, different body)
    body2 = dict(body, amount=4)
    body2_json = json.dumps(body2, separators=(",",":"))
    hdr2 = sign_headers(SECRET, body2_json)
    hdr2["Idempotency-Key"] = idk
    hdr2["Idempotency-TTL"] = "5"

    r3 = requests.post(f"{BASE}/quotes", data=body2_json, headers=hdr2, timeout=5)
    assert r3.status_code == 409
    assert r3.headers.get("X-Idempotency-Conflict") == "body-mismatch"

def test_db_row_defaults_ok():
    # peek latest row
    con = sqlite3.connect("xrpay.db")
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM quotes ORDER BY created_at DESC LIMIT 1").fetchone()
    con.close()

    assert row is not None
    # id should be INTEGER autoincrement (shows up as int via sqlite3)
    assert isinstance(row["id"], int)
    # status should have defaulted
    assert row["status"] == "VALID"
    # terms_hash nullable
    assert row["terms_hash"] is None
