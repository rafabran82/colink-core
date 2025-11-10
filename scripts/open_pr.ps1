param(
  [string]$Title,
  [string]$Body = "",
  [string]$BranchName = "",
  [string]$Base = "main",
  [switch]$Draft,
  [switch]$Open,
  [switch]$CommitAll,
  [string]$CommitMessage = "chore: bulk commit before PR"
)

function Require-Cmd($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $name"
  }
}

try {
  Require-Cmd git
  Require-Cmd gh
} catch {
  Write-Error $_.Exception.Message
  exit 1
}

# Verify gh auth
& gh auth status 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Error "GitHub CLI not logged in. Run: gh auth login"
  exit 1
}

# Ensure git repo
& git rev-parse --is-inside-work-tree 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Error "Not inside a Git repository."
  exit 1
}

$cur = (& git rev-parse --abbrev-ref HEAD).Trim()
$ts  = Get-Date -Format "yyyyMMdd-HHmmss"

function New-BranchNameFromTitle([string]$t) {
  if (-not $t) { return "pr/$ts" }
  $slug = ($t.ToLower() -replace '[^a-z0-9]+','-').Trim('-')
  if (-not $slug) { $slug = "pr" }
  return "pr/$slug-$ts"
}
if (-not $BranchName) { $BranchName = New-BranchNameFromTitle $Title }

Write-Host "Base branch: $Base"
Write-Host "Current branch: $cur"
Write-Host "New branch: $BranchName"

# Create/switch branch
& git switch -c $BranchName 2>$null
if ($LASTEXITCODE -ne 0) {
  & git switch $BranchName
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Could not create or switch to $BranchName"
    exit 1
  }
}

# Optionally commit all pending changes (disable GPG signing for this commit)
if ($CommitAll) {
  & git add -A
  & git diff --cached --quiet
  if ($LASTEXITCODE -ne 0) {
    & git -c commit.gpgsign=false commit -m $CommitMessage
    if ($LASTEXITCODE -ne 0) {
      Write-Host "Commit failed; attempting to disable signing locally for this repo..."
      & git config --local commit.gpgsign false
      & git commit -m $CommitMessage
      if ($LASTEXITCODE -ne 0) {
        Write-Error "Commit still failed. Resolve git errors and re-run."
        exit 1
      }
    }
  } else {
    Write-Host "Nothing to commit with -CommitAll (working tree clean)."
  }
}

# Push branch
& git push -u origin $BranchName
if ($LASTEXITCODE -ne 0) {
  Write-Error "Push failed. Fix errors above and re-run."
  exit 1
}

# Build gh pr create args (no --json; older gh versions don’t support it)
$prArgs = @("pr","create","--base",$Base,"--head",$BranchName)
if ($Title) { $prArgs += @("--title",$Title,"--body",$Body) } else { $prArgs += "--fill" }
if ($Draft) { $prArgs += "--draft" }
if ($Open)  { $prArgs += "--web" }

# Create PR
$null = & gh @prArgs
if ($LASTEXITCODE -ne 0) {
  Write-Error "Failed to create PR."
  exit 1
}

# Try to print PR URL (best-effort)
$prUrl = & gh pr view --head $BranchName --json url --jq .url 2>$null
if ($LASTEXITCODE -eq 0 -and $prUrl) {
  Write-Host "PR created: $prUrl"
} else {
  Write-Host "PR created. (Opened in browser if -Open was used.)"
}
