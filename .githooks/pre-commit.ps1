# Stop on errors
$ErrorActionPreference = "Stop"

# Get staged files under .artifacts/
$staged = git diff --cached --name-only -- .artifacts/ | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }

if (-not $staged) { exit 0 }

# Allowed patterns (regex)
$allowed = @(
  '^\Q.artifacts/.gitkeep\E$',
  '^\Q.artifacts/index.html\E$',
  '^\Q.artifacts/ci/.gitkeep\E$',
  '^\Q.artifacts/ci/ci_summary.json\E$',
  '^\Q.artifacts/metrics/.gitkeep\E$',
  '^\Q.artifacts/plots/.gitkeep\E$',
  '^\Q.artifacts/data/.gitkeep\E$',
  '^\Q.artifacts/bundles/.gitkeep\E$'
)

$bad = @()
foreach ($f in $staged) {
  $ok = $false
  foreach ($rx in $allowed) {
    if ($f -match $rx) { $ok = $true; break }
  }
  if (-not $ok) { $bad += $f }
}

if ($bad.Count -gt 0) {
  Write-Host "ERROR: You staged non-allowlisted files in .artifacts/:" -ForegroundColor Red
  $bad | ForEach-Object { Write-Host "  - $($_)" }
  Write-Host "Only index.html, ci/ci_summary.json, and .gitkeep files are allowed."
  exit 1
}

exit 0
