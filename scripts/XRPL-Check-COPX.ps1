param(
    [Parameter(Mandatory = $true)]
    [string]$Issuer,

    [Parameter(Mandatory = $true)]
    [string]$User,

    [Parameter(Mandatory = $true)]
    [string]$LP,

    [string]$Currency = "COPX",

    [string]$RpcUrl = "https://s.altnet.rippletest.net:51234"
)

function Invoke-XrplJsonRpc {
    param(
        [string]$Method,
        [hashtable]$Params
    )

    $body = @{
        method = $Method
        params = @($Params)
    } | ConvertTo-Json -Depth 10

    try {
        return Invoke-RestMethod -Uri $RpcUrl -Method Post -Body $body -ContentType "application/json"
    }
    catch {
        Write-Warning "❌ RPC error calling method '$Method': $($_.Exception.Message)"
        return $null
    }
}

Write-Host "🔍 Checking COPX trustlines & balances..." -ForegroundColor Cyan
Write-Host "   Issuer: $Issuer"
Write-Host "   User  : $User"
Write-Host "   LP    : $LP"
Write-Host ""

function Get-TrustLine {
    param(
        [object]$LinesResponse
    )

    if (-not $LinesResponse -or -not $LinesResponse.result -or -not $LinesResponse.result.lines) {
        return $null
    }

    return $LinesResponse.result.lines |
        Where-Object {
            $_.currency -eq $Currency -and (
                $_.account -eq $Issuer -or $_.issuer -eq $Issuer
            )
        } |
        Select-Object -First 1
}

# USER
$userLines = Invoke-XrplJsonRpc -Method "account_lines" -Params @{
    account      = $User
    ledger_index = "validated"
    limit        = 200
}

$userTL = Get-TrustLine -LinesResponse $userLines

if ($null -eq $userTL) {
    Write-Warning "⚠️ No $Currency trustline found for USER wallet."
    $userOk = $false
}
else {
    $userBal = [decimal]$userTL.balance
    Write-Host "👤 USER $Currency line:" -ForegroundColor Yellow
    Write-Host "   Balance : $userBal"
    Write-Host "   Limit   : $($userTL.limit)"
    $userOk = $true
    if ($userBal -le 0) { Write-Warning "⚠️ USER $Currency balance not positive."; $userOk = $false }
}

Write-Host ""

# LP
$lpLines = Invoke-XrplJsonRpc -Method "account_lines" -Params @{
    account      = $LP
    ledger_index = "validated"
    limit        = 200
}

$lpTL = Get-TrustLine -LinesResponse $lpLines

if ($null -eq $lpTL) {
    Write-Warning "⚠️ No $Currency trustline found for LP wallet."
    $lpOk = $false
}
else {
    $lpBal = [decimal]$lpTL.balance
    Write-Host "💧 LP $Currency line:" -ForegroundColor Yellow
    Write-Host "   Balance : $lpBal"
    Write-Host "   Limit   : $($lpTL.limit)"
    $lpOk = $true
    if ($lpBal -le 0) { Write-Warning "⚠️ LP $Currency balance not positive."; $lpOk = $false }
}

Write-Host ""

if ($userOk -and $lpOk) {
    Write-Host "🟢 HEALTH: COPX trustlines & balances OK" -ForegroundColor Green
}
elseif ($userOk -or $lpOk) {
    Write-Host "🟡 HEALTH: Partial success — one wallet OK" -ForegroundColor Yellow
}
else {
    Write-Host "🔴 HEALTH: COPX trustlines/balances NOT OK" -ForegroundColor Red
}
