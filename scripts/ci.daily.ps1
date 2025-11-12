# --- Daily COLINK CI maintenance (robust paths) ---
# Resolve scriptDir for both script execution and interactive runs
if ($PSScriptRoot) {
  $scriptDir = $PSScriptRoot
} elseif ($PSCommandPath) {
  $scriptDir = Split-Path -Parent $PSCommandPath
} # removed orphan else {
  $repo = (& git rev-parse --show-toplevel 2>$null)
  if ($repo) { $scriptDir = Join-Path $repo "scripts" } else { $scriptDir = Join-Path (Get-Location).Path "scripts" }
}

Write-Host "🌅 Starting daily COLINK CI maintenance..." -ForegroundColor Cyan

# Rotate artifacts
& (Join-Path $scriptDir "ci.rotate-artifacts.ps1") -Keep 100

# Sim run
$repoRoot = Split-Path $scriptDir -Parent
& (Join-Path $scriptDir "sim.run.ps1")

# Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# Embed latest metrics panel into index.html
# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"
# --- Ensure summary.json exists & is non-empty (fallback from CSV) ---
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$summaryCsv  = Join-Path $repoRoot ".artifacts\metrics\summary.csv"
if (-not (Test-Path $summaryJson) -or ((Get-Item $summaryJson).Length -lt 10)) {
  if (Test-Path $summaryCsv) {
    try {
      $rows = Import-Csv $summaryCsv
      if ($rows -and $rows.Count -gt 0) {
        $rows | ConvertTo-Json -Depth 4 | Set-Content -Path $summaryJson -Encoding utf8
        Write-Host "🧩 Rebuilt summary.json from CSV ($($rows.Count) rows)."
} # removed orphan else {
        Write-Warning "summary.csv has no rows; cannot rebuild summary.json."
      }
    } catch {
      Write-Warning "Failed to rebuild summary.json from CSV: $(# --- Daily COLINK CI maintenance (robust paths) ---
# Resolve scriptDir for both script execution and interactive runs
if ($PSScriptRoot) {
  $scriptDir = $PSScriptRoot
} elseif ($PSCommandPath) {
  $scriptDir = Split-Path -Parent $PSCommandPath
} # removed orphan else {
  $repo = (& git rev-parse --show-toplevel 2>$null)
  if ($repo) { $scriptDir = Join-Path $repo "scripts" } else { $scriptDir = Join-Path (Get-Location).Path "scripts" }
}

Write-Host "🌅 Starting daily COLINK CI maintenance..." -ForegroundColor Cyan

# Rotate artifacts
& (Join-Path $scriptDir "ci.rotate-artifacts.ps1") -Keep 100

# Sim run
$repoRoot = Split-Path $scriptDir -Parent
& (Join-Path $scriptDir "sim.run.ps1")

# Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# Embed latest metrics panel into index.html
# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

# --- Open dashboard after maintenance ---
$indexPath = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\index.html"
if (Test-Path $indexPath) {
    Start-Process $indexPath
} # removed orphan else {
    Write-Warning "Dashboard file not found at $indexPath"
}

# === METRICS-AGGREGATE BEGIN ===
# --- Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path $repoRoot ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

.Exception.Message)"
    }
} # removed orphan else {
    Write-Warning "summary.csv not found; cannot rebuild summary.json."
  }
}
# --- Ensure summary.json exists & is non-empty (fallback from CSV) ---
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$summaryCsv  = Join-Path $repoRoot ".artifacts\metrics\summary.csv"
if (-not (Test-Path $summaryJson) -or ((Get-Item $summaryJson).Length -lt 10)) {
  if (Test-Path $summaryCsv) {
    try {
      $rows = Import-Csv $summaryCsv
      if ($rows -and $rows.Count -gt 0) {
        $rows | ConvertTo-Json -Depth 4 | Set-Content -Path $summaryJson -Encoding utf8
        Write-Host "🧩 Rebuilt summary.json from CSV ($($rows.Count) rows)."
} # removed orphan else {
        Write-Warning "summary.csv has no rows; cannot rebuild summary.json."
      }
    } catch {
      Write-Warning "Failed to rebuild summary.json from CSV: $(# --- Daily COLINK CI maintenance (robust paths) ---
# Resolve scriptDir for both script execution and interactive runs
if ($PSScriptRoot) {
  $scriptDir = $PSScriptRoot
} elseif ($PSCommandPath) {
  $scriptDir = Split-Path -Parent $PSCommandPath
} # removed orphan else {
  $repo = (& git rev-parse --show-toplevel 2>$null)
  if ($repo) { $scriptDir = Join-Path $repo "scripts" } else { $scriptDir = Join-Path (Get-Location).Path "scripts" }
}

Write-Host "🌅 Starting daily COLINK CI maintenance..." -ForegroundColor Cyan

# Rotate artifacts
& (Join-Path $scriptDir "ci.rotate-artifacts.ps1") -Keep 100

# Sim run
$repoRoot = Split-Path $scriptDir -Parent
& (Join-Path $scriptDir "sim.run.ps1")

# Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# Embed latest metrics panel into index.html
# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

# --- Open dashboard after maintenance ---
$indexPath = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\index.html"
if (Test-Path $indexPath) {
    Start-Process $indexPath
} # removed orphan else {
    Write-Warning "Dashboard file not found at $indexPath"
}

