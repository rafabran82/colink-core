from fastapi import Request, HTTPException

REQUIRED_HEADERS = [
    ("Idempotency-Key", "Missing Idempotency-Key header."),
    ("X-Timestamp", "Missing X-Timestamp header."),
    ("X-Signature", "Missing X-Signature header."),
]

def require_idempotency_key(request: Request) -> None:
    """
    Validate core headers for idempotent, HMAC-signed POSTs.
    - Idempotency-Key is required so responses can be safely retried.
    - X-Timestamp & X-Signature must be present (actual HMAC check happens in existing auth).
    """
    headers = request.headers
    for name, msg in REQUIRED_HEADERS:
        if not headers.get(name):
            raise HTTPException(status_code=422, detail=msg)
    # Also reject obviously empty keys
    if not headers.get("Idempotency-Key", "").strip():
        raise HTTPException(status_code=422, detail="Idempotency-Key must not be empty.")

import time

def require_fresh_timestamp(request: Request, max_skew_seconds: int = 120) -> None:
    ts = request.headers.get("X-Timestamp")
    if not ts:
        raise HTTPException(status_code=422, detail="Missing X-Timestamp header.")
    try:
        ts_int = int(ts)
    except ValueError:
        raise HTTPException(status_code=422, detail="X-Timestamp must be integer epoch seconds.")
    now = int(time.time())
    if abs(now - ts_int) > max_skew_seconds:
        raise HTTPException(status_code=401, detail="Timestamp outside allowed skew window.")

