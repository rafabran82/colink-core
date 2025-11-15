param(
  [switch]$Fix
)

Write-Host "▶ GIT-NOISE CHECK"

# Find repo root
$root = (& git rev-parse --show-toplevel 2>$null)
if (-not $root) {
  Write-Warning "Not inside a git repo; skipping GIT-NOISE CHECK."
  return
}

$root = (Resolve-Path $root).Path

# --- 1) Gather candidate "noise" paths ---

$candidates = @()

# Stray root Node files / dirs
$candidates += Join-Path $root "package.json"
$candidates += Join-Path $root "package-lock.json"
$candidates += Join-Path $root "node_modules"
$candidates += Join-Path $root "colink-dashboard\backend\node_modules"

# Any *.bak backups anywhere in the repo
$bakFiles = Get-ChildItem -Path $root -Recurse -Filter *.bak -ErrorAction SilentlyContinue
if ($bakFiles) {
  $candidates += $bakFiles.FullName
}

# Filter out non-existent paths
$candidates = $candidates | Where-Object { Test-Path $_ } | Sort-Object -Unique

# --- 2) Drop anything Git already ignores (.gitignore rules) ---

$issues = @()

foreach ($item in $candidates) {
  $full = (Resolve-Path $item).Path
  # Make repo-relative path for git check-ignore
  $rel = $full.Substring($root.Length).TrimStart('\','/')
  # Ask Git if this path is ignored
  $null = git check-ignore --quiet -- "$rel" 2>$null
  if ($LASTEXITCODE -eq 0) {
    # Ignored by Git (.gitignore), so we don't treat it as an issue
    continue
  }
  $issues += $full
}

# --- 3) Ensure .gitignore has the guard patterns we want ---

$gitignore = Join-Path $root ".gitignore"
$missingGitignore = @()

$neededPatterns = @(
  "node_modules/",
  "colink-dashboard/backend/node_modules/",
  "*.bak"
)

if (Test-Path $gitignore) {
  $gi = Get-Content $gitignore -Raw
  foreach ($need in $neededPatterns) {
    if ($gi -notmatch [regex]::Escape($need)) {
      $missingGitignore += $need
    }
  }
} else {
  $missingGitignore = $neededPatterns
}

if ($issues.Count -eq 0 -and $missingGitignore.Count -eq 0) {
  Write-Host "   ✅ No git-noise issues detected."
  return
}

if ($issues) {
  Write-Host "   ⚠️ Detected git-noise issues (not git-ignored):" -ForegroundColor Yellow
  $issues | Sort-Object -Unique | ForEach-Object {
    Write-Host "     - $_"
  }
}

if ($missingGitignore) {
  Write-Host "   ⚠️ .gitignore missing patterns:" -ForegroundColor Yellow
  $missingGitignore | Sort-Object -Unique | ForEach-Object {
    Write-Host "     - $_"
  }
}

if ($Fix) {
  # Safe auto-fix:
  #  - Remove stray root package*.json (we don't use them)
  #  - Append missing patterns to .gitignore

  $rootPkg  = Join-Path $root "package.json"
  $rootLock = Join-Path $root "package-lock.json"

  if (Test-Path $rootPkg) {
    Remove-Item $rootPkg -Force
    Write-Host "   🧹 Removed $rootPkg"
  }
  if (Test-Path $rootLock) {
    Remove-Item $rootLock -Force
    Write-Host "   🧹 Removed $rootLock"
  }

  if ($missingGitignore) {
    if (-not (Test-Path $gitignore)) {
      New-Item -ItemType File -Path $gitignore -Force | Out-Null
    }
    $block = "`r`n# EWS git-noise guard`r`n" + ($missingGitignore -join "`r`n") + "`r`n"
    Add-Content -Path $gitignore -Encoding utf8 -Value $block
    Write-Host "   🧹 Updated .gitignore with missing patterns."
  }

  Write-Host "   ✅ Applied git-noise auto-fix. Re-run EWS to confirm."
  return
}

Write-Error "EWS-GIT-NOISE: repo contains non-ignored Node files / backups. Run scripts\ews.git-noise.ps1 -Fix or clean manually."
exit 1
