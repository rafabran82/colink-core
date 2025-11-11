# ci.guard-artifacts.ps1
# Fail the build if any *tracked* file exists under .artifacts that is not explicitly allowed.
# This enforces that only placeholder/summary files are versioned; everything else should remain untracked/ignored.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
  [string]$Repo = $(git rev-parse --show-toplevel),
  [string]$ArtifactsRel = ".artifacts"
)

Set-Location -Path $Repo

# Explicit allowlist of versioned files under .artifacts (tracked by Git).
# If you add a new summary or placeholder file that should be committed, add it here too.
$allowed = @(
  ".artifacts/.gitkeep",
  ".artifacts/index.html",
  ".artifacts/ci/.gitkeep",
  ".artifacts/ci/ci_summary.json",
  ".artifacts/metrics/.gitkeep",
  ".artifacts/plots/.gitkeep",
  ".artifacts/data/.gitkeep",
  ".artifacts/bundles/.gitkeep"
)

# Collect tracked files (not the ignored/untracked runtime outputs)
$tracked = (& git ls-files -z -- $ArtifactsRel) -split "`0" | Where-Object { $_ }

# Nothing tracked: that's fine.
if (-not $tracked -or $tracked.Count -eq 0) {
  Write-Host ("Guard OK. No files are tracked under {0}." -f $ArtifactsRel)
  exit 0
}

# Anything tracked but not in the allowlist is a violation.
$unexpected = @()
foreach ($p in $tracked) {
  if (-not ($allowed -contains $p)) {
    $unexpected += $p
  }
}

if ($unexpected.Count -gt 0) {
  $list = ($unexpected | ForEach-Object { " - $_" }) -join "`n"
  Write-Error ("Guard failed: unexpected tracked files under {0}:{1}`n{2}" -f $ArtifactsRel, [Environment]::NewLine, $list)
  exit 1
}

Write-Host ("Guard OK. Tracked files under {0} are allowed (count={1})." -f $ArtifactsRel, $tracked.Count)
exit 0
