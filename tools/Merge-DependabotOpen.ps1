param(
  [switch]$DryRun,          # Show actions without changing anything
  [int]$Limit = 25          # Process up to N open PRs
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg)  { Write-Host "[i] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "[✓] $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Warning $msg }
function Write-Err($msg)   { Write-Host "[x] $msg" -ForegroundColor Red }

# Helper: run a block only when not DryRun
function Invoke-IfNotDry([scriptblock]$Action) {
  if (-not $DryRun) { & $Action }
}

# Safe check for a property existing on an object
function Has-Prop($obj, $name) {
  return ($obj -is [psobject]) -and ($obj.PSObject.Properties.Name -contains $name)
}

# Identify Dependabot PRs safely: headRefName prefix OR author OR label
function Test-DependabotPR($pr) {
  $byHead   = (Has-Prop $pr 'headRefName') -and ($pr.headRefName -like 'dependabot/*')

  $byAuthor = $false
  if (Has-Prop $pr 'author' -and $pr.author) {
    # If author is present, accept null-safe lookup
    try { $byAuthor = ($pr.author.login -eq 'dependabot[bot]') } catch { $byAuthor = $false }
  }

  $byLabel  = $false
  if (Has-Prop $pr 'labels' -and $pr.labels) {
    try { $byLabel = ($pr.labels | Where-Object { $_.name -eq 'dependencies' }).Count -gt 0 } catch { $byLabel = $false }
  }

  return ($byHead -or $byAuthor -or $byLabel)
}

# Resolve repo owner/name once
$repoMeta = gh repo view --json owner,name | ConvertFrom-Json
$repoFull = "$($repoMeta.owner.login)/$($repoMeta.name)"

# 1) Gather candidate PRs (may or may not include author/labels depending on gh version/scopes)
$raw = gh pr list --state open --limit 100 `
  --json number,title,headRefName,updatedAt,author,labels `
| ConvertFrom-Json

$prs = @()
if ($raw) {
  $prs = $raw | Where-Object { Test-DependabotPR $_ } | Sort-Object updatedAt -Descending | Select-Object -First $Limit
}

if (-not $prs -or $prs.Count -eq 0) {
  Write-Ok "No open Dependabot PRs found."
  exit 0
}

Write-Info ("Found {0} Dependabot PR(s)." -f $prs.Count)

foreach ($p in $prs) {
  $pr = $p.number
  Write-Host ""
  Write-Host "=== PR #$pr — $($p.title) ===" -ForegroundColor Yellow

  # Fresh view & meta
  $view = gh pr view $pr --json headRefName,isDraft,mergeStateStatus,mergeable,reviewDecision,state | ConvertFrom-Json
  $meta = gh api "repos/$repoFull/pulls/$pr" | ConvertFrom-Json

  Write-Info ("state={0} merged={1}  head={2}  mergeState={3}  mergeable={4}  review={5}" `
    -f $view.state, $meta.merged, $view.headRefName, $view.mergeStateStatus, $view.mergeable, $view.reviewDecision)

  if ($meta.merged) {
    Write-Ok "Already merged — skipping."
    continue
  }
  if ($view.state -eq 'CLOSED' -and -not $meta.merged) {
    Write-Warn "Closed without merge — skipping."
    continue
  }
  if ($view.isDraft) {
    Write-Warn "Draft PR — skipping."
    continue
  }

  # 2) Update PR head if it exists and is behind
  $head = $view.headRefName
  $headExistsRemote = (& git ls-remote --heads origin $head) -ne $null

  if ($headExistsRemote) {
    Write-Info "Checking out PR head '$head' and syncing with origin/main…"
    Invoke-IfNotDry { gh pr checkout $pr | Out-Null }
    Invoke-IfNotDry { git fetch origin | Out-Null }

    if ($view.mergeStateStatus -eq 'BEHIND') {
      Write-Info "Head is BEHIND main → merging origin/main…"
      if (-not $DryRun) {
        try {
          git merge --no-edit origin/main | Out-Null
          git push | Out-Null
          Write-Ok "PR head updated."
        } catch {
          Write-Err "Merge failed. Resolve conflicts in this branch, then re-run."
          continue
        }
      } else {
        Write-Info "DRY RUN: would merge origin/main and push."
      }
    } else {
      Write-Info "Head is not behind; no update needed."
    }
  } else {
    Write-Info "Head branch '$head' no longer exists (likely auto-deleted); proceeding without checkout."
  }

  # 3) Approve (satisfies required review=1); harmless if already approved
  Write-Info "Approving PR (harmless if already approved)…"
  Invoke-IfNotDry {
    try { gh pr review $pr --approve | Out-Null } catch { }
  }

  # 4) Queue auto-merge (squash)
  Write-Info "Queuing auto-merge (squash)…"
  Invoke-IfNotDry {
    try { gh pr merge $pr --squash --auto | Out-Null } catch { }
  }

  # 5) Wait until merged (or stop if closed w/o merge)
  if (-not $DryRun) {
    do {
      Start-Sleep 5
      $m = gh api "repos/$repoFull/pulls/$pr" | ConvertFrom-Json
      Write-Info ("state={0} merged={1}" -f $m.state, $m.merged)
      if ($m.state -eq "closed" -and -not $m.merged) {
        Write-Warn "Closed without merge — moving on."
        break
      }
    } while (-not $m.merged)
  } else {
    Write-Info "DRY RUN: would wait for GitHub to merge automatically."
  }
}

# 6) Sync and clean
Write-Info "Syncing local main and pruning stale refs…"
Invoke-IfNotDry {
  git switch main | Out-Null
  git pull --ff-only | Out-Null
  git fetch --prune origin | Out-Null
  git remote prune origin | Out-Null
  git branch --merged origin/main | ? {$_ -notmatch '^\*|^main$'} | % { git branch -d $_.Trim() } | Out-Null
}
Write-Ok "All done."
