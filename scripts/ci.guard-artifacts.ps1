param()
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# repo root
$repo = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $repo) { $repo = (Get-Location).Path }
Set-Location $repo

# allowlist
$allowed = @(
  ".artifacts/index.html",
  ".artifacts/ci/ci_summary.json",
  ".artifacts/ci/ci_badge.json"
)

# tracked files under .artifacts
$all = (& git ls-files -- .artifacts 2>$null) -split "`n" | Where-Object { $_ -ne "" }

$blocked = @()
foreach ($p in $all) {
  if ($p -like "*.gitkeep") { continue }
  if ($allowed -contains $p) { continue }
  $blocked += $p
}

if ($blocked.Count -gt 0) {
  Write-Error ("Guard failed: unexpected tracked files under .artifacts:`n  - " + ($blocked -join "`n  - "))
  exit 1
}

Write-Host "Guard OK: only allowlisted .artifacts files are tracked."
exit 0
