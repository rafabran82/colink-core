# Idempotent Requests in COLINK Core

## Headers
- `Idempotency-Key` (required for POSTs that should be replay-safe)
- `X-Timestamp` (epoch seconds; ±120s skew allowed)
- `X-Signature` (HMAC SHA-256 of `${timestamp}.${body_json}` using server secret)

## Behavior
- First request with a new key → **MISS**; response adds `X-Idempotency-Cache: miss`.
- Retries with same key and same body → **HIT**; response adds `X-Idempotency-Cache: hit`.
- Same key **different body** → **409** with `X-Idempotency-Conflict: body-mismatch`.
- **5xx** responses are **never cached**.
- TTL default: `XR_IDEMPOTENCY_TTL` (sec, default 300). Clients should retry safely within TTL.

## Tenant Scoping
Set `XR_IDEMPOTENCY_TENANT_HEADER` (e.g. `X-Account-ID`) to scope keys per tenant.  
Cache key format includes `<TenantHeader>:<Value>` when present.

## Backends
- Memory (default)
- Redis: set `XR_IDEMPOTENCY_BACKEND=redis` and `REDIS_URL`.

## Metrics (Prometheus)
- `/metrics` endpoint (text format)
- Counters: `xrpay_idem_requests_total`, `xrpay_idem_cache_miss_total`, `xrpay_idem_cache_hit_total`, `xrpay_idem_conflict_total`, `xrpay_idem_5xx_total`
- Histogram: `xrpay_idem_latency_seconds{cache="miss|hit|none"}`

## Client Guidance
- Generate a strong unique `Idempotency-Key` per logical operation.
- Keep timestamp fresh (±120s). Sync clocks (NTP).
- Reuse the same key **only** for the same request body.
- Retry on network errors / 5xx; server won’t cache 5xx.
