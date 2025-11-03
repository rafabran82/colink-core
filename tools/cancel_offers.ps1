param(
  [string]$Issuer = "rBvZJP5WNGipMyScwFGFmDRAvcaFyn3LBY",
  [switch]$OnlyCOPX,
  [switch]$DryRun,
  [int]$Max = 500,
  [string]$SeedEnv = ""
)
$ErrorActionPreference = "Stop"
if (-not $env:XRPL_RPC) { $env:XRPL_RPC = "https://s.altnet.rippletest.net:51234" }

$py = Join-Path $PSScriptRoot "..\phase2\xrpl\cancel_all_offers.py"
if (-not (Test-Path $py)) { throw "Missing $py" }

$common = @()
if ($SeedEnv) { $common += @("--seed-env", $SeedEnv) }
$common += @("--max", "$Max")

if ($OnlyCOPX) {
  $args = @("--issuer", $Issuer, "--only-currency", "COPX") + $common
} else {
  $args = $common
}

if ($DryRun) { $args += "--dry-run" }

python $py @args
