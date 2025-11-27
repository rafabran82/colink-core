[CmdletBinding()]
param(
  [string] $Ref = "main",      # branch or commit-ish to match
  [int]    $Limit = 40,        # how many runs to scan
  [string] $RunId,             # optional: use a specific run id instead
  [switch] $LatestSuccessful   # pick latest successful run for $Ref when true
)

set-strictmode -version latest
$ErrorActionPreference = 'Stop'

function Get-Repo { gh repo view --json nameWithOwner -q .nameWithOwner }
function Get-HeadSha([string]$ref) { git rev-parse "origin/$ref" }

$repo = Get-Repo

if (-not $RunId) {
  $matchSha = Get-HeadSha $Ref

  if ($LatestSuccessful) {
    $runs = gh run list --limit $Limit --json databaseId,url,status,conclusion,headSha,event,headBranch | ConvertFrom-Json
    $pick = $runs | Where-Object { $_.headSha -eq $matchSha -and $_.conclusion -eq 'success' } |
            Sort-Object databaseId -Descending | Select-Object -First 1
    if (-not $pick) { throw "No successful run found for ref '$Ref' (sha $matchSha)." }
    $RunId = $pick.databaseId
  } else {
    $runs = gh run list --limit $Limit --json databaseId,url,status,conclusion,headSha,event | ConvertFrom-Json
    $pick = $runs | Where-Object { $_.headSha -eq $matchSha } |
            Sort-Object databaseId -Descending | Select-Object -First 1
    if (-not $pick) { throw "No run found for ref '$Ref' (sha $matchSha)." }
    $RunId = $pick.databaseId
  }
}

Write-Host "Using run: $RunId" -ForegroundColor Cyan

# 1) Jobs (sanity)
$jobs = gh api "repos/$repo/actions/runs/$RunId/jobs" --paginate | ConvertFrom-Json
$jobList = $jobs.jobs
if (-not $jobList) { Write-Warning "No jobs returned for run $RunId. (Plan-level failure?)" }

# 2) Artifacts â†’ list â†’ download each to its own subfolder
$artDir = "artifacts-$RunId"
New-Item -ItemType Directory -Force -Path $artDir | Out-Null

$arts  = gh api "repos/$repo/actions/runs/$RunId/artifacts" | ConvertFrom-Json
$items = @()
if ($arts) {
  if ($arts.PSObject.Properties.Name -contains 'artifacts' -and $arts.artifacts) {
    $items = @($arts.artifacts)
  } elseif ($arts -is [System.Array]) {
    $items = @($arts)
  }
}

if (-not $items -or $items.Count -eq 0) {
  Write-Warning "No artifacts on run $RunId."
} else {
  foreach ($a in $items) {
    $safe = ($a.name -replace '[^\w\-]+','_')
    $dest = Join-Path $artDir $safe
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null

    # gh run download extracts into --dir; isolate per artifact
    gh run download $RunId --name $a.name --dir $dest
    Write-Host "Downloaded -> $dest"
  }
}

# 3) Aggregate all smoke_summary.json â†’ CSV & JSON
$outs = Join-Path $artDir "_combined"
New-Item -ItemType Directory -Force -Path $outs | Out-Null

$rows = @()
Get-ChildItem $artDir -Directory | ForEach-Object {
  $sum = Join-Path $_.FullName 'smoke_summary.json'
  if (Test-Path $sum) {
    try {
      $json = Get-Content $sum -Raw | ConvertFrom-Json
      $rows += [pscustomobject]@{
        run_id    = $RunId
        job       = $_.Name
        runner_os = $json.runner_os
        python    = $json.python
        pair      = $json.pair
        os_raw    = $json.os
      }
    } catch {
      Write-Warning "Failed to parse $sum : $($_.Exception.Message)"
    }
  }
}

if ($rows.Count -gt 0) {
  $csv = Join-Path $outs "smoke_matrix.csv"
  $jsonOut = Join-Path $outs "smoke_matrix.json"
  $rows | Sort-Object job | Export-Csv -NoTypeInformation -Path $csv -Encoding utf8
  $rows | ConvertTo-Json -Depth 5 | Set-Content -Path $jsonOut -Encoding utf8
  Write-Host "Matrix written:" -ForegroundColor Green
  Write-Host "  $csv"
  Write-Host "  $jsonOut"
} else {
  Write-Warning "No smoke_summary.json files were found in artifacts."
}

# 4) Zip each artifact folder + one bundle
$zipOut = "artifacts-$RunId-zip"
New-Item -ItemType Directory -Force -Path $zipOut | Out-Null

Get-ChildItem $artDir -Directory | ForEach-Object {
  $zip = Join-Path $zipOut ("{0}.zip" -f $_.Name)
  if (Test-Path $zip) { Remove-Item $zip -Force }
  $pattern = Join-Path $_.FullName '*'
  Compress-Archive -Path $pattern -DestinationPath $zip -Force
  Write-Host "Packed: $zip"
}

$bundle = "artifacts-$RunId-ALL.zip"
if (Test-Path $bundle) { Remove-Item $bundle -Force }
$patternAll = Join-Path $artDir '*'
Compress-Archive -Path $patternAll -DestinationPath $bundle -Force
Write-Host "Packed bundle: $bundle"

