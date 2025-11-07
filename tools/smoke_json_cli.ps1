param(
  [string]$OutDir = "charts",
  [int]$Paths = 5,
  [int]$Steps = 10
)

$ErrorActionPreference = "Stop"

Write-Host ">> json_cli --help"
python -m colink_core.sim.json_cli --help | Out-Null

Write-Host ">> json_cli quote"
$quote = python -m colink_core.sim.json_cli quote --col-in 100 --min-out-bps 5
if (-not $quote) { throw "quote produced no output" }

Write-Host ">> json_cli sweep"
$sweep = python -m colink_core.sim.json_cli sweep --outdir $OutDir --n-paths $Paths --n-steps $Steps
if (-not $sweep) { throw "sweep produced no output" }

Write-Host ">> pytest -q"
pytest -q | Out-Null

Write-Host "OK: smoke passed"
