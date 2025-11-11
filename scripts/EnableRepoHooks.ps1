Param()

$repo = (git rev-parse --show-toplevel) 2>$null
if (-not $repo) { throw "Not inside a Git repo." }
Set-Location $repo

git config core.hooksPath .githooks
Write-Host "core.hooksPath set to .githooks"

# Quick self-test: empty commit should pass; staging a disallowed artifact should fail.
Write-Host "Smoke test: empty commit..."
git commit --allow-empty -m "ci(hooks): enable repo hooks" | Out-Null
Write-Host "OK."
