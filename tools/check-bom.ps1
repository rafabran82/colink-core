Param()

$ErrorActionPreference = "Stop"

function Test-YamlClean {
  param([string]$File)

  [byte[]]$bytes = [System.IO.File]::ReadAllBytes($File)

  $hasBomAtStart = $false
  if ($bytes.Length -ge 3) {
    $hasBomAtStart = ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
  }

  # detect CRLF
  $hasCrlf = $false
  for ($i=0; $i -lt $bytes.Length-1; $i++) {
    if ($bytes[$i] -eq 0x0D -and $bytes[$i+1] -eq 0x0A) { $hasCrlf = $true; break }
  }

  # detect any EF BB BF triplets anywhere
  $embeddedIdx = @()
  for ($i=0; $i -lt $bytes.Length-2; $i++) {
    if ($bytes[$i] -eq 0xEF -and $bytes[$i+1] -eq 0xBB -and $bytes[$i+2] -eq 0xBF) {
      $embeddedIdx += $i
      $i += 2
    }
  }

  [pscustomobject]@{
    File           = $File
    HasBomAtStart  = $hasBomAtStart
    HasCrlf        = $hasCrlf
    BomPositions   = $embeddedIdx
  }
}

$root  = Join-Path $PSScriptRoot ".."
$wfDir = Join-Path $root ".github/workflows"

if (-not (Test-Path $wfDir)) { return }

$targets = Get-ChildItem $wfDir -File -Include *.yml,*.yaml -Recurse
if (-not $targets) { return }

$bad = @()

foreach ($t in $targets) {
  $r = Test-YamlClean -File $t.FullName
  if ($r.HasBomAtStart -or $r.HasCrlf -or $r.BomPositions.Count -gt 0) {
    $bad += $r
  }
}

if ($bad.Count -gt 0) {
  $lines = foreach ($b in $bad) {
    $details = @()
    if ($b.HasBomAtStart) { $details += "BOM at start" }
    if ($b.HasCrlf)       { $details += "CRLF present" }
    if ($b.BomPositions.Count -gt 0) {
      $pos = ($b.BomPositions -join ",")
      $details += "embedded EF BB BF at byte offsets: $pos"
    }
    "{0}  ->  {1}" -f $b.File, ($details -join " ; ")
  }
  Write-Error ("Workflow encoding issues:`n" + ($lines -join "`n"))
  exit 1
}

Write-Output "[ok] Workflow YAMLs are UTF-8 (no BOM) with LF only."
exit 0