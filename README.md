[![CI](https://github.com/rafabran82/colink-core/actions/workflows/ci.yml/badge.svg)](https://github.com/rafabran82/colink-core/actions/workflows/ci.yml)

# COLINK Core — Paper Engine Quickstart

## Run (paper mode)
1) Copy config:
   - `cp .env.example .env` (Windows: `Copy-Item .env.example .env`)
2) Start API:
   - `.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8011`

## Smoke (paper)
```powershell
Invoke-RestMethod -Method POST http://127.0.0.1:8011/_paper/clear | Out-Null
Invoke-RestMethod -Method POST http://127.0.0.1:8011/_paper/position/reset | Out-Null
Invoke-RestMethod -Method POST http://127.0.0.1:8011/seed-book -ContentType "application/json" `
  -Body (@{ mid_price_xrp_per_col="0.10"; steps=0; step_pct="0.05"; base_size_col="5"; size_scale="1.0" } | ConvertTo-Json) | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method POST http://127.0.0.1:8011/market-buy  -ContentType "application/json" `
  -Body (@{ amount_col="3"; max_slippage_pct="0.20"; limit=20 } | ConvertTo-Json) | ConvertTo-Json -Depth 6
Invoke-RestMethod -Method POST http://127.0.0.1:8011/market-sell -ContentType "application/json" `
  -Body (@{ amount_col="2"; max_slippage_pct="0.20"; limit=20 } | ConvertTo-Json) | ConvertTo-Json -Depth 6
Invoke-RestMethod http://127.0.0.1:8011/_paper/book     | ConvertTo-Json -Depth 8
Invoke-RestMethod http://127.0.0.1:8011/_paper/position | ConvertTo-Json -Depth 6
```

## Endpoints (quick reference)
- `GET  /healthz` – liveness
- `GET  /_debug/settings` – runtime config (masked seeds, flags)
- `GET  /orderbook?limit=N` – XRPL orderbook snapshot
- `POST /seed-book` – seed ladder around mid
- `POST /market-buy` – market buy
- `POST /market-sell` – market sell

### Paper admin
- `GET  /_paper/book` – in-memory book
- `POST /_paper/clear` – clear book
- `GET  /_paper/position` – P&L/position
- `POST /_paper/position/reset` – reset P&L/position

## Configuration
Copy `.env.example` to `.env`. Defaults enable **paper mode**:
- `PAPER_MODE=1`
- `ISSUER_ADDR`, `TRADER_ADDR` prefilled for read-only XRPL calls

### Switch to real XRPL testnet
1) `PAPER_MODE=0`
2) Remove `ISSUER_ADDR`/`TRADER_ADDR`
3) Set **funded** `ISSUER_SEED` and `TRADER_SEED`
4) Restart uvicorn

## Troubleshooting
- **400 preflight_failed** → check `/_debug/settings` for missing/invalid addrs or seed errors
- **Invalid checksum** → seed malformed; use fresh testnet faucet seeds
- **No bids/asks** → seed with `/seed-book`

