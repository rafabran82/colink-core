# colink_core/sim â€” COPX AMM Router + Guards

This module simulates a two-hop route COL -> XRP -> COPX on a constant-product AMM,
with LP shares & fee splits, a min-out slippage guard, a size-aware TWAP guard,
and a trade limiter + circuit breaker.

## Quick start

# From repo root
python -m colink_core.sim quote --col-in 8000 --min-out-bps 150 --twap-guard
python -m colink_core.sim exec  --col-in 8000
python -m colink_core.sim sweep

The sweep writes a timestamped CSV and charts to colink_core/sim/out/.

## CLI options
- quote
  --col-in <float> : COL size to route
  --min-out-bps <float> : min-out tolerance in bps (optional)
  --twap-guard : enable size-aware TWAP guard (optional)
  Guard tuning: --twap-window, --base-bps, --cushion-bps, --cap-bps

- exec
  --col-in <float> : executes COL->XRP->COPX and shows new pool prices

- sweep
  --sizes <list> : space-separated COL sizes (default: 100 ... 50000)
  same guard tuning flags as quote
  --outdir <path> : where CSV/charts are written (default: sim/out/)

## Run just the sim tests
pwsh -NoProfile -Command "Set-Location colink_core/sim; pytest -q"

All tests should pass (14/14).
