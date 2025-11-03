param(
  [Parameter(Position=0)][string]$Path = ".env.testnet",
  [switch]$PersistUser,
  [switch]$Quiet
)

function Import-Dotenv {
  param([string]$Path, [switch]$PersistUser, [switch]$Quiet)

  if (-not (Test-Path -LiteralPath $Path)) { throw "Dotenv file not found: $Path" }

  $setCount = 0
  Get-Content -LiteralPath $Path | ForEach-Object {
    $line = $_
    if ($line -match '^\s*$' -or $line -match '^\s*[#;]') { return }
    $parts = $line -split '=', 2
    if ($parts.Count -lt 2) { return }
    $k = $parts[0].Trim()
    $v = $parts[1].Trim()
    if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
      $v = $v.Substring(1, $v.Length-2)
    }
    Set-Item -Path ("Env:{0}" -f $k) -Value $v
    if ($PersistUser) { [Environment]::SetEnvironmentVariable($k, $v, "User") }
    $setCount++
    if (-not $Quiet) { Write-Host "set $k" -ForegroundColor DarkGray }
  }

  if (-not $Quiet) { Write-Host "Loaded $setCount variables from $Path" -ForegroundColor Green }
}

Import-Dotenv -Path $Path -PersistUser:$PersistUser -Quiet:$Quiet
