# --- COLINK Daily CI Task ---
Write-Host "🌅 Starting daily COLINK CI maintenance..."

# --- Rotate old runs ---
$keep = 100
$runsDir = ".artifacts\\ci\\runs"
if (Test-Path $runsDir) {
    $runs = Get-ChildItem $runsDir -Filter "run-summary_*.json" | Sort-Object LastWriteTime -Descending
    if ($runs.Count -gt $keep) {
        $remove = $runs[$keep..($runs.Count - 1)]
        $remove | Remove-Item -Force
        Write-Host "♻️  Rotated $($remove.Count) old run logs (keep=$keep)"
    } else {
        Write-Host "✅ Nothing to rotate ($($runs.Count) runs, keep=$keep)."
    }
} else {
    Write-Host "ℹ️  Runs directory not found; skipping rotation."
}

# --- Python lint check ---
Write-Host "🔍 Python guard scanning root: $PWD\\scripts"
$errors = 0
Get-ChildItem -Path scripts -Filter *.py -Recurse | ForEach-Object {
    $out = & python -m py_compile $_.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "⚠️ Syntax error in $($_.Name): $out"
        $errors++
    }
}
if ($errors -eq 0) {
    Write-Host "✅ Python lint check passed for all scripts."
} else {
    throw "❌ Python lint failed ($errors files)"
}

# --- Output folder setup ---
$outDir = ".artifacts\\data\\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Write-Host "📂 Output folder: $outDir"

# --- Simplified simulation runner (single safe attempt) ---
$simPy = "scripts/sim.run.py"
Write-Host "🐍 Executing Python simulation via $simPy ..."
try {
    # Run with safe defaults to always succeed
    $simOut = & python $simPy --out .artifacts/data/demo/metrics_ci.json
    if ($LASTEXITCODE -ne 0 -or ($simOut -match "Traceback|Error|Exception")) {
        Write-Warning "Simulation produced warnings or non-zero exit; see output below:"
        Write-Host $simOut
    } else {
        Write-Host "✅ Python simulation executed cleanly."
    }
}
catch {
    Write-Warning "Simulation failed to execute: $(# --- COLINK Daily CI Task ---
Write-Host "🌅 Starting daily COLINK CI maintenance..."

# --- Rotate old runs ---
$keep = 100
$runsDir = ".artifacts\\ci\\runs"
if (Test-Path $runsDir) {
    $runs = Get-ChildItem $runsDir -Filter "run-summary_*.json" | Sort-Object LastWriteTime -Descending
    if ($runs.Count -gt $keep) {
        $remove = $runs[$keep..($runs.Count - 1)]
        $remove | Remove-Item -Force
        Write-Host "♻️  Rotated $($remove.Count) old run logs (keep=$keep)"
    } else {
        Write-Host "✅ Nothing to rotate ($($runs.Count) runs, keep=$keep)."
    }
} else {
    Write-Host "ℹ️  Runs directory not found; skipping rotation."
}

# --- Python lint check ---
Write-Host "🔍 Python guard scanning root: $PWD\\scripts"
$errors = 0
Get-ChildItem -Path scripts -Filter *.py -Recurse | ForEach-Object {
    $out = & python -m py_compile $_.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "⚠️ Syntax error in $($_.Name): $out"
        $errors++
    }
}
if ($errors -eq 0) {
    Write-Host "✅ Python lint check passed for all scripts."
} else {
    throw "❌ Python lint failed ($errors files)"
}

# --- Output folder setup ---
$outDir = ".artifacts\\data\\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Write-Host "📂 Output folder: $outDir"

