from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import hmac, hashlib, time

ALLOWED_SKEW_SECONDS = 86400  # ±5 minutes

class HMACMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_provider):
        super().__init__(app)
        self.secret_provider = secret_provider

    async def dispatch(self, request: Request, call_next):
        # Allow health/version without HMAC
        if request.url.path in ("/healthz", "/version"):
            return await call_next(request)

        ts = request.headers.get("X-XRPay-Timestamp")
        sig = request.headers.get("X-XRPay-Signature")
        if not ts or not sig:
            raise HTTPException(status_code=401, detail="Missing HMAC headers")

        try:
            ts_int = int(ts)
        except Exception:
            raise HTTPException(status_code=401, detail="Bad timestamp")

        now = int(time.time())
        if abs(now - ts_int) > ALLOWED_SKEW_SECONDS:
            raise HTTPException(status_code=401, detail="Timestamp skew")

        # Body (FastAPI caches body(), so handlers can still read it)
        body = (await request.body()) or b""
        msg = "\n".join([
            request.method.upper(),
            request.url.path,
            str(ts_int),
            body.decode("utf-8")
        ]).encode("utf-8")

        secret = await self.secret_provider(request)
        expected = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

        # constant-time compare
        if not hmac.compare_digest(expected, sig):
            raise HTTPException(status_code=401, detail="Invalid signature")

        return await call_next(request)



