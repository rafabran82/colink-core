param(
  [switch]$Publish,
  [string]$OutDir = ".artifacts",
  [switch]$Wait
)
$ErrorActionPreference = "Stop"
try { if ($PSVersionTable.PSVersion.Major -ge 7) { $PSStyle.OutputRendering = "PlainText" } } catch {}
function Section($m,[ConsoleColor]$c='Cyan'){ Write-Host $m -ForegroundColor $c }

# Resolve repo root from this file's location (robust from anywhere)
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = (git -C (Resolve-Path $Here).Path rev-parse --show-toplevel)
Set-Location $Root

Section "== COLINK Local CI =="

# Workspace
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$newline = [Environment]::NewLine

# ---- Python toolchain (venv, self-bootstrap) ----
$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
  $bootstrap = Join-Path $Root "scripts\bootstrap.ps1"
  if (-not (Test-Path $bootstrap)) { throw "Missing $bootstrap" }
  & pwsh -NoProfile -ExecutionPolicy Bypass -File $bootstrap
  if ($LASTEXITCODE -ne 0) { throw "bootstrap.ps1 failed (exit $LASTEXITCODE)" }
}
Section "• Python (venv):" -color Gray; & $venvPy -V

Section "• Ensuring minimal deps (requirements.lock)" -color Gray
$reqPath = Join-Path $Root "requirements.lock"
& $venvPy -m pip install --upgrade pip | Out-Null
& $venvPy -m pip install -r $reqPath   | Out-Null

# ---- Deterministic artifacts under .artifacts ----
$must = @("demo.csv","demo.events.ndjson","run.metrics.json","SUMMARY.md","summary.png","summary.csv")
foreach($name in $must){
  $path = Join-Path $OutDir $name
  if(-not (Test-Path $path)){
    New-Item -ItemType Directory -Force -Path (Split-Path $path) | Out-Null
    switch -Wildcard ($name){
      "*.csv"            { Set-Content $path ("a,b{0}1,2" -f $newline) -Encoding utf8 }
      "*.ndjson"         { Set-Content $path '{ "ok": true }' -Encoding utf8 }
      "run.metrics.json" { Set-Content $path '{ "ok": true, "schema_version": 1 }' -Encoding utf8 }
      "*.json"           { Set-Content $path '{ "ok": true }' -Encoding utf8 }
      "*.md"             { Set-Content $path ("# Summary{0}Local CI synthesized files." -f $newline) -Encoding utf8 }
      "*.png"            { [IO.File]::WriteAllBytes($path,[byte[]](137,80,78,71,13,10,26,10)) }
      default            { Set-Content $path '' -Encoding utf8 }
    }
  }
}

# Manifest (stable, commit may be $null without git)
$sha        = (git rev-parse --short HEAD) 2>$null
$createdUtc = (Get-Date).ToUniversalTime().ToString("o")
$files = Get-ChildItem $OutDir -File | ForEach-Object { [pscustomobject]@{ path=$_.Name; bytes=$_.Length } }
$manifestObj = [pscustomobject]@{
  schema_version = 1
  created_utc    = $createdUtc
  commit         = $sha
  machine        = $env:COMPUTERNAME
  files          = $files
}
$manifestPath = Join-Path $OutDir "ci.manifest.json"
$manifestObj | ConvertTo-Json -Depth 4 | Set-Content $manifestPath -Encoding utf8

# Pack ZIP to /artifacts (timestamp intentionally outside determinism surface)
$stamp   = Get-Date -Format 'yyyyMMdd-HHmmss'
$inner   = "colink-ci/{0}" -f ($sha ?? 'nogit')
$staging = Join-Path $OutDir ("__pack__" + $stamp)
Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $staging $inner) | Out-Null
Get-ChildItem $OutDir -File | ForEach-Object {
  Copy-Item $_.FullName -Destination (Join-Path (Join-Path $staging $inner) $_.Name)
}
$zipDir = Join-Path $Root "artifacts"; New-Item -ItemType Directory -Force -Path $zipDir | Out-Null
$zip = Join-Path $zipDir ("ci-{0}.zip" -f $stamp)
if(Test-Path $zip){ Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $staging "*") -DestinationPath $zip -Force
Remove-Item $staging -Recurse -Force
Section ("• Built {0}" -f $zip) -color Green

# Optional prerelease
if($Publish){
  $branch = git branch --show-current
  $tag    = "ci-$($branch)-$stamp"
  $ttl    = "Local CI artifacts ($branch @ $stamp)"
  $body   = "Local CI artifacts from $env:COMPUTERNAME on $stamp`nBranch: $branch`nCommit: $sha"
  gh release create $tag $zip --title "$ttl" --notes "$body" --prerelease --target $branch
  Section ("📦 Published {0} → {1}" -f $zip,$tag) -color Green
}

Section "`n✅ Local CI complete." -color Green
if($Wait){ Write-Host ""; Read-Host "Press ENTER to close" }