# --- Simplified simulation runner (single safe attempt) ---
$simPy = "scripts/sim.run.py"
Write-Host "🐍 Executing Python simulation via $simPy ..."
try {
    $simOut = & python $simPy --out .artifacts/data/demo/metrics_ci.json
    if ($LASTEXITCODE -ne 0 -or ($simOut -match "Traceback|Error|Exception")) {
        Write-Warning "Simulation produced warnings or non-zero exit; see output below:"
        Write-Host $simOut
    } else {
        Write-Host "✅ Python simulation executed cleanly."
    }
}
catch {
    Write-Warning "Simulation failed to execute: $($_.Exception.Message)"
}
# --- End simulation block ---

# --- Refresh dashboard ---
Write-Host "🔄 Refreshing dashboard..."
& $PSScriptRoot\\ci.fix-open.ps1
Write-Host "✅ Dashboard refreshed via rebuild_ci.cmd."

# --- Verify metrics ---
$metrics = @(
    ".artifacts\\metrics\\summary.json",
    ".artifacts\\metrics\\summary.csv",
    ".artifacts\\metrics\\delta.json"
)
foreach ($m in $metrics) {
    if (Test-Path $m) { Write-Host "✅ $(Split-Path $m -Leaf) present: $m" }
    else { Write-Warning "❌ Missing $m" }
}

# --- Open dashboard once ---
$index = ".artifacts\\index.html"
if (Test-Path $index) {

    Start-Process explorer.exe "/select,$index"
} else {
    Write-Warning "❌ index.html not found."
}
.Exception.Message)"
}
# --- End simulation block ---

# --- Refresh dashboard ---
Write-Host "🔄 Refreshing dashboard..."
& "$PSScriptRoot\ci.fix-open.ps1"
Write-Host "✅ Dashboard refreshed via ci.fix-open.ps1."
Write-Host "🔄 Refreshing dashboard..."
& $PSScriptRoot\\ci.fix-open.ps1
Write-Host "✅ Dashboard refreshed via rebuild_ci.cmd."

# --- Verify metrics ---
$metrics = @(
    ".artifacts\\metrics\\summary.json",
    ".artifacts\\metrics\\summary.csv",
    ".artifacts\\metrics\\delta.json"
)
foreach ($m in $metrics) {
    if (Test-Path $m) { Write-Host "✅ $(Split-Path $m -Leaf) present: $m" }
    else { Write-Warning "❌ Missing $m" }
}

# --- Open dashboard once ---
$index = ".artifacts\\index.html"
if (Test-Path $index) {

    Start-Process explorer.exe "/select,$index"
} else {
    Write-Warning "❌ index.html not found."
}
# disabled duplicate open
# disabled duplicate open

# --- Final: Open dashboard robustly (single owner) ---
try {
  $repoRoot = Split-Path $PSScriptRoot -Parent
  $indexRel = ".artifacts\index.html"
  $index    = Join-Path $repoRoot $indexRel

  $abs = $null
  try {
    $rp  = Resolve-Path -LiteralPath $index -ErrorAction Stop
    $abs = $rp.Path
  } catch {
    # leave $abs = $null
  }

  if ($abs -and (Test-Path -LiteralPath $abs)) {
    try {
      Start-Process -FilePath $abs -Verb Open
    } catch {
      Start-Process explorer.exe $abs
    }
    Write-Host "🌐 Dashboard opened (robust): $abs"
  } else {
    Write-Warning "Dashboard not found at: $index"
  }
} catch {
  Write-Warning "Failed to open dashboard: $(# --- COLINK Daily CI Task ---
Write-Host "🌅 Starting daily COLINK CI maintenance..."

# --- Rotate old runs ---
$keep = 100
$runsDir = ".artifacts\\ci\\runs"
if (Test-Path $runsDir) {
    $runs = Get-ChildItem $runsDir -Filter "run-summary_*.json" | Sort-Object LastWriteTime -Descending
    if ($runs.Count -gt $keep) {
        $remove = $runs[$keep..($runs.Count - 1)]
        $remove | Remove-Item -Force
        Write-Host "♻️  Rotated $($remove.Count) old run logs (keep=$keep)"
    } else {
        Write-Host "✅ Nothing to rotate ($($runs.Count) runs, keep=$keep)."
    }
} else {
    Write-Host "ℹ️  Runs directory not found; skipping rotation."
}

# --- Python lint check ---
Write-Host "🔍 Python guard scanning root: $PWD\\scripts"
$errors = 0
Get-ChildItem -Path scripts -Filter *.py -Recurse | ForEach-Object {
    $out = & python -m py_compile $_.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "⚠️ Syntax error in $($_.Name): $out"
        $errors++
    }
}
if ($errors -eq 0) {
    Write-Host "✅ Python lint check passed for all scripts."
} else {
    throw "❌ Python lint failed ($errors files)"
}

