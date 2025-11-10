# Sim Smoke artifacts – quick use

## Latest successful on main
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\collect-smoke.ps1 -Ref main -LatestSuccessful

## Specific run id
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\collect-smoke.ps1 -RunId 19165305038

### Outputs
- artifacts-<runId>\… (unzipped, one folder per job)
- artifacts-<runId>\_combined\smoke_matrix.csv|json
- artifacts-<runId>-zip\*.zip (one zip per job + _combined.zip)
- artifacts-<runId>-ALL.zip (entire bundle)
