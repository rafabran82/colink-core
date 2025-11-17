param(
    [string]$Date,
    [string]$MetricsJson
)

$metrics = $MetricsJson | ConvertFrom-Json

$index = ".artifacts/index.html"
if (-not (Test-Path $index)) {
    Write-Error "Dashboard not found: $index"
    exit 1
}

$html = Get-Content $index -Raw

$block = @"
<!-- XRPL-INTEL-BEGIN -->
<div class='intel-block'>
  <h2>XRPL Intelligence — $($metrics.date)</h2>
  <ul>
    <li><b>Total TX:</b> $($metrics.total_tx)</li>
    <li><b>Swaps:</b> $($metrics.swaps)</li>
    <li><b>Offers:</b> $($metrics.offers)</li>
    <li><b>Cancels:</b> $($metrics.cancels)</li>
    <li><b>Issued COL:</b> $($metrics.issued_COL)</li>
    <li><b>Issued CPX:</b> $($metrics.issued_CPX)</li>
    <li><b>Total Fees:</b> $($metrics.fees_total)</li>
    <li><b>Accounts LP:</b> $($metrics.accounts_lp)</li>
    <li><b>Accounts Issuer:</b> $($metrics.accounts_issuer)</li>
    <li><b>Accounts User:</b> $($metrics.accounts_user)</li>
    <li><b>Ledger Range:</b> $($metrics.ledger_first) → $($metrics.ledger_last)</li>
  </ul>
</div>
<!-- XRPL-INTEL-END -->
"@

# Remove old block
$html = $html -replace '<!-- XRPL-INTEL-BEGIN -->.*?<!-- XRPL-INTEL-END -->',''

# Insert new block at bottom
$html = $html + "`n$block`n"

Set-Content -Path $index -Encoding utf8 -Value $html

Write-Host "✨ Dashboard updated with XRPL intelligence block" -ForegroundColor Green
