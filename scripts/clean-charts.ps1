param([string]$Dir="charts")
if (Test-Path $Dir) {
  Get-ChildItem $Dir -Filter *.png -File | Remove-Item -Force
}