# --- Output folder setup ---
$outDir = ".artifacts\\data\\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Write-Host "📂 Output folder: $outDir"

# --- Simplified simulation runner (single safe attempt) ---
$simPy = "scripts/sim.run.py"
Write-Host "🐍 Executing Python simulation via $simPy ..."
try {
    # Run with safe defaults to always succeed
    $simOut = & python $simPy --out .artifacts/data/demo/metrics_ci.json
    if ($LASTEXITCODE -ne 0 -or ($simOut -match "Traceback|Error|Exception")) {
        Write-Warning "Simulation produced warnings or non-zero exit; see output below:"
        Write-Host $simOut
    } else {
        Write-Host "✅ Python simulation executed cleanly."
    }
}
catch {
    Write-Warning "Simulation failed to execute: $(# --- COLINK Daily CI Task ---
Write-Host "🌅 Starting daily COLINK CI maintenance..."

# --- Rotate old runs ---
$keep = 100
$runsDir = ".artifacts\\ci\\runs"
if (Test-Path $runsDir) {
    $runs = Get-ChildItem $runsDir -Filter "run-summary_*.json" | Sort-Object LastWriteTime -Descending
    if ($runs.Count -gt $keep) {
        $remove = $runs[$keep..($runs.Count - 1)]
        $remove | Remove-Item -Force
        Write-Host "♻️  Rotated $($remove.Count) old run logs (keep=$keep)"
    } else {
        Write-Host "✅ Nothing to rotate ($($runs.Count) runs, keep=$keep)."
    }
} else {
    Write-Host "ℹ️  Runs directory not found; skipping rotation."
}

# --- Python lint check ---
Write-Host "🔍 Python guard scanning root: $PWD\\scripts"
$errors = 0
Get-ChildItem -Path scripts -Filter *.py -Recurse | ForEach-Object {
    $out = & python -m py_compile $_.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "⚠️ Syntax error in $($_.Name): $out"
        $errors++
    }
}
if ($errors -eq 0) {
    Write-Host "✅ Python lint check passed for all scripts."
} else {
    throw "❌ Python lint failed ($errors files)"
}

# --- Output folder setup ---
$outDir = ".artifacts\\data\\$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Write-Host "📂 Output folder: $outDir"

# --- Simplified simulation runner (single safe attempt) ---
$simPy = "scripts/sim.run.py"
Write-Host "🐍 Executing Python simulation via $simPy ..."
try {
    $simOut = & python $simPy --out .artifacts/data/demo/metrics_ci.json
    if ($LASTEXITCODE -ne 0 -or ($simOut -match "Traceback|Error|Exception")) {
        Write-Warning "Simulation produced warnings or non-zero exit; see output below:"
        Write-Host $simOut
    } else {
        Write-Host "✅ Python simulation executed cleanly."
    }
}
catch {
    Write-Warning "Simulation failed to execute: $($_.Exception.Message)"
}
# --- End simulation block ---

# --- Refresh dashboard ---
Write-Host "🔄 Refreshing dashboard..."
& $PSScriptRoot\\ci.fix-open.ps1
Write-Host "✅ Dashboard refreshed via rebuild_ci.cmd."

