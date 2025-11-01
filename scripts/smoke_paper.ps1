# Paper mode smoke: clear, seed, buy, sell, then show book/position
Invoke-RestMethod -Method POST http://127.0.0.1:8011/_paper/clear | Out-Null
Invoke-RestMethod -Method POST http://127.0.0.1:8011/_paper/position/reset | Out-Null

Invoke-RestMethod -Method POST http://127.0.0.1:8011/seed-book -ContentType "application/json" `
  -Body (@{ mid_price_xrp_per_col="0.10"; steps=0; step_pct="0.05"; base_size_col="5"; size_scale="1.0" } | ConvertTo-Json) | Out-Null

Invoke-RestMethod -Method POST http://127.0.0.1:8011/market-buy  -ContentType "application/json" `
  -Body (@{ amount_col="3" } | ConvertTo-Json) | Out-Null

Invoke-RestMethod -Method POST http://127.0.0.1:8011/market-sell -ContentType "application/json" `
  -Body (@{ amount_col="2" } | ConvertTo-Json) | Out-Null

"--- BOOK ---"
Invoke-RestMethod http://127.0.0.1:8011/_paper/book | ConvertTo-Json -Depth 8
"--- POSITION ---"
Invoke-RestMethod http://127.0.0.1:8011/_paper/position | ConvertTo-Json -Depth 6
