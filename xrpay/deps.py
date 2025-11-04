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
