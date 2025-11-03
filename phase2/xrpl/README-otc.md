# OTC Scripts – Quick Use

## One trade + receipt
otc 250 0.004 0.02

## See newest *rich* receipt
powershell -ExecutionPolicy Bypass -File .\phase2\xrpl\otc_last_rich.ps1

## Verify newest receipt (PASS/FAIL)
powershell -ExecutionPolicy Bypass -File .\phase2\xrpl\otc_check_last.ps1

## Daily summary (balances + last rich receipt + CSV)
otcd

## Batch from CSV
# file headers: qty_copx,price_xrp,slippage
otcb .\phase2\xrpl\otc_batch_input.csv
