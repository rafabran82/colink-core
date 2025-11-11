param([switch]$Open)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repo

$args = @()
if (-not $Open) { $args += "-NoOpen" }
pwsh -File "scripts\Local-CI.ps1" @args
