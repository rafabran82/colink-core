from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import hashlib, json, asyncio

class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Requires Idempotency-Key on mutating requests.
    Stores fingerprint (method+path+body) and full response for 24h.
    Store must implement: get(key) -> dict|None, set(key, dict, ttl: int)
    """

    def __init__(self, app, store, ttl_seconds: int = 24*3600):
        super().__init__(app)
        self.store = store
        self.ttl = ttl_seconds

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            key = request.headers.get("Idempotency-Key")
            if not key:
                raise HTTPException(status_code=400, detail="Missing Idempotency-Key")

            body_bytes = (await request.body()) or b""
            fingerprint = hashlib.sha256(
                (request.method + request.url.path + body_bytes.decode("utf-8")).encode("utf-8")
            ).hexdigest()

            cached = await self.store.get(key)
            if cached:
                if cached["fingerprint"] != fingerprint:
                    raise HTTPException(status_code=409, detail="Idempotency-Key conflict")
                # Replay cached response
                return Response(
                    content=cached["body_bytes"],
                    status_code=cached["status"],
                    media_type=cached.get("media_type") or "application/json"
                )

            # No cache: call downstream and capture response bytes
            response = await call_next(request)
            # capture: read body from response.body_iterator (may be streaming)
            body_collector = b""
            if hasattr(response, "body_iterator") and response.body_iterator is not None:
                async for chunk in response.body_iterator:
                    body_collector += chunk
            else:
                # Fallback for non-streaming responses
                try:
                    body_collector = response.body
                except Exception:
                    body_collector = b""

            # Rebuild response so client still gets content
            out = Response(
                content=body_collector,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

            await self.store.set(key, {
                "fingerprint": fingerprint,
                "status": response.status_code,
                "body_bytes": body_collector,
                "media_type": response.media_type or "application/json"
            }, ttl=self.ttl)

            return out

        # Non-mutating request → passthrough
        return await call_next(request)

