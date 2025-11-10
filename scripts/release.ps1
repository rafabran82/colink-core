param(
  [Parameter(Mandatory=$true)][string]$Version
)
$ErrorActionPreference = "Stop"

Write-Host "Bumping version to $Version" -ForegroundColor Cyan
$pp = "pyproject.toml"
(Get-Content $pp -Raw) -replace '(?m)^\s*version\s*=\s*".*"',("version = `"$Version`"") |
  Set-Content $pp -Encoding utf8
git add $pp
git commit -m ("chore(version): {0}" -f $Version) | Out-Null

Write-Host "Tagging v$Version" -ForegroundColor Cyan
git tag -a ("v{0}" -f $Version) -m ("Release {0}" -f $Version)
git push
git push --tags

Write-Host "Done." -ForegroundColor Green