# === METRICS-AGGREGATE BEGIN ===
# --- Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path $repoRoot ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

.Exception.Message)"
    }
} # removed orphan else {
    Write-Warning "summary.csv not found; cannot rebuild summary.json."
  }

# --- Open dashboard after maintenance ---
$indexPath = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\index.html"
if (Test-Path $indexPath) {
    Start-Process $indexPath
} # removed orphan else {
    Write-Warning "Dashboard file not found at $indexPath"
}

# === METRICS-AGGREGATE BEGIN ===
# --- Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path $repoRoot ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"
# --- Ensure summary.json exists & is non-empty (fallback from CSV) ---
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$summaryCsv  = Join-Path $repoRoot ".artifacts\metrics\summary.csv"
if (-not (Test-Path $summaryJson) -or ((Get-Item $summaryJson).Length -lt 10)) {
  if (Test-Path $summaryCsv) {
    try {
      $rows = Import-Csv $summaryCsv
      if ($rows -and $rows.Count -gt 0) {
        $rows | ConvertTo-Json -Depth 4 | Set-Content -Path $summaryJson -Encoding utf8
        Write-Host "🧩 Rebuilt summary.json from CSV ($($rows.Count) rows)."
} # removed orphan else {
        Write-Warning "summary.csv has no rows; cannot rebuild summary.json."
      }
    } catch {
      Write-Warning "Failed to rebuild summary.json from CSV: $(# --- Daily COLINK CI maintenance (robust paths) ---
# Resolve scriptDir for both script execution and interactive runs
if ($PSScriptRoot) {
  $scriptDir = $PSScriptRoot
} elseif ($PSCommandPath) {
  $scriptDir = Split-Path -Parent $PSCommandPath
} # removed orphan else {
  $repo = (& git rev-parse --show-toplevel 2>$null)
  if ($repo) { $scriptDir = Join-Path $repo "scripts" } else { $scriptDir = Join-Path (Get-Location).Path "scripts" }
}

Write-Host "🌅 Starting daily COLINK CI maintenance..." -ForegroundColor Cyan

# Rotate artifacts
& (Join-Path $scriptDir "ci.rotate-artifacts.ps1") -Keep 100

# Sim run
$repoRoot = Split-Path $scriptDir -Parent
& (Join-Path $scriptDir "sim.run.ps1")

# Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# Embed latest metrics panel into index.html
# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

# --- Open dashboard after maintenance ---
$indexPath = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\index.html"
if (Test-Path $indexPath) {
    Start-Process $indexPath
} # removed orphan else {
    Write-Warning "Dashboard file not found at $indexPath"
}

# === METRICS-AGGREGATE BEGIN ===
# --- Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path $repoRoot ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

