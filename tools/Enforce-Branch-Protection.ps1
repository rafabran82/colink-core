Param(
  [string]$Owner = "rafabran82",
  [string]$Repo  = "colink-core",
  [string]$Branch = "main",
  [string[]]$Contexts = @(
    "build-test",
    "pre-commit",
    "Windows / Python 3.12",
    "sim",
    "CodeQL/CodeQL (pull_request)"
  ),
  [switch]$RequireUpToDate = $true,
  [switch]$EnforceAdmins   = $true,
  [switch]$RequireConvRes  = $true,    # require conversation resolution
  [switch]$LinearHistory   = $false,
  [switch]$AllowForcePush  = $false,
  [switch]$AllowDeletions  = $false
)

$payload = @{
  required_status_checks = @{
    strict   = [bool]$RequireUpToDate
    contexts = $Contexts
  }
  enforce_admins = [bool]$EnforceAdmins
  required_pull_request_reviews = @{
    required_approving_review_count = 0
    dismiss_stale_reviews = $true
  }
  restrictions = $null
  required_conversation_resolution = [bool]$RequireConvRes
  required_linear_history          = [bool]$LinearHistory
  allow_force_pushes               = [bool]$AllowForcePush
  allow_deletions                  = [bool]$AllowDeletions
} | ConvertTo-Json -Depth 7

$payload | gh api -X PUT `
  "repos/$Owner/$Repo/branches/$Branch/protection" `
  -H "Accept: application/vnd.github+json" `
  --input -

# Verify
gh api "repos/$Owner/$Repo/branches/$Branch/protection" `
  -H "Accept: application/vnd.github+json" `
  --jq '{required_status_checks, enforce_admins, required_pull_request_reviews, required_conversation_resolution}'
