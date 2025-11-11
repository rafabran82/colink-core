function Resolve-TimeZone([string]$Name) {
  if (-not $Name -or $Name -eq 'Local') { return [TimeZoneInfo]::Local }
  switch -Regex ($Name.Trim()) {
    '^UTC$'        { return [TimeZoneInfo]::Utc }
    '^Eastern'     { return [TimeZoneInfo]::FindSystemTimeZoneById('Eastern Standard Time') }
    '^Central'     { return [TimeZoneInfo]::FindSystemTimeZoneById('Central Standard Time') }
    '^Mountain'    { return [TimeZoneInfo]::FindSystemTimeZoneById('Mountain Standard Time') }
    '^Pacific'     { return [TimeZoneInfo]::FindSystemTimeZoneById('Pacific Standard Time') }
    default        { return [TimeZoneInfo]::FindSystemTimeZoneById($Name) } # allow exact Windows ID
  }
}

function Convert-IsoToZone([string]$Iso, [string]$Target = 'Local') {
  if (-not $Iso) { return $Iso }
  $tzTarget = Resolve-TimeZone $Target
  # Treat input ISO (yyyy-MM-ddTHH:mm:ss) as *local* time that was logged
  $dt = [DateTime]::ParseExact($Iso, 'yyyy-MM-ddTHH:mm:ss', $null, [Globalization.DateTimeStyles]::None)
  $localTz = [TimeZoneInfo]::Local
  $dto = [DateTimeOffset]::new($dt, ($localTz.GetUtcOffset($dt)))
  $dtoTarget = [TimeZoneInfo]::ConvertTime($dto, $tzTarget)
  return $dtoTarget.ToString('yyyy-MM-ddTHH:mm:ss')
}