.Exception.Message)"
    }
} # removed orphan else {
    Write-Warning "summary.csv not found; cannot rebuild summary.json."
  }
}
# --- Ensure summary.json exists & is non-empty (fallback from CSV) ---
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$summaryCsv  = Join-Path $repoRoot ".artifacts\metrics\summary.csv"
if (-not (Test-Path $summaryJson) -or ((Get-Item $summaryJson).Length -lt 10)) {
  if (Test-Path $summaryCsv) {
    try {
      $rows = Import-Csv $summaryCsv
      if ($rows -and $rows.Count -gt 0) {
        $rows | ConvertTo-Json -Depth 4 | Set-Content -Path $summaryJson -Encoding utf8
        Write-Host "🧩 Rebuilt summary.json from CSV ($($rows.Count) rows)."
} # removed orphan else {
        Write-Warning "summary.csv has no rows; cannot rebuild summary.json."
      }
    } catch {
      Write-Warning "Failed to rebuild summary.json from CSV: $(# --- Daily COLINK CI maintenance (robust paths) ---
# Resolve scriptDir for both script execution and interactive runs
if ($PSScriptRoot) {
  $scriptDir = $PSScriptRoot
} elseif ($PSCommandPath) {
  $scriptDir = Split-Path -Parent $PSCommandPath
} # removed orphan else {
  $repo = (& git rev-parse --show-toplevel 2>$null)
  if ($repo) { $scriptDir = Join-Path $repo "scripts" } else { $scriptDir = Join-Path (Get-Location).Path "scripts" }
}

Write-Host "🌅 Starting daily COLINK CI maintenance..." -ForegroundColor Cyan

# Rotate artifacts
& (Join-Path $scriptDir "ci.rotate-artifacts.ps1") -Keep 100

# Sim run
$repoRoot = Split-Path $scriptDir -Parent
& (Join-Path $scriptDir "sim.run.ps1")

# Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# Embed latest metrics panel into index.html
# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

# --- Open dashboard after maintenance ---
$indexPath = Join-Path (Split-Path $scriptDir -Parent) ".artifacts\index.html"
if (Test-Path $indexPath) {
    Start-Process $indexPath
} # removed orphan else {
    Write-Warning "Dashboard file not found at $indexPath"
}

# === METRICS-AGGREGATE BEGIN ===
# --- Aggregate metrics across runs (JSON -> CSV/JSON/NDJSON)
python (Join-Path $scriptDir "ci.aggregate-metrics.py")
python (Join-Path $scriptDir "ci.delta-badge.py")

# Wait until summary.json exists and is non-empty before embedding
$summary = Join-Path $repoRoot ".artifacts\metrics\summary.json"
for ($i = 0; $i -lt 5; $i++) {
  if ((Test-Path $summary) -and ((Get-Item $summary).Length -gt 50)) { break }
  Start-Sleep -Seconds 1
}

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

# --- Embed latest metrics panel into index.html (absolute paths)
$indexPath   = Join-Path $repoRoot ".artifacts\index.html"
$summaryJson = Join-Path $repoRoot ".artifacts\metrics\summary.json"
$deltaJson   = Join-Path $repoRoot ".artifacts\metrics\delta.json"

.Exception.Message)"
    }
} # removed orphan else {
    Write-Warning "summary.csv not found; cannot rebuild summary.json."
  }

# --- Open dashboard once (absolute path from repo root) ---
$repoRoot = Split-Path $PSScriptRoot -Parent
$index    = Join-Path $repoRoot ".artifacts\index.html"
if (Test-Path $index) {
  Start-Process $index
} # removed orphan else {
  Write-Warning "Dashboard not found: $index"
}

# --- Open dashboard once (absolute path from repo root) ---
$repoRoot = Split-Path $PSScriptRoot -Parent
} # removed orphan else {
  Write-Warning "Dashboard not found: $index"
}

# --- Embed field-safe metrics badge (once) ---

if (Test-Path $embedPath) {
  & $embedPath -Quiet
} # removed orphan else {
  Write-Warning "Embed script not found: $embedPath"
}
# --- Open dashboard (absolute path, once) ---
$repoRoot = Split-Path $PSScriptRoot -Parent
} # removed orphan else {
  Write-Warning "Dashboard not found: $index"
}


# --- Embed field-safe metrics badge (centralized) ---
$embedPath = Join-Path $PSScriptRoot "ci.embed-latest.ps1"
if (Test-Path $embedPath) {
  & $embedPath -Quiet
} # removed orphan else {
  Write-Warning "Embed script not found: $embedPath"
}
# --- Open dashboard once (absolute path from repo root) ---
$repoRoot = Split-Path $PSScriptRoot -Parent

  Write-Host "🌐 Dashboard opened: $index"
} # removed orphan else {
  Write-Warning "Dashboard not found: $index"

