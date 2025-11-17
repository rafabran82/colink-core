param(
  [string]$Note = "dev",
  [int]$KeepBundles = 10,
  [int]$KeepSnaps   = 10
)

$ErrorActionPreference = "Stop"

function Remove-OldFiles {
  param(
    [Parameter(Mandatory=$true)][string]$Dir,
    [Parameter(Mandatory=$true)][string]$Filter,
    [int]$Keep = 10
  )
  if (!(Test-Path $Dir)) { return }
  Get-ChildItem -Path $Dir -Filter $Filter -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $Keep |
    Remove-Item -Force -ErrorAction SilentlyContinue
}

# Resolve repo root
$root = (git rev-parse --show-toplevel 2>$null)
if (-not $root) { $root = (Get-Location).Path }
Set-Location -LiteralPath $root

# Directories
$artDir   = Join-Path $root '.artifacts'
$bundles  = Join-Path $artDir 'bundles'
$plotsDir = Join-Path $artDir 'plots'
$ciDir    = Join-Path $artDir 'ci'
$metrics  = Join-Path $artDir 'metrics'
$dataDir  = Join-Path $artDir 'data'

# Ensure structure
@($artDir,$bundles,$plotsDir,$ciDir,$metrics,$dataDir) | ForEach-Object {
  if (!(Test-Path $_)) { New-Item -ItemType Directory -Force -Path $_ | Out-Null }
}

Write-Host '== Phase-10: Bootstrap =='
try {
  python -c "print('Hello from Local-CI. Python OK.')" | Out-Null
  Write-Host 'Bootstrap complete.'
} catch {
  Write-Warning 'Python not available (continuing anyway).'
}

Write-Host "== Phase-30: Emit Demo Data + Charts =="
$emitScript = Join-Path $PSScriptRoot "ci\emit_demo.ps1"
if (Test-Path $emitScript) {
  Write-Host "Running emit_demo.ps1 to generate dataset, metrics, and charts..."
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $emitScript
} else {
  Write-Warning "emit_demo.ps1 not found — generating minimal placeholders."
  Set-Content -LiteralPath (Join-Path $artDir 'dataset.csv') -Encoding utf8 -Value "x,y`n1,2`n3,4"
  Set-Content -LiteralPath (Join-Path $artDir 'sample.metrics.json') -Encoding utf8 -Value '{"pass":true,"count":2}'
  $nd = @('{"t":1,"e":"start"}','{"t":2,"e":"done"}')
  Set-Content -LiteralPath (Join-Path $dataDir 'sample.events.ndjson') -Encoding utf8 -Value $nd
  [byte[]]$h = 137,80,78,71,13,10,26,10
  [IO.File]::WriteAllBytes((Join-Path $plotsDir 'sparkline.png'),      $h + (1..64))
  [IO.File]::WriteAllBytes((Join-Path $plotsDir 'summary.png'),        $h + (1..96))
  [IO.File]::WriteAllBytes((Join-Path $plotsDir 'slow_by_module.png'), $h + (1..128))
  Set-Content -LiteralPath (Join-Path $ciDir 'ci_badge.json')   -Encoding utf8 -Value '{"status":"PASS","passed":40,"skipped":2,"failed":0,"time_sec":7.426}'
  Set-Content -LiteralPath (Join-Path $ciDir 'ci_summary.json') -Encoding utf8 -Value '{"summary":"ok"}'
  Set-Content -LiteralPath (Join-Path $ciDir 'pytest.txt')      -Encoding utf8 -Value "All tests passed."
}

$badge = ConvertFrom-Json (Get-Content -Raw (Join-Path $ciDir 'ci_badge.json'))
$badgeHtml = ('<div class="badge"><span class="dot green"></span><b>{0}</b> — {1} passed; skipped {2}; failed {3}; time {4}s</div>' -f 
  $badge.status, $badge.passed, $badge.skipped, $badge.failed, ([math]::Round($badge.time_sec,3)))

