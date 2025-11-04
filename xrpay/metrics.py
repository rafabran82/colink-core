from prometheus_client import Counter, Histogram

# Core idempotency metrics
IDEM_REQUESTS_TOTAL = Counter(
    "xrpay_idem_requests_total",
    "Total idempotent-handled requests",
    ["method", "path"],
)

IDEM_CACHE_MISS_TOTAL = Counter(
    "xrpay_idem_cache_miss_total",
    "Idempotency cache misses",
    ["method", "path"],
)

IDEM_CACHE_HIT_TOTAL = Counter(
    "xrpay_idem_cache_hit_total",
    "Idempotency cache hits",
    ["method", "path"],
)

IDEM_CONFLICT_TOTAL = Counter(
    "xrpay_idem_conflict_total",
    "Idempotency conflicts (same key, different body)",
    ["method", "path"],
)

IDEM_5XX_TOTAL = Counter(
    "xrpay_idem_5xx_total",
    "Responses with 5xx (never cached)",
    ["method", "path"],
)

IDEM_LATENCY_SECONDS = Histogram(
    "xrpay_idem_latency_seconds",
    "Latency of requests through idempotency middleware",
    ["method", "path", "cache"],  # cache: "miss" | "hit" | "none"
    buckets=(0.005,0.01,0.02,0.05,0.1,0.25,0.5,1,2,5,10),
)