# --- Verify metrics ---
$metrics = @(
    ".artifacts\\metrics\\summary.json",
    ".artifacts\\metrics\\summary.csv",
    ".artifacts\\metrics\\delta.json"
)
foreach ($m in $metrics) {
    if (Test-Path $m) { Write-Host "✅ $(Split-Path $m -Leaf) present: $m" }
    else { Write-Warning "❌ Missing $m" }
}

# --- Open dashboard once ---
$index = ".artifacts\\index.html"
if (Test-Path $index) {

    Start-Process explorer.exe "/select,$index"
} else {
    Write-Warning "❌ index.html not found."
}
.Exception.Message)"
}
# --- End simulation block ---

# --- Refresh dashboard ---
Write-Host "🔄 Refreshing dashboard..."
& "$PSScriptRoot\ci.fix-open.ps1"
Write-Host "✅ Dashboard refreshed via ci.fix-open.ps1."
Write-Host "🔄 Refreshing dashboard..."
& $PSScriptRoot\\ci.fix-open.ps1
Write-Host "✅ Dashboard refreshed via rebuild_ci.cmd."

# --- Verify metrics ---
$metrics = @(
    ".artifacts\\metrics\\summary.json",
    ".artifacts\\metrics\\summary.csv",
    ".artifacts\\metrics\\delta.json"
)
foreach ($m in $metrics) {
    if (Test-Path $m) { Write-Host "✅ $(Split-Path $m -Leaf) present: $m" }
    else { Write-Warning "❌ Missing $m" }
}

# --- Open dashboard once ---
$index = ".artifacts\\index.html"
if (Test-Path $index) {

    Start-Process explorer.exe "/select,$index"
} else {
    Write-Warning "❌ index.html not found."
}
# disabled duplicate open
# disabled duplicate open

# --- Final: Open dashboard robustly (single owner) ---
try {
  $repoRoot = Split-Path $PSScriptRoot -Parent
  $indexRel = ".artifacts\index.html"
  $index    = Join-Path $repoRoot $indexRel
  $abs = $null
  try {
    $rp  = Resolve-Path -LiteralPath $index -ErrorAction Stop
    $abs = $rp.Path
  } catch { }
  if ($abs -and (Test-Path $abs)) {
    try {
      # Preferred: open with default associated app (browser)
      Start-Process -FilePath $abs -Verb Open
    } catch {
      # Fallback: Explorer will open the HTML file too
      Start-Process explorer.exe $abs
    }
    Write-Host "🌐 Dashboard opened (robust): $abs"
  } else {
    Write-Warning "Dashboard not found at: $index"
  }
} catch {
  Write-Warning "Failed to open dashboard: $($_.Exception.Message)"
}
.Exception.Message)"
}
# disabled duplicate open
# disabled duplicate open
# (disabled) inline open
# (disabled) inline open
# (disabled) inline open
# (disabled) inline open
# --- Single refresh (inline) ---
if (Test-Path 'scripts\ci.embed-latest.ps1') {
  & 'scripts\ci.embed-latest.ps1'
  if (\0 -eq 0) {
    Write-Host "✅ Embedded TZ-enabled index into .artifacts\index.html"
  } else {
    Write-Warning "Embed script returned non-zero exit."
  }
} else {
  Write-Warning "scripts\ci.embed-latest.ps1 not found — skipping embed step."
}
# --- End single refresh ---
# --- Single, final dashboard open (sole owner) ---
$index = ".artifacts\index.html"
$abs = $null
try { $abs = (Resolve-Path -LiteralPath $index -ErrorAction Stop).Path } catch {}
if ($abs) {
  Start-Process $abs
  Write-Host "🌐 Dashboard opened (single owner): $abs"
} else {
  Write-Warning "Dashboard not found: $index"
}


Start-Process ".artifacts\\index.html"


Start-Process ".artifacts\\index.html"



Start-Process ".artifacts\\index.html"


Start-Process ".artifacts\\index.html"