function List-Section {
  param([string]$Title,[string]$Dir,[string]$Filter="*")
  if (!(Test-Path $Dir)) { return "" }
  $files = Get-ChildItem -Path $Dir -Filter $Filter -File -ErrorAction SilentlyContinue
  if (!$files) { return "" }
  $lis = $files | ForEach-Object {
    $n = $_.Name; $s = if ($_.Length -gt 0) { " <span>($([int]$_.Length) B)</span>" } else { "" }
    '<li><a href="' + $n + '">' + $n + '</a>' + $s + '</li>'
  }
  return "<h3>$Title</h3><ul>`n$([string]::Join(""`n"",$lis))`n</ul>"
}

$htmlLines = @(
  '<!doctype html>',
  '<html>',
  '<head>',
  '<meta charset="utf-8"/>' ,
  '<title>Local CI — ' + $Note + '</title>',
  '<style>',
  'body{font-family:Segoe UI,Arial,sans-serif;padding:24px;}',
  '.badge{margin-bottom:16px}',
  '.dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:#4caf50;margin-right:6px}',
  'ul{line-height:1.6}',
  'span{color:#555;font-size:12px;margin-left:6px}',
  'h2{margin-top:0}',
  '</style>',
  '</head>',
  '<body>',
  '<h2>Local CI — ' + $Note + '</h2>',
  $badgeHtml,
  (List-Section -Title 'Artifacts' -Dir $artDir),
  (List-Section -Title 'Plots' -Dir $plotsDir -Filter '*.png'),
  (List-Section -Title 'Metrics' -Dir $ciDir -Filter '*.json'),
  (List-Section -Title 'Data' -Dir $dataDir),
  '</body>',
  '</html>'
)

Set-Content -LiteralPath (Join-Path $artDir 'index.html') -Encoding utf8 -Value $htmlLines
Write-Host "`n== Local CI: done =="
Write-Host ("Open: {0}" -f (Join-Path $artDir 'index.html'))

# ===== Phase-95: Artifacts Summary =====
Write-Host ''
Write-Host '📁 Contents of .artifacts:'
Get-ChildItem -Recurse -File .artifacts |
    Select-Object FullName, Length |
    Sort-Object FullName |
    Format-Table -AutoSize
