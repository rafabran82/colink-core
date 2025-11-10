param(
  [string]$Artifacts = ".\.artifacts",
  [string]$Bundles   = ".\.bundles"
)

function Ensure-Folder($p){ if(-not(Test-Path $p)){ New-Item -ItemType Directory -Force -Path $p | Out-Null } }

if(-not (Test-Path $Artifacts)){ throw "No artifacts at $Artifacts. Run .\run_ci.ps1 first." }
$files = Get-ChildItem -File -Recurse $Artifacts
if(-not $files){ throw "Artifacts folder is empty." }

Ensure-Folder $Bundles

$ts   = Get-Date -Format "yyyyMMdd-HHmmss"
$base = "release-$ts"
$zip  = Join-Path $Bundles "$base.zip"
$tgz  = Join-Path $Bundles "$base.tgz"

# Write/refresh SUMMARY.md (very small, quick parse of pytest results if present)
$summary = Join-Path $Artifacts "SUMMARY.md"
$pytest  = Join-Path $Artifacts "pytest.txt"
$pytestLine = ""
if (Test-Path $pytest) {
  $tail = Get-Content $pytest -Tail 5
  $pytestLine = ($tail | Where-Object { $_ -match '\[\s*\d+%]|\d+\s*passed|\d+\s*failed|\d+\s*skipped' }) -join ' '
}

$counts = ($files | Group-Object Extension | Sort-Object Count -Descending | ForEach-Object { "{0} × {1}" -f $_.Count, ($_.Name -replace '^\.', '') }) -join ', '
$body = @"
# Local CI Summary — $ts

- Files: $($files.Count) ($counts)
- Pytest: $pytestLine

Bundles:
- $($base).zip
- $($base).tgz
"@
Set-Content -Path $summary -Encoding utf8 -Value $body

# Create bundles
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $Artifacts '*') -DestinationPath $zip -Force

# tar is available on modern Windows
if (Test-Path $tgz) { Remove-Item $tgz -Force }
Push-Location $Artifacts
try { tar -czf $tgz * } finally { Pop-Location }

Write-Host "Wrote:"; Write-Host " - $zip"; Write-Host " - $tgz"
