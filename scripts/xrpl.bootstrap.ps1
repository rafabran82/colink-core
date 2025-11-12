param(
  [string]$Network = "testnet",
  [string]$Out = ".artifacts/data/bootstrap",
  [switch]$Execute,
  [switch]$Verbose
)
$ErrorActionPreference = "Stop"

# Resolve python script relative to this .ps1 file
$py = Join-Path $PSScriptRoot "xrpl.testnet.bootstrap.py"

# Build argv as an array
$cmd = @("python", $py, "--network", $Network, "--out", $Out)
if ($Execute) { $cmd += "--execute" }
if ($Verbose) { $cmd += "--verbose" }

Write-Host "▶ $($cmd -join ' ')"

# PS5-safe array execution: exe + splatted args
$exe  = $cmd[0]
$argv = @()
if ($cmd.Count -gt 1) { $argv = $cmd[1..($cmd.Count-1)] }
& $exe @argv
