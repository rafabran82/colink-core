$ErrorActionPreference = "Stop"

# --- logging (optional) ---
try {
  $logFile = Join-Path (git rev-parse --git-dir) "pre-commit.log"
  function Log($m){ Add-Content -Path $logFile -Value ("[{0}] {1}" -f (Get-Date -Format s), $m) }
  Log "== pre-commit start =="
} catch { }

# 1) Gather staged changes under .artifacts/, WITH status codes
#    We only enforce on A/M/R/T/etc. and skip D(Deleted) to allow cleanup.
$lines = git diff --cached --name-status -- .artifacts/ `
  | ForEach-Object { $_.Trim() } | Where-Object { $_ }

try { Log ("staged (name-status): " + ($lines -join " | ")) } catch {}

$changed = @()
foreach ($ln in $lines) {
  if ($ln -match '^(?<code>[AMRTCU])\s+(?<path>.+)$') {
    $changed += $Matches['path']
  }
}
if (-not $changed) { try { Log "no A/M/R/T/C/U under .artifacts/; OK" } catch {}; exit 0 }

# 2) Literal allow-list (exact paths as Git sees them — forward slashes)
$allowed = @(
  '.artifacts/.gitkeep',
  '.artifacts/index.html',
  '.artifacts/ci/.gitkeep',
  '.artifacts/ci/ci_summary.json',
  '.artifacts/metrics/.gitkeep',
  '.artifacts/plots/.gitkeep',
  '.artifacts/data/.gitkeep',
  '.artifacts/bundles/.gitkeep'
)

# 3) Anything not exactly in the allow-list is blocked
$bad = $changed | Where-Object { $_ -notin $allowed }

if ($bad.Count -gt 0) {
  try { Log ("BLOCK: " + ($bad -join ', ')) } catch {}
  Write-Host "ERROR: You staged non-allowlisted files in .artifacts/:" -ForegroundColor Red
  $bad | ForEach-Object { Write-Host "  - $_" }
  Write-Host "Only index.html, ci/ci_summary.json, and .gitkeep files are allowed." -ForegroundColor Yellow
  exit 1
}

try { Log "allow: only allowlisted artifacts staged; OK" } catch {}
exit 0
