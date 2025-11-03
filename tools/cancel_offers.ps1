param(
  [string]$Issuer = "rBvZJP5WNGipMyScwFGFmDRAvcaFyn3LBY",
  [switch]$OnlyCOPX,
  [switch]$DryRun,
  [int]$Max = 500,
  [string]$SeedEnv = "",
  [switch]$NoWait
)
$ErrorActionPreference = "Stop"
if (-not $env:XRPL_RPC) { $env:XRPL_RPC = "https://s.altnet.rippletest.net:51234" }

$py = Join-Path $PSScriptRoot "..\phase2\xrpl\cancel_all_offers.py"
if (-not (Test-Path $py)) { throw "Missing $py" }

$args = @()
if ($SeedEnv) { $args += @("--seed-env", $SeedEnv) }
$args += @("--max", "$Max")
if ($OnlyCOPX) { $args += @("--issuer", $Issuer, "--only-currency", "COPX") }
if ($DryRun)   { $args += "--dry-run" }
if ($NoWait)   { $args += "--no-wait" }

python $py @args
