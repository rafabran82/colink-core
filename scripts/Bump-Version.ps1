[CmdletBinding()]
param(
  [ValidateSet("major","minor","patch")] [string]$Part = "patch"
)
$path = "pyproject.toml"
if (-not (Test-Path $path)) { Write-Error "pyproject.toml not found" }

$content = Get-Content $path -Raw
if ($content -notmatch 'version\s*=\s*"(.*?)"') {
  Write-Error "No version=\"x.y.z\" found in pyproject.toml"
}
$ver = [System.Version]::Parse($Matches[1])
switch ($Part) {
  "major" { $new = "{0}.{1}.{2}" -f ($ver.Major + 1), 0, 0 }
  "minor" { $new = "{0}.{1}.{2}" -f $ver.Major, ($ver.Minor + 1), 0 }
  "patch" { $new = "{0}.{1}.{2}" -f $ver.Major, $ver.Minor, ($ver.Build + 1) }
}
Write-Host "Bumping version $ver -> $new"
$updated = [regex]::Replace($content, 'version\s*=\s*"(.*?)"', 'version = "' + $new + '"', 1)
Set-Content -Path $path -Value $updated -Encoding utf8
Write-Output $new

