param(
  [Parameter(Mandatory=$true)]
  [string]$RunId
)

$root  = "artifacts-$RunId"
if (-not (Test-Path $root)) {
  throw "Folder '$root' not found. Download artifacts first."
}

$zipOut = "artifacts-$RunId-zip"
New-Item -ItemType Directory -Force -Path $zipOut | Out-Null

Get-ChildItem $root -Directory | ForEach-Object {
  $zip = Join-Path $zipOut ("{0}.zip" -f $_.Name)
  if (Test-Path $zip) { Remove-Item $zip -Force }
  $pattern = Join-Path $_.FullName '*'
  Compress-Archive -Path $pattern -DestinationPath $zip -Force
  "Packed: $zip"
}

