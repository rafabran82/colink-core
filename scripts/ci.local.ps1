param(
  [string]$Out = ".artifacts",
  [string]$Junit = ".artifacts/ci/junit.xml"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $Out,"$Out/ci","$Out/plots","$Out/metrics","$Out/bundles","$Out/data" | Out-Null

# Run tests → JUnit + text log
$pytestArgs = @("-m","pytest","--junitxml",$Junit,"-q")
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "python"
$psi.Arguments = $pytestArgs -join " "
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError  = $true
$p = [System.Diagnostics.Process]::Start($psi)
$stdout = $p.StandardOutput.ReadToEnd()
$stderr = $p.StandardError.ReadToEnd()
$p.WaitForExit()

$txt = Join-Path $Out "ci\pytest.txt"
$std = Join-Path $Out "ci\ci_run.stdout.log"
$err = Join-Path $Out "ci\ci_run.stderr.log"
Set-Content -LiteralPath $txt -Value $stdout -Encoding utf8
Set-Content -LiteralPath $std -Value $stdout -Encoding utf8
Set-Content -LiteralPath $err -Value $stderr -Encoding utf8

# Minimal index + summary (no giant here-strings)
$ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
$index = Join-Path $Out "index.html"
@(
'<!doctype html><meta charset="utf-8"><title>Local CI</title>',
"<h1>Local CI</h1><p>Generated: $ts</p>"
) -join "`n" | Set-Content -LiteralPath $index -Encoding utf8

$sum = Join-Path $Out "ci\ci_summary.json"
$summaryObj = [ordered]@{ status = "local"; generatedAt = $ts; normalExit = $p.ExitCode }
($summaryObj | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $sum -Encoding utf8

exit 0
