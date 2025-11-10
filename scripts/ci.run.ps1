param([switch]$Publish,[string]$OutDir=".artifacts",[switch]$Wait)
$ErrorActionPreference='Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = (git -C (Resolve-Path $Here).Path rev-parse --show-toplevel)
$script = Join-Path $root "scripts/ci.local.ps1"
if (-not (Test-Path $script)) { throw "Missing $script" }
& pwsh -NoProfile -ExecutionPolicy Bypass -WorkingDirectory $root -File $script @PSBoundParameters
exit $LASTEXITCODE