param(
  [Parameter(Mandatory=$true, ValueFromPipeline=$true, ValueFromPipelineByPropertyName=$true)]
  [string[]]$Path
)

$utf8NoBom = [System.Text.UTF8Encoding]::new($false, $true)

function Normalize-One($p) {
  $full = (Resolve-Path $p).Path
  $bytes = [IO.File]::ReadAllBytes($full)

  # Strip UTF-8 BOM if present
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    $bytes = $bytes[3..($bytes.Length-1)]
  }

  $text = [System.Text.Encoding]::UTF8.GetString($bytes)

  # Drop leading U+FEFF if present, and normalize to LF
  if ($text.Length -gt 0 -and $text[0] -eq [char]0xFEFF) { $text = $text.Substring(1) }
  $text = $text -replace "`r`n?", "`n"

  $sw = New-Object System.IO.StreamWriter($full, $false, $utf8NoBom)
  try { $sw.Write($text) } finally { $sw.Close() }
}

$Path | ForEach-Object { Normalize-One $_ }
