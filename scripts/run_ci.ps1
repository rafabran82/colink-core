# scripts/run_ci.ps1
[CmdletBinding()] param(
  [string]$Python = "python",
  [string]$Out = ".artifacts",
  [switch]$NoTests,
  [switch]$NoPlot
)
$ErrorActionPreference = "Stop"
$repo = (git rev-parse --show-toplevel); Set-Location $repo
$ci   = Join-Path $repo "scripts/ci.local.ps1"
$idx  = Join-Path $repo "$Out\index.html"
& pwsh -NoProfile -File $ci -Python $Python -Out $Out @($NoTests ? '-NoTests' : $null) @($NoPlot ? '-NoPlot' : $null)
$code = $LASTEXITCODE
Write-Host ("Local CI exit: {0}" -f $code)
if (Test-Path $idx) { Write-Host "Opening $idx"; Start-Process $idx }
exit $code
