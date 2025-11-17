param(
    [string]$OutDir = (Join-Path (Get-Location) ".artifacts")
)

# --- Setup directories ---
$plots = Join-Path $OutDir "plots"
New-Item -ItemType Directory -Force -Path $OutDir, $plots | Out-Null

Write-Host "== Emit Demo Data =="
Write-Host "Output path: $OutDir"

# --- Generate synthetic dataset ---
$t = 0..19
$rand = New-Object System.Random
$data = foreach ($i in $t) {
    $y = [math]::Sin($i / 3) + ($rand.NextDouble() - 0.5) * 0.4
    [pscustomobject]@{ t = $i; y = [math]::Round($y, 4) }
}

$csvPath = Join-Path $OutDir "dataset.csv"
$data | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $csvPath
Write-Host "→ dataset.csv written ($($data.Count) rows)"

# --- JSON metrics ---
$mean = ($data.y | Measure-Object -Average).Average
$variance = ($data.y | ForEach-Object { ($_ - $mean) * ($_ - $mean) } | Measure-Object -Average).Average
$std = [math]::Sqrt($variance)

$metrics = @{
    run_id   = "demo-$([DateTimeOffset]::Now.ToUnixTimeSeconds())"
    mean_y   = $mean
    std_y    = $std
    n_points = $data.Count
    status   = "ok"
}
$metricsPath = Join-Path $OutDir "sample.metrics.json"
$metrics | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $metricsPath
Write-Host "→ sample.metrics.json written"

# --- NDJSON events ---
$ndjsonPath = Join-Path $OutDir "sample.events.ndjson"
$data | ForEach-Object { @{ t = $_.t; y = $_.y } | ConvertTo-Json -Compress } |
    Out-File -Encoding utf8 -FilePath $ndjsonPath
Write-Host "→ sample.events.ndjson written"

# --- Minimal PNG stubs ---
# --- Real PNG charts (System.Drawing) ---
Add-Type -AssemblyName System.Drawing

# ========== summary.png ==========
$summary = Join-Path $plots "summary.png"
$bmp = [System.Drawing.Bitmap]::new(600, 300)
$g   = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.Clear([System.Drawing.Color]::White)

$pen = [System.Drawing.Pen]::new([System.Drawing.Color]::RoyalBlue, 2)
$points = [System.Collections.Generic.List[System.Drawing.PointF]]::new()
for ($i = 0; $i -lt $data.Count; $i++) {
    $x = [float](30 + $i * 28)
    $y = [float](150 - ($data[$i].y * 100))
    $points.Add([System.Drawing.PointF]::new($x, $y))
}
if ($points.Count -gt 1) { $g.DrawLines($pen, $points.ToArray()) }

$g.Dispose()
$bmp.Save($summary, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

# ========== sparkline.png ==========
$spark = [System.Drawing.Bitmap]::new(200, 40)
$gs = [System.Drawing.Graphics]::FromImage($spark)
$gs.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$gs.Clear([System.Drawing.Color]::White)
$penS = [System.Drawing.Pen]::new([System.Drawing.Color]::MediumSeaGreen, 2)
$minY = ($data.y | Measure-Object -Minimum).Minimum
$maxY = ($data.y | Measure-Object -Maximum).Maximum
$pointsS = [System.Collections.Generic.List[System.Drawing.PointF]]::new()
for ($i = 0; $i -lt $data.Count; $i++) {
    $x = [float](5 + $i * (190 / ($data.Count - 1)))
    $yNorm = ($data[$i].y - $minY) / ($maxY - $minY + 1e-9)
    $y = [float](35 - $yNorm * 30)
    $pointsS.Add([System.Drawing.PointF]::new($x, $y))
}
if ($pointsS.Count -gt 1) { $gs.DrawLines($penS, $pointsS.ToArray()) }
$gs.Dispose()
$spark.Save((Join-Path $plots "sparkline.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$spark.Dispose()

# ========== slow_by_module.png ==========
$bar = [System.Drawing.Bitmap]::new(400, 200)
$gb = [System.Drawing.Graphics]::FromImage($bar)
$gb.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$gb.Clear([System.Drawing.Color]::White)
$brush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::CornflowerBlue)

$modules = "auth","core","api","db","billing"
$rand = New-Object System.Random
for ($i=0; $i -lt $modules.Count; $i++) {
    $height = $rand.Next(30, 160)
    $x = 50 + $i * 60
    $y = 180 - $height
    $gb.FillRectangle($brush, $x, $y, 40, $height)
    $gb.DrawString($modules[$i], [System.Drawing.Font]::new("Arial", 8),
        [System.Drawing.Brushes]::Black, $x, 185)
}
$gb.Dispose()
$bar.Save((Join-Path $plots "slow_by_module.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$bar.Dispose()

Write-Host "→ 3 charts generated: summary, sparkline, slow_by_module"

Write-Host "Emit demo completed successfully."