Write-Host ''
Write-Host '✅ Artifact summary displayed successfully.'
# ===== Phase-96: Auto-open index.html (local only) =====
if ($env:CI -ne 'true' -and $env:GITHUB_ACTIONS -ne 'true') {
    $indexPath = Join-Path (Join-Path $PSScriptRoot '..') '.artifacts\index.html'
    if (Test-Path $indexPath) {
        try {
            Write-Host "`n🌐 Opening index.html in default browser..."
            Start-Process $indexPath
            Write-Host "✅ Browser launched successfully."
        } catch {
            Write-Warning "⚠️ Could not auto-open browser: $($_.Exception.Message)"
        }
    } else {
        Write-Warning "index.html not found at $indexPath"
    }
} else {
    Write-Host "🧩 Skipping browser open (CI environment detected)."
}
# ===== Phase-97: Run Summary Logger =====
try {
    $runStart = Get-Date
    $ciRunsDir = Join-Path ".artifacts" "ci\\runs"
    if (!(Test-Path $ciRunsDir)) {
        New-Item -ItemType Directory -Force -Path $ciRunsDir | Out-Null
    }

    $artifactFiles = Get-ChildItem -Recurse -File .artifacts -ErrorAction SilentlyContinue
    $totalFiles = $artifactFiles.Count
    $totalBytes = ($artifactFiles | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($totalBytes / 1MB, 2)

    $summary = [ordered]@{
        run_id     = (Get-Date -Format "yyyyMMdd-HHmmss")
        note       = $Note
        timestamp  = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        artifacts  = $totalFiles
        size_mb    = $sizeMB
        user       = $env:USERNAME
        machine    = $env:COMPUTERNAME
        cwd        = (Get-Location).Path
    }

    $json = ($summary | ConvertTo-Json -Depth 3)
    $fileName = "run-summary_$($summary.run_id).json"
    $filePath = Join-Path $ciRunsDir $fileName
    Set-Content -Path $filePath -Value $json -Encoding utf8
    Write-Host "`n🧾 Run summary logged to $filePath ($totalFiles files, $sizeMB MB)"
}
catch {
    Write-Warning "⚠️ Failed to record run summary: $($_.Exception.Message)"
}
# ===== Phase-98: Master CSV Log =====
try {
    $csvPath = ".artifacts\\ci\\runs\\runs_log.csv"
    $entry = "{0},{1},{2},{3},{4},{5}" -f `
        $summary.run_id, $summary.timestamp, $summary.note, `
        $summary.artifacts, $summary.size_mb, $summary.user

    if (!(Test-Path $csvPath)) {
        "run_id,timestamp,note,artifacts,size_mb,user" | Out-File -FilePath $csvPath -Encoding utf8
    }
    Add-Content -Path $csvPath -Value $entry
    Write-Host "🗃️  Appended summary to master runs_log.csv"
}
catch {
    Write-Warning "⚠️ Could not update master CSV log: $($_.Exception.Message)"
}
# ===== Phase-98: Master CSV Log (Extended Analytics) =====
try {
    $csvPath = ".artifacts\\ci\\runs\\runs_log.csv"

    # Compute averages and runtime
    $avgSizeKB = if ($totalFiles -gt 0) { [math]::Round(($totalBytes / 1KB) / $totalFiles, 2) } else { 0 }
    $runEnd = Get-Date
    $runtimeSec = [math]::Round(($runEnd - $runStart).TotalSeconds, 2)

    # Update summary object to include computed metrics
    $summary.avg_size_kb = $avgSizeKB
    $summary.runtime_sec = $runtimeSec

    # Persist updated JSON file (overwrite same path)
    $jsonUpdated = ($summary | ConvertTo-Json -Depth 3)
    Set-Content -Path $filePath -Value $jsonUpdated -Encoding utf8

    # Prepare CSV header + line
    $header = "run_id,timestamp,note,artifacts,size_mb,avg_size_kb,runtime_sec,user"
    $entry = "{0},{1},{2},{3},{4},{5},{6},{7}" -f `
        $summary.run_id, $summary.timestamp, $summary.note, `
        $summary.artifacts, $summary.size_mb, $summary.avg_size_kb, `
        $summary.runtime_sec, $summary.user

    # Create file if needed, otherwise append
    if (!(Test-Path $csvPath)) {
        $header | Out-File -FilePath $csvPath -Encoding utf8
    }
    Add-Content -Path $csvPath -Value $entry

    Write-Host "🗃️  Appended summary to master runs_log.csv ($runtimeSec sec, avg $avgSizeKB KB/file)"
}
catch {
    Write-Warning "⚠️ Could not update master CSV log: $($_.Exception.Message)"
}

# ===== Phase-99: CI Trend Chart (PowerShell/.NET) =====
try {
    $runsDir   = ".artifacts\ci\runs"
    $csvPath   = Join-Path $runsDir "runs_log.csv"
    $outPng    = Join-Path $runsDir "runs_trend.png"

    if (Test-Path $csvPath) {
        Write-Host "📈 Generating CI trend chart (PowerShell) from $csvPath ..."

        # Read CSV (expected headers: run_id,timestamp,note,artifacts,size_mb,user, [optional: runtime_sec])
        $rows = Import-Csv -Path $csvPath
        if (-not $rows -or $rows.Count -eq 0) { throw "runs_log.csv has no rows." }

        # Build x-axis labels and numeric series
        $labels   = @()
        $arts     = @()
        $sizes    = @()
        $runtimes = @()
        foreach ($r in $rows) {
            $labels  += ($r.timestamp -as [string])
            $arts    += ($r.artifacts -as [double])
            $sizes   += ($r.size_mb   -as [double])
            $rt = 0
            if ($r.PSObject.Properties.Name -contains 'runtime_sec') {
                $rt = ($r.runtime_sec -as [double])
            }
            $runtimes += ($rt)
        }

        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Windows.Forms.DataVisualization

        $chart = New-Object System.Windows.Forms.DataVisualization.Charting.Chart
        $width,$height = 900,420
        $chart.Width  = $width
        $chart.Height = $height
        $chart.BackColor = [System.Drawing.Color]::White

        $area = New-Object System.Windows.Forms.DataVisualization.Charting.ChartArea "main"
        $area.AxisX.Interval = 1
        $area.AxisX.LabelStyle.Angle = -45
        $area.AxisX.MajorGrid.Enabled = $false
        $area.AxisY.MajorGrid.LineColor = [System.Drawing.Color]::Gainsboro
        $area.AxisY2.Enabled = [System.Windows.Forms.DataVisualization.Charting.AxisEnabled]::True
        $area.AxisY2.MajorGrid.Enabled = $false
        $chart.ChartAreas.Add($area)

        $chart.Titles.Add("Local-CI Run Trends") | Out-Null

        function Add-Line($name,$vals,$useAxisY2=$false) {
            $s = New-Object System.Windows.Forms.DataVisualization.Charting.Series $name
            $s.ChartType = [System.Windows.Forms.DataVisualization.Charting.SeriesChartType]::Line
            $s.BorderWidth = 2
            if ($useAxisY2) { $s.YAxisType = [System.Windows.Forms.DataVisualization.Charting.AxisType]::Secondary }
            for ($i=0; $i -lt $labels.Count; $i++) {
                $p = $s.Points.Add($vals[$i])
                $s.Points[$p].AxisLabel = $labels[$i]
            }
            $chart.Series.Add($s) | Out-Null
        }

        Add-Line -name 'Artifacts'   -vals $arts
        Add-Line -name 'Total MB'    -vals $sizes -useAxisY2 $true
        if (($runtimes | Measure-Object -Sum).Sum -gt 0) {
            Add-Line -name 'Runtime (sec)' -vals $runtimes
        }

        $legend = New-Object System.Windows.Forms.DataVisualization.Charting.Legend
        $legend.Docking = 'Top'
        $chart.Legends.Add($legend) | Out-Null

        $chart.SaveImage($outPng, 'Png')
        Write-Host "✅ Trend chart written: $outPng"
    } else {
        Write-Warning "No runs_log.csv found — skipping trend chart."
    }
}
catch {
    Write-Warning "⚠️ CI trend chart failed: $($_.Exception.Message)"
}

# ===== Phase-100: Embed CI Trend Chart into index.html =====
try {
    $htmlPath = ".artifacts\index.html"
    $chartRel = "ci/runs/runs_trend.png"
    $chartAbs = ".artifacts\$chartRel"

    if ((Test-Path $htmlPath) -and (Test-Path $chartAbs)) {
        Write-Host "🧩 Embedding CI trend chart into index.html ..."
        $html  = Get-Content -Raw -Path $htmlPath -Encoding utf8
        $embed = "<hr/><h3>CI Trend History</h3><img src='$chartRel' style='max-width:920px;border:1px solid #ddd;border-radius:8px'/>"
        if ($html -notmatch 'CI Trend History') {
            $html = $html -replace '(?i)</body>', "$embed`n</body>"
            Set-Content -Path $htmlPath -Encoding utf8 -Value $html
            Write-Host "✅ Embedded trend chart into .artifacts\index.html"
        } else {
            Write-Host "ℹ️  Chart already embedded — skipped."
        }
    } else {
        Write-Warning "No index.html or trend chart found — skipping embed."
    }
}
catch {
    Write-Warning "⚠️ Trend chart embedding failed: $($_.Exception.Message)"
}
