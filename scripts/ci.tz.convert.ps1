param(
  [Parameter(Mandatory)][string]$InCsv,
  [Parameter(Mandatory)][ValidateSet("Eastern","Central","Mountain","Pacific","UTC","Local")]
  [string]$ToTz,
  [string]$OutCsv = $(Join-Path $env:TEMP ("runs_log_{0}.csv" -f $ToTz))
)
$ErrorActionPreference = "Stop"
# Map friendly → Windows TZ
$map = @{
  "Eastern"  = "Eastern Standard Time"
  "Central"  = "Central Standard Time"
  "Mountain" = "Mountain Standard Time"
  "Pacific"  = "Pacific Standard Time"
  "UTC"      = "UTC"
  "Local"    = $null
}
$tzId = $map[$ToTz]
$lines = Get-Content -Path $InCsv
$out = New-Object System.Collections.Generic.List[string]
foreach ($ln in $lines) {
  $parts = $ln -split ',',3
  if ($parts.Count -lt 3) { continue }
  $ts,$files,$mb = $parts
  try {
    $dt = [datetime]::Parse($ts) # assumes input is local time ISO
    if ($tzId) {
      $src = [System.TimeZoneInfo]::Local
      $dst = [System.TimeZoneInfo]::FindSystemTimeZoneById($tzId)
      $utc = [System.TimeZoneInfo]::ConvertTimeToUtc($dt, $src)
      $view = [System.TimeZoneInfo]::ConvertTimeFromUtc($utc, $dst)
    } else {
      $view = $dt
    }
    $iso = $view.ToString("yyyy-MM-ddTHH:mm:ss")
    $out.Add("{0},{1},{2}" -f $iso,$files,$mb)
  } catch { }
}
$out | Set-Content -Path $OutCsv -Encoding utf8
Write-Output $OutCsv
