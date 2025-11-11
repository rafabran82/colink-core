# ci.guard-artifacts.ps1
# Fail the build if any *tracked* file exists under .artifacts that is not explicitly allowed.

param(
  [string]$Repo,                      # resolved after param if not provided
  [string]$ArtifactsRel = ".artifacts"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve $Repo only after parameters are bound
if ([string]::IsNullOrWhiteSpace($Repo)) {
  $Repo = (& git rev-parse --show-toplevel).Trim()
}
if ([string]::IsNullOrWhiteSpace($Repo)) {
  throw "Unable to resolve repository root."
}

Set-Location -Path $Repo

# Explicit allowlist of versioned files under .artifacts (tracked by Git).
$allowed = @(
  ".artifacts/reports/weekly.csv",
  ".artifacts/reports/summary.json",
  ".artifacts/.gitkeep",
  ".artifacts/index.html",
  ".artifacts/ci/.gitkeep",
  ".artifacts/ci/ci_summary.json",
  ".artifacts/metrics/.gitkeep",
  ".artifacts/plots/.gitkeep",
  ".artifacts/data/.gitkeep",
  ".artifacts/bundles/.gitkeep"
)

# Gather tracked files beneath .artifacts (not runtime outputs)
$tracked = (& git ls-files -z -- $ArtifactsRel) -split "`0" | Where-Object { $_ }

if (-not $tracked -or $tracked.Count -eq 0) {
  Write-Host ("Guard OK. No files are tracked under {0}." -f $ArtifactsRel)
  exit 0
}

# Anything tracked but not in the allowlist is a violation.
$unexpected = @()
foreach ($p in $tracked) {
  if (-not ($allowed -contains $p)) { $unexpected += $p }
}

if ($unexpected.Count -gt 0) {
  $list = ($unexpected | ForEach-Object { " - $_" }) -join "`n"
  Write-Error ("Guard failed: unexpected tracked files under {0}:{1}`n{2}" -f $ArtifactsRel, [Environment]::NewLine, $list)
  exit 1
}

Write-Host ("Guard OK. Tracked files under {0} are allowed (count={1})." -f $ArtifactsRel, $tracked.Count)
exit 0




