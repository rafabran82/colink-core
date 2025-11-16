param(
    [string]$Date = (Get-Date).ToString("yyyyMMdd")
)

$roll = & scripts/CI-Rollup-Parse.ps1 -Date $Date | ConvertFrom-Json

$index = ".artifacts/index.html"
if (-not (Test-Path $index)) {
    Write-Error "index.html not found: $index"
    exit 1
}

$block = @"
<!-- XRPL-ROLLUP-BEGIN -->
<h2>XRPL Intelligence Snapshot ($($Date.Substring(0,4))-$($Date.Substring(4,2))-$($Date.Substring(6,2)))</h2>
<ul>
  <li><b>Total TX:</b> $($roll.total_tx)</li>
  <li><b>Unique Accounts:</b> $($roll.unique_accounts)</li>
  <li><b>Swaps:</b> $($roll.swap_tx)</li>
  <li><b>OfferCreate:</b> $($roll.offer_create)</li>
  <li><b>Payments:</b> $($roll.payment_tx)</li>
  <li><b>Ledger Range:</b> $($roll.min_ledger) → $($roll.max_ledger)</li>
  <li><b>First TX:</b> $($roll.first_tx_hash)</li>
  <li><b>Last TX:</b> $($roll.last_tx_hash)</li>
</ul>
<!-- XRPL-ROLLUP-END -->
"@

# Inject or replace block
$html = Get-Content $index -Raw
$begin = "<!-- XRPL-ROLLUP-BEGIN -->"
$end   = "<!-- XRPL-ROLLUP-END -->"

if ($html -match [regex]::Escape($begin)) {
    $pattern = "$begin.*?$end"
    $html = [regex]::Replace($html, $pattern, $block, "Singleline")
} else {
    $html += "`n$block`n"
}

Set-Content $index -Encoding utf8 -Value $html
Write-Host "✨ XRPL Rollup metrics injected into index.html"
