param(
  [string]$Network = "testnet",
  [string]$Out = ".artifacts/data/bootstrap",
  [switch]$Execute,
  [switch]$Verbose
)
$ErrorActionPreference = "Stop"
$py = "scripts/xrpl.testnet.bootstrap.py"
$cmd = @("python", $py, "--network", $Network, "--out", $Out)
if ($Execute) { $cmd += "--execute" }
if ($Verbose) { $cmd += "--verbose" }
Write-Host "▶ $($cmd -join ' ')"
& $cmd
