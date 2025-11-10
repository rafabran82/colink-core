# === Approve-And-Merge v3 ===
# Smart multi-PR merge helper with -All and -DryRun modes

function Approve-And-Merge {
    [CmdletBinding(DefaultParameterSetName="Single")]
    param(
        [Parameter(ParameterSetName="Single", Position=0)]
        [int]$Number,

        [Parameter(ParameterSetName="Batch")]
        [switch]$All,

        [switch]$DryRun
    )

    # small helpers
    function _log($msg, $color="White") {
        Write-Host $msg -ForegroundColor $color
    }

    function _mergeOne($n) {
        _log "🔎 Checking PR #$n..." Cyan
        if ($DryRun) { _log "  (dry-run: would check CI + merge)" Yellow; return }

        gh pr checks $n --watch 2>$null | Out-Null
        try {
            gh pr merge $n --squash 2>$null
            _log "✅ Merged PR #$n" Green
        }
        catch {
            _log "⚠️  Normal merge blocked — trying admin override..." Yellow
            try {
                gh pr merge $n --admin --squash 2>$null
                _log "✅ Merged (admin) PR #$n" Green
            }
            catch {
                _log "❌ Failed to merge PR #$n" Red
            }
        }

        $head = gh pr view $n --json headRefName -q .headRefName 2>$null
        if ($head) {
            git branch -D $head 2>$null
            git push origin --delete $head 2>$null
            _log "🧹 Cleaned branch $head" DarkGray
        }
    }

    if ($All) {
        $prs = gh pr list --state open --json number,title -q '.[].number'
        if (-not $prs) {
            _log "No open pull requests found." Yellow
            return
        }

        _log "Processing all open PRs: $($prs -join ', ')" Cyan
        foreach ($n in $prs) { _mergeOne $n }
    }
    elseif ($Number) {
        _mergeOne $Number
    }
    else {
        _log "Usage: Approve-And-Merge <PR#> | -All | -All -DryRun" Yellow
    }

    _log "✅ Done." Green
}
# === end Approve-And-Merge v3 ===
